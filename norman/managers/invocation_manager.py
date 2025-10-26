import asyncio
import time
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
from norman_objects.shared.queries.query_constraints import QueryConstraints
from norman_objects.shared.security.sensitive import Sensitive
from norman_objects.shared.status_flags.status_flag import StatusFlag
from norman_objects.shared.status_flags.status_flag_value import StatusFlagValue

from norman._app_config import NormanAppConfig
from norman.helpers.file_transfer_manager import FileTransferManager
from norman.managers.authentication_manager import AuthenticationManager
from norman.objects.configs.invocation_config import InvocationConfig
from norman.objects.configs.invocation_output_handle import InvocationOutputHandle
from norman.objects.configs.invocation_result import InvocationResult


class InvocationManager:
    def __init__(self):
        self._authentication_manager = AuthenticationManager()
        self._http_client = HttpClient()

        self._file_pull_service = FilePull()
        self._file_push_service = FilePush()
        self._file_transfer = FileTransferManager()
        self._persist_service = Persist()
        self._retrieve_service = Retrieve()

    async def invoke(self, invocation_config: dict[str, Any]) -> InvocationResult:
        invocation_config = InvocationConfig.model_validate(invocation_config)
        await self._authentication_manager.invalidate_access_token()

        await self._http_client.open()
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
                task = self._file_transfer.upload_primitive(token, input, input_data)
                tasks.append(task)
            elif input_source == "File":
                pairing_request = SocketInputPairingRequest(
                    invocation_id=input.invocation_id,
                    input_id=input.id,
                    account_id=input.account_id,
                    model_id=input.model_id,
                    file_size_in_bytes=0 # temporary, will be set in file_transfer
                )

                task = self._file_transfer.upload_file(token, pairing_request, input_data)
                tasks.append(task)
            elif input_source == "Stream":
                pairing_request = SocketInputPairingRequest(
                    invocation_id=input.invocation_id,
                    input_id=input.id,
                    account_id=input.account_id,
                    model_id=input.model_id,
                    file_size_in_bytes=0 # temporary, will be set in file_transfer
                )
                task = self._file_transfer.upload_buffer(token, pairing_request, input_data)
                tasks.append(task)
            else:
                download_request = InputDownloadRequest(
                    signature_id=input.signature_id,
                    invocation_id=input.invocation_id,
                    input_id=input.id,
                    account_id=input.account_id,
                    model_id=input.model_id,
                    links=[input_data],
                )
                task = self._file_pull_service.submit_input_links(token, download_request)
                tasks.append(task)

        await asyncio.gather(*tasks)

    async def _wait_for_flags(self, token: Sensitive[str], invocation: Invocation):
        entity_ids = [invocation.id]
        entity_ids.extend([input.id for input in invocation.inputs])
        entity_ids.extend([output.id for output in invocation.outputs])
        flag_constraints = QueryConstraints.includes("Status_Flags", "Entity_ID", entity_ids)

        while True:
            start_time = time.time()

            results = await self._persist_service.status_flags.get_status_flags(token, flag_constraints)
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

            elapsed = time.time() - start_time
            wait_time = NormanAppConfig.get_flags_interval - elapsed

            if wait_time > 0:
                await asyncio.sleep(wait_time)

    async def _get_results(self, token: Sensitive[str], invocation: Invocation) -> "InvocationResult":
        output_handles = {}

        for output in invocation.outputs:
            task = self._get_output_results(token, invocation, output)
            output_handles[output.display_title] = await task

        return InvocationResult(output_handles)

    async def _get_output_results(self, token: Sensitive[str], invocation: Invocation, output: InvocationSignature):
        account_id = invocation.account_id
        model_id = invocation.model_id
        invocation_id = invocation.id

        headers, stream = await self._retrieve_service.get_invocation_output(
            token, account_id, model_id, invocation_id, output.id
        )

        return InvocationOutputHandle(stream)
