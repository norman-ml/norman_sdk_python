import os
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from norman_objects.shared.inputs.input_source import InputSource


class InputSourceResolver:
    @staticmethod
    def resolve(data: Any) -> InputSource:
        if isinstance(data, str):
            stripped_string = data.strip()

            if InputSourceResolver.is_url(stripped_string):
                return InputSource.Link

            path = Path(stripped_string)
            if path.exists():
                return InputSource.File
            if os.sep in stripped_string:
                raise FileNotFoundError(f"InputSourceResolver: file not found at '{path}'")

            return InputSource.Primitive

        if isinstance(data, Path):
            if data.exists():
                return InputSource.File
            raise FileNotFoundError(f"InputSourceResolver: file not found at '{data}'")

        if hasattr(data, "read") or hasattr(data, "__aiter__"):
            return InputSource.Stream

        return InputSource.Primitive

    @staticmethod
    def is_url(stripped_string: str):
        parsed = urlparse(stripped_string)
        if parsed.scheme not in ["http", "https"]:
            return False
        if parsed.netloc is None or parsed.netloc == "":
            return False
        return True
