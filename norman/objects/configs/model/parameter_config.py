from pydantic import BaseModel, Field


class ParameterConfig(BaseModel):
    parameter_name: str = Field(description="Name of the parameter")
    data_encoding: str = Field(description="Encoding format used for this parameter")
