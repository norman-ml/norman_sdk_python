import os
from typing import Any

from norman_core.clients.http_client import HttpClient
from norman_core.services.file_pull.file_pull import FilePull
from norman_core.services.persist import Persist
from norman_objects.services.file_pull.requests.asset_download_request import AssetDownloadRequest
from norman_objects.services.file_push.pairing.socket_asset_pairing_request import SocketAssetPairingRequest
from norman_objects.shared.models.model import Model
from norman_objects.shared.models.model_asset import ModelAsset
from norman_objects.shared.security.sensitive import Sensitive
from norman_utils_external.file_utils import FileUtils

from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.model.asset_config import AssetConfig
from norman.objects.configs.model.model_config import ModelConfig
from norman.objects.factories.model_factory import ModelFactory
from norman.resolvers.flag_status_resolver import FlagStatusResolver
from norman.resolvers.input_source_resolver import InputSourceResolver
from norman.services.file_transfer_service import FileTransferService


class ModelUploadManager:
    """
    High-level orchestrator responsible for uploading complete model packages
    to the Norman platform. This includes:

    - Authenticating the user
    - Creating the model entry in the metadata store
    - Uploading all model assets (files, streams, links)
    - Waiting for backend processing flags to reach completion

    The `ModelUploadManager` is the primary entry point for pushing model
    definitions and associated resources to Norman.

    **Constructor**

    Initializes all required services to perform model uploads:

    - Authentication manager (token lifecycle)
    - File transfer service (streaming file uploads)
    - File utilities (size detection)
    - Flag resolver (asynchronous completion waiting)
    - HTTP client (shared request session)
    - File pull / persist services (backend integration)

    **Attributes**

    - **_authentication_manager** (`AuthenticationManager`)
        Handles API-key–based authentication and token refresh.

    - **_file_transfer_service** (`FileTransferService`)
        Streams file/stream assets into the file-push subsystem.

    - **_file_utils** (`FileUtils`)
        Used for detecting buffer sizes for streamed assets.

    - **_flag_status_resolver** (`FlagStatusResolver`)
        Waits for backend flags to indicate upload completion.

    - **_http_client** (`HttpClient`)
        Reusable HTTP session for authenticated requests.

    - **_file_pull_service**, **_persist_service**
        Services for backend-side link submission and model metadata updates.

    **Methods**
    """

    def __init__(self) -> None:
        self._authentication_manager = AuthenticationManager()
        self._file_transfer_service = FileTransferService()
        self._file_utils = FileUtils()
        self._flag_status_resolver = FlagStatusResolver()
        self._http_client = HttpClient()

        self._file_pull_service = FilePull()
        self._persist_service = Persist()

    async def upload_model(self, model_config: dict[str, Any]) -> Model:
        """
        **Coroutine — Public API**

        Upload a complete model package to the Norman platform. This includes:

        - Validating configuration with `ModelConfig`
        - Creating the model entry via `ModelFactory`
        - Uploading all associated assets (files, streams, or URLs)
        - Waiting for model-level status flags to reach completion

        **Parameters**

        - **model_config** (`dict[str, Any]`)
            A raw dictionary containing the model’s definition and asset
            configuration. It will be validated via `ModelConfig`.

        **Returns**

        - **Model**
            The fully registered model returned from the backend.

        **Raises**

        - **RuntimeError**
            If model creation in the backend fails.
        - **ValueError**
            If asset sources are invalid.
        - **TimeoutError**
            If assets do not finish processing within the configured timeout.
        """
        await self._authentication_manager.invalidate_access_token()
        validated_model_config = ModelConfig.model_validate(model_config)
        model = ModelFactory.create(validated_model_config)

        async with self._http_client:
            model = await self._create_model_in_database(self._authentication_manager.access_token, model)
            await self._upload_assets(self._authentication_manager.access_token, model, validated_model_config)
            await self._wait_for_flags(self._authentication_manager.access_token, model)
            return model

    async def _create_model_in_database(self, token: Sensitive[str], model: Model) -> Model:
        """
        **Coroutine**

        Create the model metadata entry in the Norman backend.

        **Returns**

        - **Model**
            The server-generated model instance, including IDs.

        **Raises**

        - **RuntimeError**
            If the backend fails to create the model.
        """
        models = await self._persist_service.models.create_models(token, [model])
        if not models:
            raise RuntimeError("Model creation failed")
        return models[0]

    async def _upload_assets(self, token: Sensitive[str], model: Model, model_config: ModelConfig) -> None:
        """
        **Coroutine**

        Upload all the model’s assets according to their configuration.
        Routing is determined by the declared source type
        (file, stream, or link).
        """
        asset_configs = {asset_entry.asset_name: asset_entry for asset_entry in model_config.assets}

        for model_asset in model.assets:
            asset_config = asset_configs[model_asset.asset_name]
            await self._handle_asset_upload(token, model_asset, asset_config)

    async def _handle_asset_upload(self, token: Sensitive[str], model_asset: ModelAsset, asset: AssetConfig) -> None:
        """
        **Coroutine**

        Upload a specific asset, determining the correct upload method
        based on the asset's detected or declared source.
        """
        data = asset.data

        if asset.source is not None:
            source = asset.data  # Note: This may be a logic bug; likely should be `asset.source`
        else:
            source = InputSourceResolver.resolve(data)

        if source == "File":
            await self._handle_file_asset(token, model_asset, data)
        elif source == "Stream":
            await self._handle_stream_asset(token, model_asset, data)
        elif source == "Link":
            await self._handle_link_asset(token, model_asset, data)
        else:
            raise ValueError(f"Invalid model asset source: {source}")

    async def _handle_file_asset(self, token: Sensitive[str], model_asset: ModelAsset, path: str) -> None:
        """
        **Coroutine**

        Upload an asset stored on disk.
        """
        file_size = os.path.getsize(path)
        pairing_request = SocketAssetPairingRequest(
            account_id=model_asset.account_id,
            model_id=model_asset.model_id,
            asset_id=model_asset.id,
            file_size_in_bytes=file_size
        )
        await self._file_transfer_service.upload_file(token, pairing_request, path)

    async def _handle_stream_asset(self, token: Sensitive[str], model_asset: ModelAsset, stream: Any) -> None:
        """
        **Coroutine**

        Upload an asset supplied as a file-like stream.
        """
        file_size = self._file_utils.get_buffer_size(stream)
        pairing_request = SocketAssetPairingRequest(
            account_id=model_asset.account_id,
            model_id=model_asset.model_id,
            asset_id=model_asset.id,
            file_size_in_bytes=file_size
        )
        await self._file_transfer_service.upload_from_buffer(token, pairing_request, stream)

    async def _handle_link_asset(self, token: Sensitive[str], model_asset: ModelAsset, data: str) -> None:
        """
        **Coroutine**

        Submit a link-based asset for backend downloading.
        """
        download_request = AssetDownloadRequest(
            account_id=model_asset.account_id,
            model_id=model_asset.model_id,
            asset_id=model_asset.id,
            asset_name=model_asset.asset_name,
            links=[data],
        )
        await self._file_pull_service.submit_asset_links(token, download_request)

    async def _wait_for_flags(self, token: Sensitive[str], model: Model) -> None:
        """
        **Coroutine**

        Wait until the model and all associated assets reach a terminal state.
        """
        entity_ids = [model.id]
        entity_ids.extend([asset.id for asset in model.assets])

        await self._flag_status_resolver.wait_for_entities(token, entity_ids)
