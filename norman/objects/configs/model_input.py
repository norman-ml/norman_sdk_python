from typing import Any
from pydantic import BaseModel, Field
from norman_objects.shared.inputs.input_source import InputSource


class ModelInput(BaseModel):
    source: InputSource = Field(..., description="Where the input data is coming from")
    data: Any = Field(..., description="Actual input payload (e.g., bytes, string, or link)")
