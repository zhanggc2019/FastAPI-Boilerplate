from typing import Sequence
from uuid import UUID

from sqlalchemy import Select, or_, select

from app.models import ChatConversation, ChatMessage
from app.repositories import BaseRepository


class ChatConversationRepository(BaseRepository[ChatConversation]):
    async def list_by_user(self, user_uuid: UUID, keyword: str | None = None) -> Sequence[ChatConversation]:
        query = select(ChatConversation).where(ChatConversation.user_uuid == user_uuid)
        if keyword:
            like = f"%{keyword}%"
            query = (
                query.outerjoin(ChatMessage)
                .where(or_(ChatConversation.title.ilike(like), ChatMessage.content.ilike(like)))
                .distinct()
            )
        query = query.order_by(ChatConversation.updated_at.desc())
        result = await self.session.scalars(query)
        return list(result.all())

    async def get_by_uuid_and_user(self, conversation_uuid: UUID, user_uuid: UUID) -> ChatConversation | None:
        query = select(ChatConversation).where(
            ChatConversation.uuid == conversation_uuid,
            ChatConversation.user_uuid == user_uuid,
        )
        result = await self.session.scalars(query)
        return result.one_or_none()
