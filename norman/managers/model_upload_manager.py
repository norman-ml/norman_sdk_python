import os
from typing import Any

from norman_core.clients.http_client import HttpClient
from norman_core.services.file_pull.file_pull import FilePull
from norman_core.services.persist import Persist
from norman_objects.services.file_pull.requests.asset_download_request import AssetDownloadRequest
from norman_objects.services.file_push.pairing.socket_asset_pairing_request import SocketAssetPairingRequest
from norman_objects.shared.models.model_asset import ModelAsset
from norman_objects.shared.models.model_projection import ModelProjection
from norman_objects.shared.security.sensitive import Sensitive
from norman_utils_external.file_utils import FileUtils

from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.model.asset_config import AssetConfig
from norman.objects.configs.model.model_projection_config import ModelProjectionConfig
from norman.objects.factories.model_projection_factory import ModelProjectionFactory
from norman.resolvers.flag_status_resolver import FlagStatusResolver
from norman.resolvers.input_source_resolver import InputSourceResolver
from norman.services.file_transfer_service import FileTransferService


class ModelUploadManager:
    def __init__(self) -> None:
        self._authentication_manager = AuthenticationManager()
        self._file_transfer_service = FileTransferService()
        self._file_utils = FileUtils()
        self._flag_status_resolver = FlagStatusResolver()
        self._http_client = HttpClient()

        self._file_pull_service = FilePull()
        self._persist_service = Persist()

    async def upload_model(self, model_config: dict[str, Any]) -> ModelProjection:
        await self._authentication_manager.invalidate_access_token()
        validated_model_config = ModelProjectionConfig.model_validate(model_config)
        model = ModelProjectionFactory.create(validated_model_config)

        async with self._http_client:
            model = await self._create_model_in_database(self._authentication_manager.access_token, model)
            await self._upload_assets(self._authentication_manager.access_token, model, validated_model_config)
            await self._wait_for_flags(self._authentication_manager.access_token, model)
            return model

    async def _create_model_in_database(self, token: Sensitive[str], model: ModelProjection) -> ModelProjection:
        models = await self._persist_service.models.create_model_projections(token, [model])
        if models is None or len(models) == 0:
            raise RuntimeError("Model creation failed")
        return models[0]

    async def _upload_assets(self, token: Sensitive[str], model: ModelProjection, model_config: ModelProjectionConfig) -> None:
        asset_configs = {asset_entry.asset_name: asset_entry for asset_entry in model_config.version.assets}

        # Ensure version_id is set and not "0"
        version_id = model.version.id
        if not version_id or version_id == "0":
            raise ValueError(f"Model version ID is not set properly. Got: {version_id}")

        for model_asset in model.version.assets:
            asset_config = asset_configs[model_asset.asset_name]
            # Pass model.version.id since model_asset.version_id may be "0"
            await self._handle_asset_upload(token, model_asset, asset_config, version_id)

    async def _handle_asset_upload(self, token: Sensitive[str], model_asset: ModelAsset, asset: AssetConfig, version_id: str) -> None:
        data = asset.data

        if asset.source is not None:
            source = asset.data
        else:
            source = InputSourceResolver.resolve(data)

        if source == "File":
            await self._handle_file_asset(token, model_asset, data, version_id)
        elif source == "Stream":
            await self._handle_stream_asset(token, model_asset, data, version_id)
        elif source == "Link":
            await self._handle_link_asset(token, model_asset, data, version_id)
        else:
            raise ValueError(f"Invalid model asset source: {source}")

    async def _handle_file_asset(self, token: Sensitive[str], model_asset: ModelAsset, path: str, version_id: str) -> None:
        file_size = os.path.getsize(path)
        
        pairing_request = SocketAssetPairingRequest(
            account_id=model_asset.account_id,
            model_id=model_asset.model_id,
            asset_id=model_asset.id,
            file_size_in_bytes=file_size
        )
        
        # Pass version_id separately since SocketAssetPairingRequest model doesn't include it
        await self._file_transfer_service.upload_file_with_version_id(token, pairing_request, path, version_id)

    async def _handle_stream_asset(self, token: Sensitive[str], model_asset: ModelAsset, stream: Any, version_id: str) -> None:
        file_size = self._file_utils.get_buffer_size(stream)
        pairing_request = SocketAssetPairingRequest(
            account_id=model_asset.account_id,
            model_id=model_asset.model_id,
            asset_id=model_asset.id,
            file_size_in_bytes=file_size
        )
        # Pass version_id separately since SocketAssetPairingRequest model doesn't include it
        await self._file_transfer_service.upload_from_buffer_with_version_id(token, pairing_request, stream, version_id)

    async def _handle_link_asset(self, token: Sensitive[str], model_asset: ModelAsset, data: str, version_id: str) -> None:
        download_request = AssetDownloadRequest(
            account_id=model_asset.account_id,
            model_id=model_asset.model_id,
            version_id=version_id,  # Use passed version_id instead of model_asset.version_id
            asset_id=model_asset.id,
            asset_name=model_asset.asset_name,
            links=[data],
        )
        await self._file_pull_service.submit_asset_links(token, download_request)

    async def _wait_for_flags(self, token: Sensitive[str], model: ModelProjection) -> None:
        entity_ids = [model.version.id]
        entity_ids.extend([asset.id for asset in model.version.assets])

        await self._flag_status_resolver.wait_for_entities(token, entity_ids)
