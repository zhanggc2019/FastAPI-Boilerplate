from typing import Callable, List

from fastapi import APIRouter, Depends

from app.services import AuthService, UserService
from app.models.user import User
from app.schemas.extras.token import Token
from app.schemas.requests.users import LoginUserRequest, RegisterUserRequest
from app.schemas.responses.users import UserResponse
from app.core.factory.factory import Factory
from app.api.deps import AuthenticationRequired
from app.api.deps.current_user import get_current_user
from app.api.deps.permissions import Permissions
from app.core.permissions import BasePermission

user_router = APIRouter()


@user_router.get("/", dependencies=[Depends(AuthenticationRequired)])
async def get_users(
    user_service: UserService = Depends(Factory().get_user_service),
    assert_access: Callable = Depends(Permissions(str(BasePermission.READ))),
) -> List[UserResponse]:
    users = await user_service.get_all()

    assert_access(resource=users)
    return [UserResponse.model_validate(user) for user in users]


@user_router.post("/register", status_code=201)
async def register_user(
    register_user_request: RegisterUserRequest,
    auth_service: AuthService = Depends(Factory().get_auth_service),
) -> UserResponse:
    user = await auth_service.register(
        email=register_user_request.email,
        password=register_user_request.password,
        username=register_user_request.username,
    )
    return UserResponse.model_validate(user)


@user_router.post("/login")
async def login_user(
    login_user_request: LoginUserRequest,
    auth_service: AuthService = Depends(Factory().get_auth_service),
) -> Token:
    return await auth_service.login(email=login_user_request.email, password=login_user_request.password)


@user_router.get("/profile", dependencies=[Depends(AuthenticationRequired)])
def get_user(
    user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(user)
