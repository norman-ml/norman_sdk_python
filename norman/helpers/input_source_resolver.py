import os
import re
from pathlib import Path
from typing import Any
from norman_objects.shared.inputs.input_source import InputSource


class InputSourceResolver:
    @staticmethod
    def resolve(data: Any) -> InputSource:
        # Handle file paths (str or Path)
        if isinstance(data, (str, Path)):
            path = Path(data)
            if path.exists():
                return InputSource.File
            if os.sep in str(path) or path.suffix:
                raise FileNotFoundError(f"InputSourceResolver: file not found at '{path}'")

        # URL / link
        if isinstance(data, str) and re.match(r"^(http|https)://", data):
            return InputSource.Link

        # Stream (bytes-like generator or file-like)
        if hasattr(data, "read") or hasattr(data, "__aiter__"):
            return InputSource.Stream

        # Primitive fallback
        return InputSource.Primitive
