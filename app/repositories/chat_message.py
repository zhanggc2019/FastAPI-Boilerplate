from uuid import UUID

from sqlalchemy import select

from app.models import ChatMessage
from app.repositories import BaseRepository


class ChatMessageRepository(BaseRepository[ChatMessage]):
    async def list_by_conversation(self, conversation_uuid: UUID) -> list[ChatMessage]:
        query = select(ChatMessage).where(ChatMessage.conversation_uuid == conversation_uuid)
        query = query.order_by(ChatMessage.created_at.asc())
        result = await self.session.scalars(query)
        return list(result.all())
