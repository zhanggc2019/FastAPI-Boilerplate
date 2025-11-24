from uuid import UUID
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class CurrentUser(BaseModel):
    model_config = ConfigDict(validate_assignment=True)

    uuid: Optional[UUID] = Field(None, description="User UUID")
