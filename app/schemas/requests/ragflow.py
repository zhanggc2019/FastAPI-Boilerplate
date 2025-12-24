from typing import Any

from pydantic import BaseModel, Field


class RagflowChatMessage(BaseModel):
    role: str = Field(..., description="Message role, e.g. user/assistant/system")
    content: str = Field(..., min_length=1, description="Message content")


class RagflowAskRequest(BaseModel):
    question: str | None = Field(default=None, description="User question (shortcut for single message)")
    messages: list[RagflowChatMessage] | None = Field(default=None, description="Chat messages")
    chat_id: str | None = Field(default=None, description="Override chat id")
    stream: bool = Field(default=False, description="Whether to stream response")
    extra_body: dict[str, Any] | None = Field(default=None, description="Extra request body")
