from uuid import UUID

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Base response schema with common configuration."""

    model_config = {
        "from_attributes": True,
    }


class BaseUUIDResponse(BaseResponse):
    """Base response schema for models with UUID fields."""

    uuid: UUID = Field(..., description="Resource UUID")
