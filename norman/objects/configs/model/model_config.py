from typing import List, Optional

from norman_objects.shared.models.model_hosting_location import ModelHostingLocation
from pydantic import BaseModel, Field

from norman.objects.configs.model.asset_config import AssetConfig
from norman.objects.configs.model.signature_config import SignatureConfig
from norman_objects.shared.models.output_format import OutputFormat
from norman_objects.shared.models.model_type import ModelType
from norman_objects.shared.models.http_request_type import HttpRequestType

class ModelConfig(BaseModel):
    name: str = Field(..., description="Unique name of the model")
    version_label: str = Field(..., description="Human-readable version label (e.g., 'v1.0' or 'beta')")
    short_description: str = Field(..., description="Concise summary describing what the model does")
    long_description: str = Field(..., description="Detailed explanation of the model, usage, and behavior")

    inputs: List[SignatureConfig] = Field(..., description="Input signatures defining model inputs and their formats")
    outputs: List[SignatureConfig] = Field(..., description="Output signatures defining model outputs and their formats")
    assets: List[AssetConfig] = Field(..., description="List of associated model assets required for execution")

    output_format: Optional[OutputFormat] = Field(None, description="Optional format of model outputs (e.g., JSON, Binary)")
    model_type: Optional[ModelType] = Field(None, description="Optional model type or framework (e.g., PyTorch, Transformer_hf)")
    request_type: Optional[HttpRequestType] = Field(None, description="Optional HTTP request type used for inference (e.g., POST, GET)")
    model_class: Optional[str] = Field(None, description="Fully qualified class name or identifier for the model implementation")
    hosting_location: Optional[ModelHostingLocation] = Field(None, description="Hosting location of the model (Internal or External)")
    url: Optional[str] = Field(None, description="URL pointing to the model, required for external models")
