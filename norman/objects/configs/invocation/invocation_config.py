from typing import List
from pydantic import BaseModel, Field

from norman.objects.configs.invocation.invocation_signature_config import InvocationSignatureConfig


class InvocationConfig(BaseModel):
    model_name: str = Field(..., description="Name of the model to invoke")
    inputs: List[InvocationSignatureConfig] = Field(..., description="List of model input configurations")
