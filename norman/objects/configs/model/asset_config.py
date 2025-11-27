from typing import Any, Optional

from norman_objects.shared.inputs.input_source import InputSource
from pydantic import BaseModel, Field


class AssetConfig(BaseModel):
    asset_name: str = Field(description="Identifier for the asset (e.g., 'weights', 'tokenizer')")
    data: Any = Field(description="Asset content or reference (e.g., file path, URL, or in-memory data)")
    source: Optional[InputSource] = Field(None, description="Where the input data is coming from")
