from fastapi import APIRouter, Depends

from app.api.deps.authentication import AuthenticationRequired

from .chats import chat_router

chats_router = APIRouter()
chats_router.include_router(
    chat_router,
    tags=["Chats"],
    dependencies=[Depends(AuthenticationRequired)],
)

__all__ = ["chats_router"]
