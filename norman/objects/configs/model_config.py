from typing import List

from norman_objects.shared.model_signatures.model_signature import ModelSignature
from norman_objects.shared.model_signatures.signature_type import SignatureType
from norman_objects.shared.models.http_request_type import HttpRequestType
from norman_objects.shared.models.model_asset import ModelAsset
from norman_objects.shared.models.model_hosting_location import ModelHostingLocation
from norman_objects.shared.models.model_type import ModelType
from norman_objects.shared.models.output_format import OutputFormat
from pydantic import BaseModel, Field, field_validator


class ModelConfig(BaseModel):
    name: str = Field(..., description="Model name (unique per account)")
    model_class: str = Field(..., description="Model class identifier (e.g., image-to-image)")
    url: str = Field(..., description="Model endpoint URL (if applicable, may be empty at creation time)")
    short_description: str = Field(..., description="Short summary of the model")
    long_description: str = Field(..., description="Human-readable description")
    version_label: str = Field(..., description="Version label for this model")

    request_type: HttpRequestType = HttpRequestType.Post
    model_type: ModelType = ModelType.Pytorch_jit
    hosting_location: ModelHostingLocation = ModelHostingLocation.Internal
    output_format: OutputFormat = OutputFormat.Json

    inputs: List[ModelSignature] = Field(..., description="Input signatures")
    outputs: List[ModelSignature] = Field(..., description="Output signatures")
    assets: List[ModelAsset] = Field(..., description="Associated model assets")

    # Inject signature_type automatically
    @field_validator("inputs", mode="before")
    @classmethod
    def set_input_signature_type(cls, inputs):
        if isinstance(inputs, list):
            for i in inputs:
                # Only set if missing, to avoid overwriting valid values
                if "signature_type" not in i:
                    i["signature_type"] = SignatureType.Input
        return inputs

    @field_validator("outputs", mode="before")
    @classmethod
    def set_output_signature_type(cls, outputs):
        if isinstance(outputs, list):
            for o in outputs:
                if "signature_type" not in o:
                    o["signature_type"] = SignatureType.Output
        return outputs
