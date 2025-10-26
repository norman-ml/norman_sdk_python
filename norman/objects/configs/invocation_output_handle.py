from typing import Any

from norman_core.clients.http_client import HttpClient

class InvocationOutputHandle:
    def __init__(self, stream) -> None:
        self._http_client = HttpClient()
        self._stream = stream

    async def bytes(self) -> bytes:
        bytes_result = bytearray()
        async for chunk in self._stream:
            bytes_result.extend(chunk)
        await self._http_client.close()
        return bytes_result

    def stream(self) -> Any:
        self._http_client.close()
        return self._stream
