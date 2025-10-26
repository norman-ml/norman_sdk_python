from typing import Dict, Optional

from pydantic import BaseModel, Field

from norman.objects.configs.model_input import ModelInput
from norman.objects.configs.output_config import OutputConfig


class InvocationConfig(BaseModel):
    model_name: str = Field(..., description="Name of the model to invoke")
    inputs: Dict[str, ModelInput] = Field(..., description="Mapping of input keys to ModelInput definitions")
    outputs: Optional[Dict[str, OutputConfig]] = Field(default=None, description="Optional mapping of output keys to OutputConfig definitions If not provided, defaults to model's standard outputs.")
