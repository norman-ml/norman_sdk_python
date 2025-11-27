from pydantic import BaseModel, Field


class AggregateTagConfig(BaseModel):
    name: str = Field(description="Tag name")
