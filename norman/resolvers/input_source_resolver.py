import os
from io import IOBase
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from norman_objects.shared.inputs.input_source import InputSource
import asyncio


class InputSourceResolver:
    @staticmethod
    def resolve(data: Any) -> InputSource:
        if data is None:
            raise ValueError("Input source cannot be None")

        if isinstance(data, str):
            stripped = data.strip()

            if InputSourceResolver._is_url(stripped):
                return InputSource.Link

            path = Path(stripped)
            if path.exists():
                return InputSource.File

            if os.sep in stripped:
                raise FileNotFoundError("Resolved data as a file path, but no file exists at the specified location")

            return InputSource.Primitive

        elif isinstance(data, Path):
            if data.exists():
                return InputSource.File

            raise FileNotFoundError("No file exists at the specified location")

        elif InputSourceResolver._is_async_stream(data):
            return InputSource.Stream

        elif InputSourceResolver._is_sync_stream(data):
            return InputSource.Stream

        else:
            return InputSource.Primitive

    @staticmethod
    def _is_url(stripped_string: str):
        parsed = urlparse(stripped_string)
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

        has_read = callable(getattr(obj, "read", None))
        has_iter = callable(getattr(obj, "__iter__", None)) or callable(getattr(obj, "__next__", None))

        return has_read and has_iter

    @staticmethod
    def _is_async_stream(obj: Any) -> bool:
        aiter_def = getattr(obj, "__aiter__", None)
        if not callable(aiter_def):
            return False

        anext_def = getattr(obj, "__anext__", None)
        if callable(anext_def):
            return True

        read_attr = getattr(obj, "read", None)
        if callable(read_attr):
            if asyncio.iscoroutinefunction(read_attr):
                return True

        return False
