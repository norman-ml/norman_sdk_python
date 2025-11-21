from enum import Enum


class OutputDeliveryMode(str, Enum):
    Bytes = "bytes"
    Stream = "stream"
