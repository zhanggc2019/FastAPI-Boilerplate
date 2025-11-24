from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base
from app.db.mixins import TimestampMixin

class ApiKey(Base, TimestampMixin):
    """
    API Key 模型

    使用加密的 key 作为主键
    """
    __tablename__ = "api_keys"

    # 使用加密后的 key 作为主键
    key = Column(String, primary_key=True, nullable=False)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")
