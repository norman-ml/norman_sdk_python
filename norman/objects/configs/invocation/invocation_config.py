from typing import List, Optional

from pydantic import BaseModel, Field

from norman.objects.configs.invocation.invocation_signature_config import InvocationSignatureConfig
from norman.objects.configs.invocation.output_delivery_mode import OutputDeliveryMode


class InvocationConfig(BaseModel):
    model_name: str = Field(..., description="Name of the model to invoke")
    inputs: List[InvocationSignatureConfig] = Field(..., description="List of model input configurations")
    outputs_format: Optional[dict[str, OutputDeliveryMode]] = Field(None, description="Mapping of output names to their formats")
