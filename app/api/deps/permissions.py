from http import HTTPStatus

from fastapi import Depends, Request

from app.core.exceptions import CustomException
from app.core.factory import Factory
from app.core.security.access_control import (
    AccessControl,
    Authenticated,
    Everyone,
    RolePrincipal,
    UserPrincipal,
)
from app.services import UserService


class InsufficientPermissionsException(CustomException):
    code = HTTPStatus.FORBIDDEN
    error_code = HTTPStatus.FORBIDDEN
    message = "Insufficient permissions"


def get_user_service() -> UserService:
    """获取用户服务实例以解析权限主体。"""
    return Factory().get_user_service()


async def get_user_principals(
    request: Request,
    user_service: UserService | None = None,
) -> list:
    """
    依据当前请求构建权限主体列表。

    Args:
        request: FastAPI 请求对象，携带认证上下文。
        user_service: 用户服务实例，未显式传入时会通过工厂创建。

    Returns:
        与当前用户关联的权限主体集合。
    """
    if user_service is None:
        user_service = Factory().get_user_service()

    principals: list = [Everyone]
    user_id = getattr(request.user, "id", None)

    if not user_id:
        return principals

    user = await user_service.get_by_id(id_=user_id)

    principals.append(Authenticated)
    principals.append(UserPrincipal(user.id))

    if getattr(user, "is_admin", False):
        principals.append(RolePrincipal("admin"))

    return principals


async def get_user_principals_with_deps(
    request: Request,
    user_service: UserService = Depends(get_user_service),
) -> list:
    """FastAPI 依赖形式的权限主体解析器。"""
    return await get_user_principals(request, user_service)


Permissions = AccessControl(
    user_principals_getter=get_user_principals_with_deps,
    permission_exception=InsufficientPermissionsException,
)

