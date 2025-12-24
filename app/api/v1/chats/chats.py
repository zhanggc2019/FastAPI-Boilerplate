from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, Request, status

from app.core.factory import Factory
from app.schemas.requests.chat import ChatConversationCreate, ChatMessageCreate
from app.schemas.responses.chat import ChatConversationResponse, ChatMessageResponse
from app.services import ChatService

chat_router = APIRouter()


@chat_router.get("/", response_model=List[ChatConversationResponse])
async def list_conversations(
    request: Request,
    keyword: str | None = None,
    chat_service: ChatService = Depends(Factory().get_chat_service),
) -> List[ChatConversationResponse]:
    conversations = await chat_service.list_conversations(request.user.uuid, keyword)
    return [ChatConversationResponse.model_validate(item) for item in conversations]


@chat_router.post("/", response_model=ChatConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: Request,
    payload: ChatConversationCreate,
    chat_service: ChatService = Depends(Factory().get_chat_service),
) -> ChatConversationResponse:
    conversation = await chat_service.create_conversation(request.user.uuid, payload.title)
    return ChatConversationResponse.model_validate(conversation)


@chat_router.delete("/{conversation_uuid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    request: Request,
    conversation_uuid: str,
    chat_service: ChatService = Depends(Factory().get_chat_service),
) -> None:
    await chat_service.delete_conversation(UUID(conversation_uuid), request.user.uuid)


@chat_router.get("/{conversation_uuid}/messages", response_model=List[ChatMessageResponse])
async def list_messages(
    request: Request,
    conversation_uuid: str,
    chat_service: ChatService = Depends(Factory().get_chat_service),
) -> List[ChatMessageResponse]:
    messages = await chat_service.list_messages(UUID(conversation_uuid), request.user.uuid)
    return [ChatMessageResponse.model_validate(item) for item in messages]


@chat_router.post("/{conversation_uuid}/messages", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
async def create_message(
    request: Request,
    conversation_uuid: str,
    payload: ChatMessageCreate,
    chat_service: ChatService = Depends(Factory().get_chat_service),
) -> ChatMessageResponse:
    message = await chat_service.add_message(
        conversation_uuid=UUID(conversation_uuid),
        user_uuid=request.user.uuid,
        role=payload.role,
        content=payload.content,
        sources=[item.model_dump() for item in payload.sources] if payload.sources else None,
    )
    return ChatMessageResponse.model_validate(message)
