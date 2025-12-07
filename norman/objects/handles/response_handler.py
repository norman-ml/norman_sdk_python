from typing import Any, Coroutine


class ResponseHandler:
    """
    A helper class for consuming asynchronous streaming responses.

    This class wraps a coroutine that returns a tuple of `(headers, stream)`,
    where `stream` is an asynchronous iterator yielding byte chunks.
    It provides convenience methods to either retrieve the full response body
    as bytes or access the raw stream.
    """

    def __init__(self, callable_coroutine: Coroutine) -> None:
        self.__callable_coroutine = callable_coroutine

    async def bytes(self) -> bytes:
        """Read and return the full response body as bytes.

        **Returns**

        - bytes: The concatenated byte content from the stream.
        """
        bytes_result = bytearray()
        headers, stream = await self.__callable_coroutine

        async for chunk in stream:
            bytes_result.extend(chunk)

        return bytes_result

    async def stream(self) -> Any:
        """Return the raw asynchronous stream for manual iteration.

        **Returns**

        - Any: The underlying async iterable stream.
        """
        headers, stream = await self.__callable_coroutine
        return stream
