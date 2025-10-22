from fastapi import APIRouter
from .pagination_demo import pagination_router
from .rate_limit import limit_router

test_router = APIRouter()
test_router.include_router(
    limit_router,
    tags=["Test模块"],
)
test_router.include_router(
    pagination_router,
    tags=["Test模块"],
)


__all__ = ["test_router", "pagination_router"]
