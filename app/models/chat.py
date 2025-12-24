from sqlalchemy import Column, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.models import BaseModel


class ChatConversation(BaseModel):
    __tablename__ = "chat_conversations"

    title = Column(String(255), nullable=False)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid", ondelete="CASCADE"), nullable=False)

    user = relationship("User", back_populates="chat_conversations", uselist=False, lazy="raise")
    messages = relationship(
        "ChatMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="raise",
    )


class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"

    role = Column(String(32), nullable=False)
    content = Column(Text, nullable=False)
    sources = Column(JSONB, nullable=True)
    conversation_uuid = Column(UUID(as_uuid=True), ForeignKey("chat_conversations.uuid", ondelete="CASCADE"), nullable=False)

    conversation = relationship("ChatConversation", back_populates="messages", uselist=False, lazy="raise")
