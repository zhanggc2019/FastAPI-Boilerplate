from typing import Literal

from pydantic import BaseModel, Field


class ChatConversationCreate(BaseModel):
    title: str | None = Field(default=None, max_length=255, description="Conversation title")


class ChatMessageSource(BaseModel):
    id: str | None = None
    document_name: str | None = None
    document_id: str | None = None
    dataset_id: str | None = None
    url: str | None = None
    content: str | None = None
    positions: list[str] | list[int] | None = None
    similarity: float | None = None
    vector_similarity: float | None = None
    term_similarity: float | None = None
    doc_type: str | None = None
    image_id: str | None = None


class ChatMessageCreate(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(..., min_length=1, description="Message content")
    sources: list[ChatMessageSource] | None = None
