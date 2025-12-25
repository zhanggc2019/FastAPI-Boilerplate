from typing import Any

from pydantic import BaseModel, Field


class RagflowAskResponse(BaseModel):
    answer: str = Field(..., description="Answer text")
    session_id: str | None = Field(default=None, description="Conversation session id")
    reference: dict[str, Any] | None = Field(default=None, description="Reference payload")
    raw: dict[str, Any] = Field(default_factory=dict, description="Raw response payload from RAGFlow")
