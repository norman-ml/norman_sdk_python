from typing import TypedDict, Any

from norman.objects.configs.input_source import InputSource


class ModelInput(TypedDict):
    source: InputSource
    data: Any