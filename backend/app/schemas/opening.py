from pydantic import BaseModel, Field


class OpeningMarginRequest(BaseModel):
    margin: float = Field(ge=0)
