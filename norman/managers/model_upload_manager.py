from typing import Any

import aiofiles
from norman.helpers.flag_status_resolver import FlagHelper
from norman.helpers.input_source_resolver import InputSourceResolver
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

from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.model.asset_config import AssetConfig
from norman.objects.configs.model.model_config import ModelConfig
from norman.objects.factories.model_factory import ModelFactory
from norman.services.file_transfer_service import FileTransferService


class ModelUploadManager:
    def __init__(self) -> None:
        self._authentication_manager = AuthenticationManager()
        self._file_transfer_service = FileTransferService()
        self._http_client = HttpClient()

        self._file_pull_service = FilePull()
        self._file_push_service = FilePush()
        self._file_utils = FileUtils()
        self._flag_helper = FlagHelper()
        self._persist_service = Persist()

    async def upload_model(self, model_config: dict[str, Any]) -> Model:
        await self._authentication_manager.invalidate_access_token()
        validated_model_config = ModelConfig.model_validate(model_config)
        model = ModelFactory.create(validated_model_config)

        async with self._http_client:
            model = await self._create_model_in_database(self._authentication_manager.access_token, model)
            await self._upload_assets(self._authentication_manager.access_token, model, validated_model_config)
            await self._wait_for_flags(self._authentication_manager.access_token, model)
            return model

    async def _create_model_in_database(self, token: Sensitive[str], model: Model) -> Model:
        models = await self._persist_service.models.create_models(token, [model])
        if models is None or len(models) == 0:
            raise RuntimeError("Model creation failed")
        return models[0]

    async def _upload_assets(self, token: Sensitive[str], model: Model, model_config: ModelConfig) -> None:
        asset_configs = {asset_entry.asset_name: asset_entry for asset_entry in model_config.assets}

        for model_asset in model.assets:
            asset_config = asset_configs[model_asset.asset_name]
            await self._handle_asset_upload(token, model_asset, asset_config)

    async def _handle_asset_upload(self, token: Sensitive[str], model_asset: ModelAsset, asset: AssetConfig) -> None:
        data = asset.data

        if data.source is not None:
            source = asset.data
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
        await self._file_transfer_service.upload_file(token, pairing_request, path)

    async def _handle_stream_asset(self, token: Sensitive[str], model_asset: ModelAsset, stream: Any) -> None:
        pairing_request = SocketAssetPairingRequest(
            account_id=model_asset.account_id,
            model_id=model_asset.model_id,
            asset_id=model_asset.id,
            file_size_in_bytes=0  # temporary, updated in file_transfer
        )
        await self._file_transfer_service.upload_from_buffer(token, pairing_request, stream)

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
        entity_ids = [model.id]
        entity_ids.extend([asset.id for asset in model.assets])

        await self._flag_helper.wait_for_entities(token, entity_ids)

