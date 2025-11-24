from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class ApiKey(BaseModel):
    __tablename__ = "api_keys"

    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="api_keys")
