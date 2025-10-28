from pydantic import BaseModel, Field

from norman.objects.configs.model.parameter_config import ParameterConfig


class SignatureConfig(BaseModel):
    display_title: str = Field(..., description="Human-readable name for this input or output")
    data_encoding: str = Field(..., description="Encoding format for the data (e.g., 'UTF-8', 'binary')")
    receive_format: str = Field(..., description="Expected data format at runtime (e.g., 'File', 'Stream', 'Text')")

    parameters: list[ParameterConfig]
