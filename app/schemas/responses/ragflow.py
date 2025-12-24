from typing import Any

from pydantic import BaseModel, Field


class RagflowAskResponse(BaseModel):
    answer: str = Field(..., description="Answer text")
    session_id: str | None = Field(default=None, description="Conversation session id")
    raw: dict[str, Any] = Field(default_factory=dict, description="Raw response payload from RAGFlow")
