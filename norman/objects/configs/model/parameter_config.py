from pydantic import BaseModel, Field


class ParameterConfig(BaseModel):
    parameter_name: str = Field(description="Name of the matching argument defined in the model forward function signature")
    data_encoding: str = Field(description="Encoding format expected by the model forward function for this parameter data")
