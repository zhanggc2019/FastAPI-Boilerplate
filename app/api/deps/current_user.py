from fastapi import Depends, Request

from app.core.factory import Factory
from app.services.user import UserService


from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_session

def get_user_service(db_session: AsyncSession = Depends(get_session)) -> UserService:
    """获取用户服务实例，供依赖注入使用。"""
    return Factory().get_user_service(db_session=db_session)


async def get_current_user(
    request: Request,
    user_service: UserService = Depends(get_user_service),
):
    """
    获取当前登录用户。

    Args:
        request: FastAPI 请求对象，包含用户上下文。
        user_service: 业务服务，用于按 ID 查询用户。

    Returns:
        当前用户实体。
    """
    return await user_service.get_by_id(request.user.id)

