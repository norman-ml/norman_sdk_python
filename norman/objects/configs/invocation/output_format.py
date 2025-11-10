from enum import Enum


class OutputFormat(str, Enum):
    Bytes = "bytes"
    Stream = "stream"
