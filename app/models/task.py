from sqlalchemy import Boolean, Column, ForeignKey, String
from sqlalchemy.orm import relationship

from core.models import BaseModel
from core.permissions import BasePermission
from core.security.access_control import (
    Allow,
    Authenticated,
    RolePrincipal,
    UserPrincipal,
)


class Task(BaseModel):
    __tablename__ = "tasks"

    title = Column(String(255), nullable=False)
    description = Column(String(255), nullable=False)
    is_completed = Column(Boolean, default=False, nullable=False)

    task_author_id = Column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    author = relationship("User", back_populates="tasks", uselist=False, lazy="raise")

    def __acl__(self):
        basic_permissions = [BasePermission.CREATE]
        self_permissions = [
            BasePermission.READ,
            BasePermission.EDIT,
            BasePermission.DELETE,
        ]
        all_permissions = list(BasePermission)

        return [
            (Allow, Authenticated, basic_permissions),
            (Allow, UserPrincipal(self.task_author_id), self_permissions),
            (Allow, RolePrincipal("admin"), all_permissions),
        ]
