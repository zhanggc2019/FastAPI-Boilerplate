from fastapi import APIRouter, Depends

from app.api.deps.authentication import AuthenticationRequired

from .tasks import task_router

tasks_router = APIRouter()
tasks_router.include_router(
    task_router,
    tags=["Tasks"],
    dependencies=[Depends(AuthenticationRequired)],
)

__all__ = ["tasks_router"]
