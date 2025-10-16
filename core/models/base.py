from uuid import uuid4

from sqlalchemy import BigInteger, Boolean, Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from core.database import Base
from core.database.mixins import TimestampMixin


class BaseModel(Base, TimestampMixin):
    """Base model class with common fields for all models."""

    __abstract__ = True

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)

    __mapper_args__ = {"eager_defaults": True}