import os
from typing import Any

from norman_core.clients.http_client import HttpClient
from norman_core.services.file_pull.file_pull import FilePull
from norman_core.services.file_push.file_push import FilePush
from norman_core.services.persist import Persist
from norman_core.services.retrieve.retrieve import Retrieve
from norman_objects.services.file_pull.requests.input_download_request import InputDownloadRequest
from norman_objects.services.file_push.pairing.socket_input_pairing_request import SocketInputPairingRequest
from norman_objects.shared.invocation_signatures.invocation_signature import InvocationSignature
from norman_objects.shared.invocations.invocation import Invocation
from norman_objects.shared.security.sensitive import Sensitive
from norman_utils_external.file_utils import FileUtils

from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.invocation.invocation_config import InvocationConfig
from norman.objects.configs.invocation.invocation_input_config import InvocationInputConfig
from norman.objects.factories.invocation_config_factory import InvocationConfigFactory
from norman.objects.handles.response_handler import ResponseHandler
from norman.resolvers.flag_status_resolver import FlagStatusResolver
from norman.resolvers.input_source_resolver import InputSourceResolver
from norman.services.file_transfer_service import FileTransferService


class InvocationManager:
    """
    High-level orchestrator responsible for executing model invocations within
    the Norman SDK. The manager coordinates authentication, invocation creation,
    input upload, asynchronous status polling, output retrieval, and response
    resolution.

    This class acts as the public entry point for performing a model invocation:
    users provide an `invocation_config`, and the manager handles the entire
    pipeline needed to produce final outputs.

    Invocation lifecycle:

    1. Authenticate (refresh token if needed)
    2. Create invocation record in the database
    3. Upload model inputs (primitive, stream, file, or URL)
    4. Wait for status flags to indicate completion
    5. Retrieve output handlers
    6. Consume resolved outputs in the desired format

    **Constructor**

    Initializes all supporting services required for invoking a model:
    - Authentication manager
    - File transfer service
    - File utilities
    - Flag polling resolver
    - File pull, persist, and retrieve services
    - Reusable HTTP session

    **Attributes**

    - **_authentication_manager** (`AuthenticationManager`)
        Handles authentication and access token lifecycle.

    - **_file_transfer_service** (`FileTransferService`)
        Responsible for uploading primitive, file, and stream inputs.

    - **_file_utils** (`FileUtils`)
        Utility for buffer-size and file-type calculations.

    - **_flag_status_resolver** (`FlagStatusResolver`)
        Polls backend status flags until invocation is complete.

    - **_http_client** (`HttpClient`)
        Reusable HTTP client for authenticated API calls.

    - **_file_pull_service**, **_persist_service**, **_retrieve_service**
        Norman Core services for pulling files, persisting metadata,
        and retrieving outputs.

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
        self._retrieve_service = Retrieve()

    async def invoke(self, invocation_config: dict[str, Any]) -> dict[str, Any]:
        """
        **Coroutine — Public API**

        Execute a full model invocation based on the provided configuration.
        This method orchestrates authentication, input upload, status polling,
        output retrieval, and final response resolution.

        **Parameters**

        - **invocation_config** (`dict[str, Any]`)
            Raw invocation parameters, validated and normalized into an
            `InvocationConfig` via `InvocationConfigFactory`.

        **Returns**

        - **dict[str, Any]**
            A mapping from output display titles to fully resolved output values.
            Output formats depend on the configured consume mode.

        **Raises**

        - **RuntimeError**
            If invocation record creation fails.
        - **ValueError**
            If input upload or response handling fails.
        - **TimeoutError**
            If invocation does not complete within the configured flag timeout.
        """
        await self._authentication_manager.invalidate_access_token()
        validated_invocation_config = InvocationConfigFactory.create(invocation_config)

        async with self._http_client:
            invocation = await self._create_invocation_in_database(self._authentication_manager.access_token, validated_invocation_config)
            await self._upload_inputs(self._authentication_manager.access_token, invocation, validated_invocation_config)
            await self._wait_for_flags(self._authentication_manager.access_token, invocation)
            output_handlers = await self._get_response_handlers(self._authentication_manager.access_token, invocation)
            results = await self._resolve_outputs(validated_invocation_config, output_handlers)

        return results

    async def _create_invocation_in_database(self, token: Sensitive[str], invocation_config: InvocationConfig) -> Invocation:
        """
        **Coroutine**

        Create an invocation entry in the database based on the model name.

        **Returns**

        - **Invocation**
            The invocation record returned by the backend.

        **Raises**

        - **RuntimeError**
            If no invocation is created.
        """
        invocations = await self._persist_service.invocations.create_invocations_by_model_names(
            token=token,
            model_name_counter={invocation_config.model_name: 1}
        )
        if not invocations:
            raise RuntimeError("Invocation creation failed")
        return invocations[0]

    async def _upload_inputs(self, token: Sensitive[str], invocation: Invocation, invocation_config: InvocationConfig) -> None:
        """
        **Coroutine**

        Upload all invocation inputs, dispatching to the correct handler
        based on input source type.
        """
        input_configs = {input_config.display_title: input_config for input_config in invocation_config.inputs}

        for invocation_input in invocation.inputs:
            input_config = input_configs[invocation_input.display_title]
            await self._handle_input_upload(token, invocation_input, input_config)

    async def _handle_input_upload(self, token: Sensitive[str], invocation_input: InvocationSignature, input_config: InvocationInputConfig) -> None:
        """
        **Coroutine**

        Determine the appropriate upload strategy for the input and execute it.
        """
        data = input_config.data
        source = input_config.source or InputSourceResolver.resolve(data)

        if source == "Primitive":
            await self._upload_primitive_input(token, invocation_input, data)
        elif source == "File":
            await self._upload_file_input(token, invocation_input, data)
        elif source == "Stream":
            await self._upload_stream_input(token, invocation_input, data)
        elif source == "Link":
            await self._submit_link_input(token, invocation_input, data)
        else:
            raise ValueError(f"Unsupported input source: {source}")

    async def _upload_primitive_input(self, token: Sensitive[str], invocation_input: InvocationSignature, data: Any) -> None:
        """
        **Coroutine**

        Upload primitive data (strings, numbers, dicts, lists) by converting
        it into a `BytesIO` buffer.
        """
        byte_buffer = self._file_transfer_service.normalize_primitive_data(data)
        buffer_size = self._file_utils.get_buffer_size(byte_buffer)
        pairing_request = SocketInputPairingRequest(
            invocation_id=invocation_input.invocation_id,
            input_id=invocation_input.id,
            account_id=invocation_input.account_id,
            model_id=invocation_input.model_id,
            file_size_in_bytes=buffer_size
        )
        await self._file_transfer_service.upload_from_buffer(token, pairing_request, byte_buffer)

    async def _upload_file_input(self, token: Sensitive[str], invocation_input: InvocationSignature, path: str) -> None:
        """
        **Coroutine**

        Upload a file from disk by allocating a socket and streaming contents.
        """
        file_size = os.path.getsize(path)
        pairing_request = SocketInputPairingRequest(
            invocation_id=invocation_input.invocation_id,
            input_id=invocation_input.id,
            account_id=invocation_input.account_id,
            model_id=invocation_input.model_id,
            file_size_in_bytes=file_size
        )
        await self._file_transfer_service.upload_file(token, pairing_request, path)

    async def _upload_stream_input(self, token: Sensitive[str], invocation_input: InvocationSignature, stream: Any) -> None:
        """
        **Coroutine**

        Upload an in-memory byte stream.
        """
        file_size = self._file_utils.get_buffer_size(stream)
        pairing_request = SocketInputPairingRequest(
            invocation_id=invocation_input.invocation_id,
            input_id=invocation_input.id,
            account_id=invocation_input.account_id,
            model_id=invocation_input.model_id,
            file_size_in_bytes=file_size
        )
        await self._file_transfer_service.upload_from_buffer(token, pairing_request, stream)

    async def _submit_link_input(self, token: Sensitive[str], invocation_input: InvocationSignature, link: str) -> None:
        """
        **Coroutine**

        Submit a URL for backend-side downloading.
        """
        download_request = InputDownloadRequest(
            signature_id=invocation_input.signature_id,
            invocation_id=invocation_input.invocation_id,
            input_id=invocation_input.id,
            account_id=invocation_input.account_id,
            model_id=invocation_input.model_id,
            links=[link],
        )
        await self._file_pull_service.submit_input_links(token, download_request)

    async def _wait_for_flags(self, token: Sensitive[str], invocation: Invocation) -> None:
        """
        **Coroutine**

        Block until the invocation and all associated inputs/outputs reach
        the `Finished` state or error out.
        """
        entity_ids = [invocation.id]
        entity_ids.extend([input.id for input in invocation.inputs])
        entity_ids.extend([output.id for output in invocation.outputs])

        await self._flag_status_resolver.wait_for_entities(token, entity_ids)

    async def _get_response_handlers(self, token: Sensitive[str], invocation: Invocation) -> dict[str, Any]:
        """
        **Coroutine**

        Create `ResponseHandler` objects for each invocation output.
        """
        response_handlers = {}
        for output in invocation.outputs:
            invocation_output = self._retrieve_service.get_invocation_output(
                token,
                invocation.account_id,
                invocation.model_id,
                invocation.id,
                output.id
            )
            response_handlers[output.display_title] = ResponseHandler(invocation_output)

        return response_handlers

    async def _resolve_outputs(self, invocation_config: InvocationConfig, response_handlers: dict[str, ResponseHandler]) -> dict[str, Any]:
        """
        **Coroutine**

        Consume output handlers and produce final resolved output values,
        applying user-defined `consume_mode` where applicable.
        """
        output_configs = {}
        if invocation_config.outputs is not None:
            for output_config in invocation_config.outputs:
                output_configs[output_config.display_title] = output_config

        invocation_results = {}
        for display_title, response_handler in response_handlers.items():
            if display_title in output_configs:
                output_config = output_configs[display_title]
                consume_mode = output_config.consume_mode

                if consume_mode is None:
                    method = response_handler.bytes
                else:
                    if not hasattr(response_handler, consume_mode.value):
                        raise ValueError(f"Unsupported response handler method: {consume_mode}")

                    method = getattr(response_handler, consume_mode.value)
            else:
                method = response_handler.bytes

            invocation_results[display_title] = await method()

        return invocation_results
