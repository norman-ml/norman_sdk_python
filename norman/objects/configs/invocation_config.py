from typing import Dict

from pydantic import BaseModel, Field

from norman.objects.configs.invocation_input_config import InvocationInputConfig


class InvocationConfig(BaseModel):
    model_name: str = Field(..., description="Name of the model to invoke")
    inputs: Dict[str, InvocationInputConfig] = Field(..., description="Mapping of input keys to ModelInput definitions")
