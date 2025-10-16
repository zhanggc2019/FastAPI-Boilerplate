from pydantic import UUID4, BaseModel, Field


class UserResponse(BaseModel):
    email: str = Field(..., json_schema_extra={"example": "john.doe@example.com"})
    username: str = Field(..., json_schema_extra={"example": "john.doe"})
    uuid: UUID4 = Field(..., json_schema_extra={"example": "a3b8f042-1e16-4f0a-a8f0-421e16df0a2f"})

    model_config = {
        "from_attributes": True,
    }
