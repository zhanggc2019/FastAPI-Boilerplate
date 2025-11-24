from uuid import UUID
from pydantic import BaseModel, field_serializer
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
    key: str  # 加密后的 key (用于删除等操作)
    plaintext_key: Optional[str] = None  # 明文 key (仅在创建时返回)
    is_active: bool
    created_at: datetime
    user_uuid: UUID

    class Config:
        from_attributes = True
        # 允许从模型的私有属性读取
        populate_by_name = True

    @field_serializer('plaintext_key')
    def serialize_plaintext_key(self, value):
        """序列化明文 key"""
        return value

    @classmethod
    def from_orm_with_plaintext(cls, obj):
        """从 ORM 对象创建,包含明文 key"""
        data = {
            "key": obj.key,
            "plaintext_key": getattr(obj, '_plaintext_key', None),
            "name": obj.name,
            "is_active": obj.is_active,
            "created_at": obj.created_at,
            "user_uuid": obj.user_uuid,
            "expires_at": obj.expires_at
        }
        return cls(**data)
