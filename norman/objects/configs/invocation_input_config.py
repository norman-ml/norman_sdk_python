from typing import Any, Optional
from norman_objects.shared.inputs.input_source import InputSource
from pydantic import BaseModel, Field


class InvocationInputConfig(BaseModel):
    display_title: str = Field(..., description="Human-friendly name for the input")
    data: Any = Field(..., description="Actual input payload (bytes, string, or file path)")
    source: Optional[InputSource] = Field(None, description="Where the input data is coming from")
