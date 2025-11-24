from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ApiKeyBase(BaseModel):
    name: str
    expires_at: Optional[datetime] = None

class ApiKeyCreate(ApiKeyBase):
    pass

class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    is_active: Optional[bool] = None

class ApiKeyResponse(ApiKeyBase):
    id: int
    key: str
    is_active: bool
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True
