import asyncio
from typing import Any

import aiofiles
from norman_core.clients.http_client import HttpClient
from norman_core.clients.socket_client import SocketClient
from norman_core.services.file_pull.file_pull import FilePull
from norman_core.services.file_push.file_push import FilePush
from norman_core.services.persist import Persist
from norman_objects.services.file_pull.requests.asset_download_request import AssetDownloadRequest
from norman_objects.services.file_push.checksum.checksum_request import ChecksumRequest
from norman_objects.services.file_push.pairing.socket_asset_pairing_request import SocketAssetPairingRequest
from norman_objects.shared.models.model import Model
from norman_objects.shared.models.model_asset import ModelAsset
from norman_objects.shared.queries.query_constraints import QueryConstraints
from norman_objects.shared.security.sensitive import Sensitive
from norman_objects.shared.status_flags.status_flag import StatusFlag
from norman_objects.shared.status_flags.status_flag_value import StatusFlagValue

from norman.helpers.get_buffer_size import get_buffer_size
from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.model_config import ModelConfig


class ModelUploadManager:
    def __init__(self):
        self._authentication_manager = AuthenticationManager()
        self._http_client = HttpClient()

        self._file_pull_service = FilePull()
        self._file_push_service = FilePush()
        self._persist_service = Persist()

    async def upload_model(self, model_config_dict: dict[str, Any]) -> Model:
        await self._authentication_manager.validate_access_token()
        model_config = ModelConfig.model_validate(model_config_dict)
        
        async with self._http_client:
            model = Model(account_id=self._authentication_manager.account_id, **model_config.model_dump())

            model = await self._create_model_in_persist(self._authentication_manager.access_token, model)
            await self._upload_assets(self._authentication_manager.access_token, model, model_config_dict["assets"])
            await self._wait_for_flags(self._authentication_manager.access_token, model)
            return model

    async def _create_model_in_persist(self, token: Sensitive[str], model: Model) -> Model:
        response = await self._persist_service.models.create_models(token, [model])

        if len(response) == 0:
            raise ValueError("Failed to create model")
        return next(iter(response.values()))

    async def _upload_assets(self, token: Sensitive[str], model: Model, assets: list[dict[str, Any]]):
        tasks = []
        for model_asset in model.assets:
            asset = next(asset for asset in assets if asset["asset_name"] == model_asset.asset_name)
            asset_source = asset["source"]
            asset_data = asset["data"]

            if asset_source == "Link":
                tasks.append(self._upload_link(token, model, model_asset, asset_data))
            elif asset_source == "Path":
                tasks.append(self._upload_file(token, model, model_asset, asset_data))
            elif asset_source == "Stream":
                tasks.append(self._upload_buffer(token, model, model_asset, asset_data))
            else:
                raise ValueError("Model asset source must be one of link, path, or stream.")

        await asyncio.gather(*tasks)

    async def _upload_link(self, token: Sensitive[str], model: Model, model_asset: ModelAsset, link: str):
        download_request = AssetDownloadRequest(
            account_id=model.account_id,
            model_id=model.id,
            asset_id=model_asset.id,
            asset_name=model_asset.asset_name,
            links=[link]
        )
        await self._file_pull_service.submit_asset_links(token, download_request)

    async def _upload_file(self, token: Sensitive[str], model: Model, model_asset: ModelAsset, path: str):
        async with aiofiles.open(path, mode="rb") as file:
            await self._upload_buffer(token, model, model_asset, file)

    async def _upload_buffer(self, token: Sensitive[str], model: Model, model_asset: ModelAsset, file_buffer: Any):
        pairing_request = SocketAssetPairingRequest(
            account_id=model.account_id,
            model_id=model.id,
            asset_id=model_asset.id,
            file_size_in_bytes=get_buffer_size(file_buffer),
        )
        socket_info = await self._file_push_service.allocate_socket_for_asset(token, pairing_request)
        checksum = await SocketClient.write_and_digest(socket_info, file_buffer)

        checksum_request = ChecksumRequest(
            pairing_id=socket_info.pairing_id,
            checksum=checksum
        )
        await self._file_push_service.complete_file_transfer(token, checksum_request)

    async def _wait_for_flags(self, token: Sensitive[str], model: Model):
        while True:
            model_flag_constraints = QueryConstraints.equals("Status_Flags", "Entity_ID", model.id)
            asset_flag_constraints = QueryConstraints.includes("Status_Flags", "Entity_ID", [asset.id for asset in model.assets])

            model_flag_task = self._persist_service.status_flags.get_status_flags(token, model_flag_constraints)
            asset_flag_task = self._persist_service.status_flags.get_status_flags(token, asset_flag_constraints)

            results = await asyncio.gather(model_flag_task, asset_flag_task)

            all_model_flags: list[StatusFlag] = [flag for flag_result in results for flag_list in flag_result.values() for flag in flag_list]

            failed_flags = [flag for flag in all_model_flags if flag.flag_value == StatusFlagValue.Error]
            if len(failed_flags) > 0:
                raise Exception("Failed to upload model", failed_flags)

            all_finished = all(flag.flag_value == StatusFlagValue.Finished for flag in all_model_flags)
            if all_finished:
                break
            await asyncio.sleep(5)
