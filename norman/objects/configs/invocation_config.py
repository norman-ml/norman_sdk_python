from typing import Dict
from pydantic import BaseModel, Field
from norman.objects.configs.model_input import ModelInput

class InvocationConfig(BaseModel):
    model_name: str = Field(..., description="Name of the model to invoke")
    inputs: Dict[str, ModelInput] = Field(..., description="Mapping of input keys to ModelInput definitions")
