from pydantic import BaseModel, ConfigDict, Field


class CurrentUser(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    id: int = Field(None, description="User ID")
