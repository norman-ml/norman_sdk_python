import asyncio
import io
from typing import Any, Union

import aiofiles
from norman_core.clients.http_client import HttpClient
from norman_core.clients.socket_client import SocketClient
from norman_core.services.file_pull.file_pull import FilePull
from norman_core.services.file_push.file_push import FilePush
from norman_core.services.persist import Persist
from norman_core.services.retrieve.retrieve import Retrieve
from norman_objects.services.file_pull.requests.input_download_request import InputDownloadRequest
from norman_objects.services.file_push.checksum.checksum_request import ChecksumRequest
from norman_objects.services.file_push.pairing.socket_input_pairing_request import SocketInputPairingRequest
from norman_objects.shared.invocation_signatures.invocation_signature import InvocationSignature
from norman_objects.shared.invocations.invocation import Invocation
from norman_objects.shared.queries.query_constraints import QueryConstraints
from norman_objects.shared.security.sensitive import Sensitive
from norman_objects.shared.status_flags.status_flag import StatusFlag
from norman_objects.shared.status_flags.status_flag_value import StatusFlagValue
from norman_utils_external.get_buffer_size import get_buffer_size
from norman_utils_external.streaming_utils import AsyncBufferedReader, BufferedReader

from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.invocation_config import InvocationConfig


class InvocationManager:
    def __init__(self):
        self._authentication_manager = AuthenticationManager()
        self._http_client = HttpClient()

        self._file_pull_service = FilePull()
        self._file_push_service = FilePush()
        self._persist_service = Persist()
        self._retrieve_service = Retrieve()

    async def invoke(self, invocation_config: dict[str, Any]) -> dict[str, bytearray]:
        invocation_config = InvocationConfig.model_validate(invocation_config)
        await self._authentication_manager.invalidate_access_token()

        async with self._http_client:
            invocation = await self._create_invocation_in_database(self._authentication_manager.access_token, invocation_config)
            await self._upload_inputs(self._authentication_manager.access_token, invocation, invocation_config)
            await self._wait_for_flags(self._authentication_manager.access_token, invocation)
            return await self._get_results(self._authentication_manager.access_token, invocation)

    async def _create_invocation_in_database(self, token: Sensitive[str], invocation_config: InvocationConfig):
        invocations = await self._persist_service.invocations.create_invocations_by_model_names(token=token, model_name_counter={invocation_config.model_name: 1})
        return invocations[0]

    async def _upload_inputs(self, token: Sensitive[str], invocation: Invocation, invocation_config: InvocationConfig):
        tasks = []

        for input in invocation.inputs:
            input_config = invocation_config.inputs[input.display_title]
            input_source = input_config.source
            input_data = input_config.data

            if input_source == "Primitive":
                task = self._upload_primitive(token, input, input_data)
                tasks.append(task)
            elif input_source == "File":
                task = self._upload_file(token, input, input_data)
                tasks.append(task)
            elif input_source == "Stream":
                task = self._upload_buffer(token, input, input_data)
                tasks.append(task)
            else:
                task = self._upload_link(token, input, input_data)
                tasks.append(task)

        await asyncio.gather(*tasks)

    async def _wait_for_flags(self, token: Sensitive[str], invocation: Invocation):
        while True:
            invocation_constraints = QueryConstraints.equals("Status_Flags", "Entity_ID", invocation.id)
            results = await self._persist_service.status_flags.get_status_flags(token, invocation_constraints)
            if len(results) == 0:
                raise ValueError(f"Invocation {invocation.id} has no flags")

            all_flags: list[StatusFlag] = []
            for key in results:
                all_flags.extend(results[key])

            any_failed = any(flag.flag_value == StatusFlagValue.Error for flag in all_flags)
            all_finished = all(flag.flag_value == StatusFlagValue.Finished for flag in all_flags)

            if any_failed:
                raise ValueError(f"Invocation {invocation.id} has failed")
            if all_finished:
                break

            await asyncio.sleep(1)

    async def _get_results(self, token: Sensitive[str], invocation: Invocation) -> dict[str, bytearray]:
        output_tasks = []
        for output in invocation.outputs:
            task = self._get_output_results(token, invocation, output.id)
            output_tasks.append(task)

        results: list[bytearray] = await asyncio.gather(*output_tasks)
        return {
            output.display_title: result
            for output, result in zip(invocation.outputs, results)
        }

    async def _get_output_results(self, token: Sensitive[str], invocation: Invocation, output_id: str) -> bytearray:
        account_id = invocation.account_id
        model_id = invocation.model_id
        invocation_id = invocation.id

        headers, stream = await self._retrieve_service.get_invocation_output(token, account_id, model_id, invocation_id, output_id)

        results = bytearray()
        async for chunk in stream:
            results.extend(chunk)

        return results

    async def _upload_primitive(self, token: Sensitive[str], input: InvocationSignature, data: Any):
        buffer = io.BytesIO()
        buffer.write(str(data).encode("utf-8"))
        buffer.seek(0)

        await self._upload_buffer(token, input, buffer)

    async def _upload_file(self, token: Sensitive[str], input: InvocationSignature, file_path: str):
        async with aiofiles.open(file_path, mode="rb") as file:
            await self._upload_buffer(token, input, file)

    async def _upload_buffer(self, token: Sensitive[str], input: InvocationSignature, buffer: Union[AsyncBufferedReader, BufferedReader]):
        pairing_request = SocketInputPairingRequest(
            invocation_id=input.invocation_id,
            input_id=input.id,
            account_id=input.account_id,
            model_id=input.model_id,
            file_size_in_bytes=get_buffer_size(buffer)
        )
        request = await self._file_push_service.allocate_socket_for_input(
            token, pairing_request
        )

        file_checksum = await SocketClient.write_and_digest(request, buffer)

        checksum_request = ChecksumRequest(
            pairing_id=request.pairing_id, checksum=file_checksum
        )
        await self._file_push_service.complete_file_transfer(token, checksum_request)

    async def _upload_link(self, token: Sensitive[str], input: InvocationSignature, link: str):
        download_request = InputDownloadRequest(
            signature_id=input.signature_id,
            invocation_id=input.invocation_id,
            input_id=input.id,
            account_id=input.account_id,
            model_id=input.model_id,
            links=[link]
        )
        response = await self._file_pull_service.submit_input_links(token, download_request)
        return response
