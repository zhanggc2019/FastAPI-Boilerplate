from typing import Callable, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from app.controllers import AuthController, UserController
from app.models.user import User
from app.schemas.extras.oauth import OAuthLogin
from app.schemas.extras.token import Token
from app.schemas.requests.users import LoginUserRequest, RegisterUserRequest
from app.schemas.responses.users import UserResponse
from core.config import config
from core.factory import Factory
from core.fastapi.dependencies import AuthenticationRequired
from core.fastapi.dependencies.current_user import get_current_user
from core.fastapi.dependencies.permissions import Permissions
from core.permissions import BasePermission

user_router = APIRouter()


@user_router.get("/", dependencies=[Depends(AuthenticationRequired)])
async def get_users(
    user_controller: UserController = Depends(Factory().get_user_controller),
    assert_access: Callable = Depends(Permissions(str(BasePermission.READ))),
) -> List[UserResponse]:
    users = await user_controller.get_all()

    assert_access(resource=users)
    return [UserResponse.model_validate(user) for user in users]


@user_router.post("/", status_code=201)
async def register_user(
    register_user_request: RegisterUserRequest,
    auth_controller: AuthController = Depends(Factory().get_auth_controller),
) -> UserResponse:
    user = await auth_controller.register(
        email=register_user_request.email,
        password=register_user_request.password,
        username=register_user_request.username,
    )
    return UserResponse.model_validate(user)


@user_router.post("/login")
async def login_user(
    login_user_request: LoginUserRequest,
    auth_controller: AuthController = Depends(Factory().get_auth_controller),
) -> Token:
    return await auth_controller.login(email=login_user_request.email, password=login_user_request.password)


@user_router.get("/profile", dependencies=[Depends(AuthenticationRequired)])
def get_user(
    user: User = Depends(get_current_user),
) -> UserResponse:
    return UserResponse.model_validate(user)


@user_router.post("/oauth/{provider}")
async def oauth_login(
    provider: str,
    oauth_login: OAuthLogin,
    auth_controller: AuthController = Depends(Factory().get_auth_controller),
) -> Token:
    if provider not in ["google", "github", "wechat", "alipay"]:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

    token = await auth_controller.oauth_login(provider, oauth_login.code)
    return token  # type: ignore


@user_router.get("/oauth/{provider}")
async def oauth_redirect(provider: str):
    if provider == "google":
        return RedirectResponse(
            f"https://accounts.google.com/oauth/authorize?"
            f"client_id={config.GOOGLE_CLIENT_ID}&"
            f"redirect_uri={config.GOOGLE_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=openid email profile"
        )
    elif provider == "github":
        return RedirectResponse(
            f"https://github.com/login/oauth/authorize?"
            f"client_id={config.GITHUB_CLIENT_ID}&"
            f"redirect_uri={config.GITHUB_REDIRECT_URI}&"
            f"scope=user:email"
        )
    elif provider == "wechat":
        return RedirectResponse(
            f"https://open.weixin.qq.com/connect/qrconnect?"
            f"appid={config.WECHAT_APP_ID}&"
            f"redirect_uri={config.WECHAT_REDIRECT_URI}&"
            f"response_type=code&"
            f"scope=snsapi_login&"
            f"state=wechat_login"
        )
    elif provider == "alipay":
        # For Alipay, the redirect would typically be handled on the frontend
        # due to the complexity of their OAuth process
        return {"message": "Please use the Alipay QR code login on the frontend"}
    else:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")


@user_router.get("/oauth/{provider}/callback")
async def oauth_callback(provider: str, code: str):
    # This is a simplified callback endpoint
    # In a real application, you would exchange the code for an access token
    # and then redirect to your frontend with the token or set a cookie
    return {
        "message": (
            f"OAuth callback received for {provider} with code {code}. "
            "In a real application, you would exchange this code for an access token."
        )
    }
