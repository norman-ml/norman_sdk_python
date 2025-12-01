from pydantic import BaseModel, Field


class ModelTagConfig(BaseModel):
    name: str = Field(description="Tag name")
