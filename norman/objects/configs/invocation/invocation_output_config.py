from typing import Any, Optional
from norman_objects.shared.inputs.input_source import InputSource
from pydantic import BaseModel, Field

from norman.objects.configs.invocation.consume_mode import ConsumeMode


class InvocationOutputConfig(BaseModel):
    display_title: str = Field(description="Human-friendly name for the output")
    data: Any = Field(description="Actual output payload (bytes, string, or file path)")
    consume_mode: Optional[ConsumeMode] = Field(None, description="Where the data is coming from")
