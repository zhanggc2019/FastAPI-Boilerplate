from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import BaseUUIDResponse
from app.schemas.requests.chat import ChatMessageSource


class ChatConversationResponse(BaseUUIDResponse):
    title: str = Field(..., description="Conversation title")
    created_at: datetime
    updated_at: datetime


class ChatMessageResponse(BaseUUIDResponse):
    role: Literal["user", "assistant", "system"]
    content: str
    conversation_uuid: UUID
    created_at: datetime
    sources: list[ChatMessageSource] | None = None
