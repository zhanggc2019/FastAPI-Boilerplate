from pydantic import Field

from app.schemas.base import BaseUUIDResponse


class UserResponse(BaseUUIDResponse):
    email: str = Field(..., json_schema_extra={"example": "john.doe@example.com"})
    username: str = Field(..., json_schema_extra={"example": "john.doe"})
