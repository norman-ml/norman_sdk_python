from typing import Optional, Literal, Any

from pydantic import BaseModel


class OutputConfig(BaseModel):
    format: Literal["Memory", "Stream"] = "Memory"
    data: Optional[Any] = None
