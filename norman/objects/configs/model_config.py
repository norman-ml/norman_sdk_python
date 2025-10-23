import random
import string
from typing import List

from norman_objects.shared.model_signatures.model_signature import ModelSignature
from norman_objects.shared.model_signatures.signature_type import SignatureType
from norman_objects.shared.models.http_request_type import HttpRequestType
from norman_objects.shared.models.model_asset import ModelAsset
from norman_objects.shared.models.model_hosting_location import ModelHostingLocation
from norman_objects.shared.models.model_type import ModelType
from norman_objects.shared.models.output_format import OutputFormat
from pydantic import BaseModel, Field, field_validator, model_validator

from norman.managers.authentication_manager import AuthenticationManager


class ModelConfig(BaseModel):
    name: str = Field(..., description="Model name")
    model_class: str = Field("", description="Model class identifier")
    url: str = Field("", description="Model endpoint URL")
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

    # Inject account_id from AuthenticationManager into all assets
    @model_validator(mode="before")
    def inject_account_id(cls, values):
        if "assets" in values and isinstance(values["assets"], list):
            auth_manager = AuthenticationManager()
            account_id = getattr(auth_manager, "account_id", None)
            if account_id:
                for asset in values["assets"]:
                    if "account_id" not in asset or not asset["account_id"]:
                        asset["account_id"] = account_id
        return values

    @model_validator(mode="before")
    def generate_version_label(cls, values):
        if 'version_label' not in values or not values['version_label']:
            # Generate a random 6-character string with letters (a-z, A-Z) and numbers (1-9)
            version_label = ''.join(random.choices(string.ascii_letters + '123456789', k=6))
            values['version_label'] = version_label
        return values

    # Inject signature_type automatically
    @field_validator("inputs", mode="before")
    @classmethod
    def set_input_signature_type(cls, inputs):
        if isinstance(inputs, list):
            for input in inputs:
                # Only set if missing, to avoid overwriting valid values
                if "signature_type" not in input:
                    input["signature_type"] = SignatureType.Input
        return inputs

    @field_validator("outputs", mode="before")
    @classmethod
    def set_output_signature_type(cls, outputs):
        if isinstance(outputs, list):
            for output in outputs:
                if "signature_type" not in output:
                    output["signature_type"] = SignatureType.Output
        return outputs
