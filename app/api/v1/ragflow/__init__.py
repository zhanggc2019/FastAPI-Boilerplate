from fastapi import APIRouter, Depends

from app.api.deps.authentication import AuthenticationRequired

from .ragflow import ragflow_router

ragflow_api_router = APIRouter()
ragflow_api_router.include_router(
    ragflow_router,
    tags=["RAGFlow"],
    dependencies=[Depends(AuthenticationRequired)],
)

__all__ = ["ragflow_api_router"]
