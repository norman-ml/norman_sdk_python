from typing import Dict, Optional

from pydantic import BaseModel, Field

from norman.objects.configs.invocation_input_config import InvocationInputConfig
from norman.objects.configs.invocation_output_config import InvocationOutputConfig


class InvocationConfig(BaseModel):
    model_name: str = Field(..., description="Name of the model to invoke")
    inputs: Dict[str, InvocationInputConfig] = Field(..., description="Mapping of input keys to ModelInput definitions")
    outputs: Optional[Dict[str, InvocationOutputConfig]] = Field(default=None, description="Optional mapping of output keys to OutputConfig definitions If not provided, defaults to model's standard outputs.")
