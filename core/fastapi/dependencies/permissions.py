from http import HTTPStatus

from fastapi import Depends, Request

from app.controllers.user import UserController
from core.exceptions import CustomException
from core.factory import Factory
from core.security.access_control import (
    AccessControl,
    Authenticated,
    Everyone,
    RolePrincipal,
    UserPrincipal,
)


class InsufficientPermissionsException(CustomException):
    code = HTTPStatus.FORBIDDEN
    error_code = HTTPStatus.FORBIDDEN
    message = "Insufficient permissions"


async def get_user_principals(
    request: Request,
    user_controller: UserController = None,
) -> list:
    """
    获取用户权限主体列表

    Args:
        request: FastAPI请求对象
        user_controller: 用户控制器，如果为None则通过工厂方法获取

    Returns:
        list: 权限主体列表
    """
    if user_controller is None:
        user_controller = Factory().get_user_controller()

    user_id = request.user.id
    principals = [Everyone]

    if not user_id:
        return principals

    user = await user_controller.get_by_id(id_=user_id)

    principals.append(Authenticated)
    principals.append(UserPrincipal(user.id))

    if user.is_admin:
        principals.append(RolePrincipal("admin"))

    return principals


def get_user_controller():
    """获取用户控制器实例"""
    return Factory().get_user_controller()


# 创建带依赖注入的权限获取函数
async def get_user_principals_with_deps(
    request: Request,
    user_controller: UserController = Depends(get_user_controller),
) -> list:
    return await get_user_principals(request, user_controller)


Permissions = AccessControl(
    user_principals_getter=get_user_principals_with_deps,
    permission_exception=InsufficientPermissionsException,
)
