from enum import Enum


class ConsumeMode(str, Enum):
    Bytes = "bytes"
    Stream = "stream"
