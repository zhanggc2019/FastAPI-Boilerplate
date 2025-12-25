from uuid import UUID

from app.core.exceptions import BadRequestException, ResourceNotFoundException
from app.db import Propagation, Transactional
from app.models import ChatConversation, ChatMessage
from app.repositories import ChatConversationRepository, ChatMessageRepository
from app.services.base import BaseService


class ChatService(BaseService[ChatConversation]):
    def __init__(
        self,
        conversation_repository: ChatConversationRepository,
        message_repository: ChatMessageRepository,
    ):
        super().__init__(model=ChatConversation, repository=conversation_repository)
        self.conversation_repository = conversation_repository
        self.message_repository = message_repository

    async def list_conversations(self, user_uuid: UUID, keyword: str | None = None) -> list[ChatConversation]:
        return list(await self.conversation_repository.list_by_user(user_uuid, keyword))

    @Transactional(propagation=Propagation.REQUIRED)
    async def create_conversation(self, user_uuid: UUID, title: str | None = None) -> ChatConversation:
        if not user_uuid:
            raise BadRequestException("Invalid user")
        conversation_title = (title or "").strip() or "新会话"
        return await self.conversation_repository.create(
            {
                "user_uuid": user_uuid,
                "title": conversation_title,
            }
        )

    async def get_conversation(self, conversation_uuid: UUID, user_uuid: UUID) -> ChatConversation:
        conversation = await self.conversation_repository.get_by_uuid_and_user(conversation_uuid, user_uuid)
        if not conversation:
            raise ResourceNotFoundException("Conversation not found")
        return conversation

    @Transactional(propagation=Propagation.REQUIRED)
    async def update_conversation_title(
        self,
        conversation_uuid: UUID,
        user_uuid: UUID,
        title: str,
    ) -> ChatConversation:
        conversation = await self.get_conversation(conversation_uuid, user_uuid)
        conversation.title = title.strip()
        return conversation

    async def list_messages(self, conversation_uuid: UUID, user_uuid: UUID) -> list[ChatMessage]:
        await self.get_conversation(conversation_uuid, user_uuid)
        return await self.message_repository.list_by_conversation(conversation_uuid)

    @Transactional(propagation=Propagation.REQUIRED)
    async def add_message(
        self,
        conversation_uuid: UUID,
        user_uuid: UUID,
        role: str,
        content: str,
        sources: list[dict] | None = None,
    ) -> ChatMessage:
        if not content:
            raise BadRequestException("Message content is required")
        if role not in {"user", "assistant", "system"}:
            raise BadRequestException("Invalid message role")
        await self.get_conversation(conversation_uuid, user_uuid)
        return await self.message_repository.create(
            {
                "conversation_uuid": conversation_uuid,
                "role": role,
                "content": content,
                "sources": sources,
            }
        )

    @Transactional(propagation=Propagation.REQUIRED)
    async def delete_conversation(self, conversation_uuid: UUID, user_uuid: UUID) -> None:
        conversation = await self.get_conversation(conversation_uuid, user_uuid)
        await self.conversation_repository.delete(conversation)
