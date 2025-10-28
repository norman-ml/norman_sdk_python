from typing import List
from pydantic import BaseModel, Field

from norman.objects.configs.invocation.invocation_input_config import InvocationInputConfig


class InvocationConfig(BaseModel):
    model_name: str = Field(..., description="Name of the model to invoke")
    inputs: List[InvocationInputConfig] = Field(..., description="List of model input configurations")
