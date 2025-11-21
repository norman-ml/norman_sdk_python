import asyncio
from typing import Any

from norman_core.clients.http_client import HttpClient
from norman_core.services.file_pull.file_pull import FilePull
from norman_core.services.file_push.file_push import FilePush
from norman_core.services.persist import Persist
from norman_core.services.retrieve.retrieve import Retrieve
from norman_objects.services.file_pull.requests.input_download_request import InputDownloadRequest
from norman_objects.services.file_push.pairing.socket_input_pairing_request import SocketInputPairingRequest
from norman_objects.shared.invocations.invocation import Invocation
from norman_objects.shared.security.sensitive import Sensitive

from norman.helpers.file_transfer_manager import FileTransferManager
from norman.helpers.flag_helper import FlagHelper
from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.invocation.invocation_config import InvocationConfig
from norman.objects.factories.invocation_config_factory import InvocationConfigFactory
from norman.objects.handles.response_handler import ResponseHandler


class InvocationManager:
    def __init__(self) -> None:
        self._authentication_manager = AuthenticationManager()
        self._http_client = HttpClient()

        self._file_pull_service = FilePull()
        self._file_push_service = FilePush()
        self._file_transfer = FileTransferManager()
        self._flag_helper = FlagHelper()
        self._persist_service = Persist()
        self._retrieve_service = Retrieve()

    async def invoke(self, invocation_config: dict[str, Any]) -> dict[str, Any]:
        await self._authentication_manager.invalidate_access_token()
        validated_invocation_config = InvocationConfigFactory.create(invocation_config)

        async with self._http_client:
            invocation = await self._create_invocation_in_database(self._authentication_manager.access_token, validated_invocation_config)
            await self._upload_inputs(self._authentication_manager.access_token, invocation, validated_invocation_config)
            await self._wait_for_flags(self._authentication_manager.access_token, invocation)
            output_handlers = await self._get_results(self._authentication_manager.access_token, invocation)
            results = await self._resolve_outputs(validated_invocation_config, output_handlers)

        return results

    async def _create_invocation_in_database(self, token: Sensitive[str], invocation_config: InvocationConfig) -> Invocation:
        invocations = await self._persist_service.invocations.create_invocations_by_model_names(token=token, model_name_counter={invocation_config.model_name: 1})
        if invocations is None or len(invocations) == 0:
            raise RuntimeError("Invocation creation failed")
        return invocations[0]

    async def _upload_inputs(self, token: Sensitive[str], invocation: Invocation, invocation_config: InvocationConfig) -> None:
        config_map = {input_config.display_title: input_config for input_config in invocation_config.inputs}

        for invocation_input in invocation.inputs:
            input_config = config_map.get(invocation_input.display_title)
            await self._handle_input(token, invocation_input, input_config)

    async def _handle_input(self, token: Sensitive[str], input, input_config) -> None:
        source = input_config.source
        data = input_config.data

        if source == "Primitive":
            await self._upload_primitive_input(token, input, data)
        elif source == "File":
            await self._upload_file_input(token, input, data)
        elif source == "Stream":
            await self._upload_stream_input(token, input, data)
        elif source == "Link":
            await self._submit_link_input(token, input, data)
        else:
            raise ValueError(f"Unsupported input source: {source}")

    async def _upload_primitive_input(self, token: Sensitive[str], input, data) -> None:
        pairing_request = SocketInputPairingRequest(
            invocation_id=input.invocation_id,
            input_id=input.id,
            account_id=input.account_id,
            model_id=input.model_id,
            file_size_in_bytes=0
        )

        await self._file_transfer.upload_primitive(token, pairing_request, data)

    async def _upload_file_input(self, token: Sensitive[str], input, path: str) -> None:
        pairing_request = SocketInputPairingRequest(
            invocation_id=input.invocation_id,
            input_id=input.id,
            account_id=input.account_id,
            model_id=input.model_id,
            file_size_in_bytes=0
        )
        await self._file_transfer.upload_file(token, pairing_request, path)

    async def _upload_stream_input(self, token: Sensitive[str], input, stream: Any) -> None:
        pairing_request = SocketInputPairingRequest(
            invocation_id=input.invocation_id,
            input_id=input.id,
            account_id=input.account_id,
            model_id=input.model_id,
            file_size_in_bytes=0
        )
        await self._file_transfer.upload_from_buffer(token, pairing_request, stream)

    async def _submit_link_input(self, token: Sensitive[str], input, link: str) -> None:
        download_request = InputDownloadRequest(
            signature_id=input.signature_id,
            invocation_id=input.invocation_id,
            input_id=input.id,
            account_id=input.account_id,
            model_id=input.model_id,
            links=[link],
        )
        await self._file_pull_service.submit_input_links(token, download_request)

    async def _wait_for_flags(self, token: Sensitive[str], invocation: Invocation) -> None:
        entity_ids = [invocation.id]
        entity_ids.extend([input.id for input in invocation.inputs])
        entity_ids.extend([output.id for output in invocation.outputs])

        await self._flag_helper.wait_for_entities(token, entity_ids)

    async def _get_results(self, token: Sensitive[str], invocation: Invocation) -> dict[str, Any]:
        output_handles = {}

        for output in invocation.outputs:
            invocation_output = self._retrieve_service.get_invocation_output(token, invocation.account_id, invocation.model_id, invocation.id, output.id)
            output_handles[output.display_title] = ResponseHandler(invocation_output)

        return output_handles

    async def _resolve_outputs(self, validated_invocation_config: Any, output_handlers: dict[str, Any],) -> dict[str, Any]:
        for output_name, output_handler in output_handlers.items():
            if (validated_invocation_config.outputs_format is not None):
                output_format = validated_invocation_config.outputs_format[output_name]
                output_handler_method = output_format.value
                method = getattr(output_handler, output_handler_method, None)
                output_result = await method()

            else:
                output_result = await output_handler.bytes()

            output_handlers[output_name] = output_result

        return output_handlers
