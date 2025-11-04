from uuid import uuid4

from sqlalchemy import BigInteger, Column
from sqlalchemy.dialects.postgresql import UUID

from app.db import Base
from app.db.mixins import TimestampMixin


class BaseModel(Base, TimestampMixin):
    """Base model class with common fields for all models."""

    __abstract__ = True

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)

    __mapper_args__ = {"eager_defaults": True}
