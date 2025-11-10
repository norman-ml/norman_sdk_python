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
from norman_objects.shared.security.sensitive import Sensitive
from norman_utils_external.file_utils import FileUtils

from norman.helpers.file_transfer_manager import FileTransferManager
from norman.helpers.flag_helper import FlagHelper
from norman.helpers.input_source_resolver import InputSourceResolver
from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.model.model_config import ModelConfig
from norman.objects.factories.model_factory import ModelFactory
from norman.objects.configs.model.asset_config import AssetConfig


class ModelUploadManager:
    def __init__(self) -> None:
        self._authentication_manager = AuthenticationManager()
        self._http_client = HttpClient()
        self._file_transfer = FileTransferManager()

        self._file_pull_service = FilePull()
        self._file_push_service = FilePush()
        self._file_utils = FileUtils()
        self._flag_helper = FlagHelper()
        self._persist_service = Persist()

    async def upload_model(self, model_config: dict[str, Any]) -> Model:
        await self._authentication_manager.invalidate_access_token()
        model = ModelFactory.create(model_config)

        async with self._http_client:
            model = await self._create_model_in_persist(self._authentication_manager.access_token, model)
            await self._upload_assets(self._authentication_manager.access_token, model, model_config["assets"])
            await self._wait_for_flags(self._authentication_manager.access_token, model)
            return model

    async def _create_model_in_persist(self, token: Sensitive[str], model: Model) -> Model:
        response = await self._persist_service.models.create_models(token, [model])

        if len(response) == 0:
            raise ValueError("Failed to create model")
        return next(iter(response.values()))

    async def _upload_assets(self, token: Sensitive[str], model: Model, assets: list[dict]) -> None:
        tasks = [
            self._handle_asset(token, model_asset, assets)
            for model_asset in model.assets
        ]
        await asyncio.gather(*tasks)

    async def _handle_asset(self, token: Sensitive[str], model_asset: ModelAsset, assets: list[dict]) -> None:
        asset = next(asset for asset in assets if asset["asset_name"] == model_asset.asset_name)
        data = asset["data"]

        if "source" in data:
            source = asset["data"]
        else:
            source = InputSourceResolver.resolve(data)

        if source == "Link":
            await self._handle_link_asset(token, model_asset, data)
        elif source == "File":
            await self._handle_file_asset(token, model_asset, data)
        elif source == "Stream":
            await self._handle_stream_asset(token, model_asset, data)
        else:
            raise ValueError(f"Invalid model asset source: {source}")

    async def _handle_link_asset(self, token: Sensitive[str], model_asset: ModelAsset, data: str) -> None:
        download_request = AssetDownloadRequest(
            account_id=model_asset.account_id,
            model_id=model_asset.model_id,
            asset_id=model_asset.id,
            asset_name=model_asset.asset_name,
            links=[data],
        )
        await self._file_pull_service.submit_asset_links(token, download_request)

    async def _handle_file_asset(self, token: Sensitive[str], model_asset: ModelAsset, path: str) -> None:
        pairing_request = SocketAssetPairingRequest(
            account_id=model_asset.account_id,
            model_id=model_asset.model_id,
            asset_id=model_asset.id,
            file_size_in_bytes=0  # temporary, updated in file_transfer
        )
        await self._file_transfer.upload_file(token, pairing_request, path)

    async def _handle_stream_asset(self, token: Sensitive[str], model_asset: ModelAsset, stream: Any) -> None:
        pairing_request = SocketAssetPairingRequest(
            account_id=model_asset.account_id,
            model_id=model_asset.model_id,
            asset_id=model_asset.id,
            file_size_in_bytes=0  # temporary, updated in file_transfer
        )
        await self._file_transfer.upload_from_buffer(token, pairing_request, stream)

    async def _upload_link(self, token: Sensitive[str], model: Model, model_asset: ModelAsset, link: str) -> list[str]:
        download_request = AssetDownloadRequest(
            account_id=model.account_id,
            model_id=model.id,
            asset_id=model_asset.id,
            asset_name=model_asset.asset_name,
            links=[link]
        )
        await self._file_pull_service.submit_asset_links(token, download_request)

    async def _upload_file(self, token: Sensitive[str], model: Model, model_asset: ModelAsset, path: str) -> None:
        async with aiofiles.open(path, mode="rb") as file:
            await self._upload_buffer(token, model, model_asset, file)

    async def _upload_buffer(self, token: Sensitive[str], model: Model, model_asset: ModelAsset, file_buffer: Any) -> None:
        pairing_request = SocketAssetPairingRequest(
            account_id=model.account_id,
            model_id=model.id,
            asset_id=model_asset.id,
            file_size_in_bytes=self._file_utils.get_buffer_size(file_buffer),
        )
        socket_info = await self._file_push_service.allocate_socket_for_asset(token, pairing_request)
        checksum = await SocketClient.write_and_digest(socket_info, file_buffer)

        checksum_request = ChecksumRequest(
            pairing_id=socket_info.pairing_id,
            checksum=checksum
        )
        await self._file_push_service.complete_file_transfer(token, checksum_request)

    async def _wait_for_flags(self, token: Sensitive[str], model: Model) -> None:
        entity_ids = [model.id] + [asset.id for asset in model.assets]
        await self._flag_helper.wait_for_entities(token, entity_ids)
