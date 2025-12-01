from typing import Any, Coroutine


class ResponseHandler:
    def __init__(self, callable_coroutine: Coroutine) -> None:
        self.__callable_coroutine = callable_coroutine

    async def bytes(self) -> bytes:
        bytes_result = bytearray()
        headers, stream = await self.__callable_coroutine

        async for chunk in stream:
            bytes_result.extend(chunk)

        return bytes_result

    async def stream(self) -> Any:
        headers, stream = await self.__callable_coroutine
        return stream
