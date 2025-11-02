from typing import Any

from norman_core.clients.http_client import HttpClient
from norman_core.services.retrieve.retrieve import Retrieve


class InvocationOutputHandle:
    def __init__(self, token, account_id, model_id, invocation_id, output_id) -> None:
        self._retrieve_service = Retrieve()
        self._token = token
        self._account_id = account_id
        self._model_id = model_id
        self._invocation_id = invocation_id
        self._output_id = output_id

        self._http_client = HttpClient()

    async def bytes(self) -> bytes:
        bytes_result = bytearray()
        async with self._http_client:
            stream = await self._get_output_results_stream()
            async for chunk in stream:
                bytes_result.extend(chunk)
        return bytes_result

    async def stream(self) -> Any:
        async with self._http_client:
            stream = await self._get_output_results_stream()
        return stream

    async def _get_output_results_stream(self):
        headers, stream = await self._retrieve_service.get_invocation_output(
            self._token,
            self._account_id,
            self._model_id,
            self._invocation_id,
            self._output_id
        )

        return stream
