from fastapi import Depends, Request

from app.controllers.user import UserController
from core.factory import Factory


def get_user_controller():
    """获取用户控制器实例"""
    return Factory().get_user_controller()


async def get_current_user(
    request: Request,
    user_controller: UserController = Depends(get_user_controller),
):
    """
    获取当前用户

    Args:
        request: FastAPI请求对象
        user_controller: 用户控制器实例

    Returns:
        当前用户对象
    """
    return await user_controller.get_by_id(request.user.id)
