from typing import TypedDict

from norman.objects.configs.model_input import ModelInput


class InvocationConfig(TypedDict):
    model_name: str
    inputs: dict[str, ModelInput]
