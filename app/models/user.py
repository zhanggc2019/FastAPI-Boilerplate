from sqlalchemy import Boolean, Column, Unicode
from sqlalchemy.orm import relationship

from app.models import BaseModel
from app.core.permissions import BasePermission
from app.core.security.access_control import Allow, Everyone, RolePrincipal, UserPrincipal


class User(BaseModel):
    __tablename__ = "users"

    email = Column(Unicode(255), nullable=False, unique=True)
    password = Column(Unicode(255), nullable=False)
    username = Column(Unicode(255), nullable=False, unique=True)
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)

    tasks = relationship("Task", back_populates="author", lazy="raise", passive_deletes=True)
    api_keys = relationship("ApiKey", back_populates="user", lazy="raise", passive_deletes=True)
    chat_conversations = relationship("ChatConversation", back_populates="user", lazy="raise", passive_deletes=True)

    def __acl__(self):
        basic_permissions = [BasePermission.READ, BasePermission.CREATE]
        self_permissions = [
            BasePermission.READ,
            BasePermission.EDIT,
            BasePermission.CREATE,
        ]
        all_permissions = list(BasePermission)

        return [
            (Allow, Everyone, basic_permissions),
            (Allow, UserPrincipal(value=self.uuid), self_permissions),
            (Allow, RolePrincipal(value="admin"), all_permissions),
        ]
