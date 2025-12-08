import asyncio
from io import IOBase
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from norman_objects.shared.inputs.input_source import InputSource


class InputSourceResolver:
    """
    Utility class for determining the type of input source provided to the
    Norman SDK. The resolver inspects the incoming data and classifies it as:

    - `InputSource.File` - A local file path (string or `Path`) that exists.
    - `InputSource.Stream` - A synchronous or asynchronous stream object.
    - `InputSource.Link` - A valid HTTP or HTTPS URL.
    - `InputSource.Primitive` - Any other literal or primitive value.

    This classification enables the SDK to handle file uploads, URLs, streams,
    and primitive values in a unified manner.

    **Methods**
    """
    @staticmethod
    def resolve(data: Any) -> InputSource:
        """
        Determine the appropriate `InputSource` type for the given value.

        Classification follows these rules:

        1. **Path**
           If `data` is a `Path` object that exists on disk → `InputSource.File`.

        2. **Async Stream**
           If `data` exposes `__aiter__`, `__anext__`, and an async `read()` → `InputSource.Stream`.

        3. **Sync Stream**
           If `data` is a file-like object or exposes `read`, `__iter__`, and `__next__` → `InputSource.Stream`.

        4. **String**
           - If it is a valid HTTP/HTTPS URL → `InputSource.Link`.
           - If it is a file path that exists → `InputSource.File`.
           - Otherwise → `InputSource.Primitive`.

        5. **Anything else**
           Falls back to `InputSource.Primitive`.

        **Parameters**

        - **data** (`Any`)
            The input object to classify. May be a string, file path, stream,
            or primitive value.

        **Returns**

        - **InputSource** - The detected input source classification.

        **Raises**

        - **ValueError** - If `data` is `None`.
        - **FileNotFoundError** - If a `Path` object points to a non-existent file.
        """
        if data is None:
            raise ValueError("Input data cannot be None")
        elif isinstance(data, Path):
            if data.exists():
                return InputSource.File

            raise FileNotFoundError("No file exists at the specified location")
        elif InputSourceResolver._is_async_stream(data):
            return InputSource.Stream
        elif InputSourceResolver._is_sync_stream(data):
            return InputSource.Stream
        elif isinstance(data, str):
            stripped = data.strip()

            if InputSourceResolver._is_url(stripped):
                return InputSource.Link

            path = Path(stripped)
            if path.exists():
                return InputSource.File

            return InputSource.Primitive
        else:
            return InputSource.Primitive

    @staticmethod
    def _is_url(data: str):
        parsed = urlparse(data)
        if parsed.scheme not in ["http", "https"]:
            return False
        elif parsed.netloc is None or parsed.netloc == "":
            return False
        else:
            return True

    @staticmethod
    def _is_sync_stream(obj: Any) -> bool:
        if isinstance(obj, IOBase):
            return True

        read_attribute = getattr(obj, "read", None)
        if not callable(read_attribute):
            return False

        iter_attribute = getattr(obj, "__iter__", None)
        if not callable(iter_attribute):
            return False

        next_attribute = getattr(obj, "__next__", None)
        if not callable(next_attribute):
            return False

        return True

    @staticmethod
    def _is_async_stream(obj: Any) -> bool:
        aiter_attribute = getattr(obj, "__aiter__", None)
        if not callable(aiter_attribute):
            return False

        anext_attribute = getattr(obj, "__anext__", None)
        if not callable(anext_attribute):
            return False

        read_attribute = getattr(obj, "read", None)
        if not callable(read_attribute) or not asyncio.iscoroutinefunction(read_attribute):
            return False

        return True
