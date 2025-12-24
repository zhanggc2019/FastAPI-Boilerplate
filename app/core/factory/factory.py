from functools import partial

from fastapi import Depends

from app.db import get_session
from app.models import ChatConversation, ChatMessage, Task, User
from app.repositories import (
    ChatConversationRepository,
    ChatMessageRepository,
    TaskRepository,
    UserRepository,
)
from app.services import AuthService, ChatService, RagflowService, TaskService, UserService


class Factory:
    """Service and repository factory for dependency injection."""

    # Repositories
    task_repository = partial(TaskRepository, Task)
    user_repository = partial(UserRepository, User)
    chat_conversation_repository = partial(ChatConversationRepository, ChatConversation)
    chat_message_repository = partial(ChatMessageRepository, ChatMessage)

    def get_user_service(self, db_session=Depends(get_session)):
        return UserService(user_repository=self.user_repository(db_session=db_session))

    def get_task_service(self, db_session=Depends(get_session)):
        return TaskService(task_repository=self.task_repository(db_session=db_session))

    def get_auth_service(self, db_session=Depends(get_session)):
        return AuthService(
            user_repository=self.user_repository(db_session=db_session),
        )

    def get_ragflow_service(self):
        return RagflowService()

    def get_chat_service(self, db_session=Depends(get_session)):
        return ChatService(
            conversation_repository=self.chat_conversation_repository(db_session=db_session),
            message_repository=self.chat_message_repository(db_session=db_session),
        )
