from typing import Optional

from norman_objects.shared.model_signatures.http_location import HttpLocation
from pydantic import BaseModel, Field

from norman.objects.configs.model.parameter_config import ParameterConfig


class SignatureConfig(BaseModel):
    display_title: str = Field(..., description="Human-readable name for this input or output")
    data_encoding: str = Field(..., description="Encoding format for the data (e.g., 'UTF-8', 'binary')")
    receive_format: str = Field(..., description="Expected data format at runtime (e.g., 'File', 'Link', 'Primitive')")

    parameters: list[ParameterConfig]

    http_location: Optional[HttpLocation] = Field(None, description="Optional HTTP location of the value (e.g., Body, Path, Query) when transmitted via HTTP.")
    hidden: Optional[bool] = Field(None, description="If True, this field is hidden from public display.")
    default_value: Optional[str] = Field(None, description="Default value to use when no explicit value is provided.")
