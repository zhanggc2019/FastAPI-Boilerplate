from pydantic import EmailStr
import httpx

from app.models import User
from app.repositories import UserRepository
from app.schemas.extras.token import Token
from core.controller import BaseController
from core.database import Propagation, Transactional
from core.exceptions import BadRequestException, UnauthorizedException
from core.security import JWTHandler, PasswordHandler
from core.config import config


class AuthController(BaseController[User]):
    def __init__(self, user_repository: UserRepository):
        super().__init__(model=User, repository=user_repository)
        self.user_repository = user_repository

    @Transactional(propagation=Propagation.REQUIRED)
    async def register(self, email: EmailStr, password: str, username: str) -> User:
        # Check if user exists with email
        user = await self.user_repository.get_by_email(email)

        if user:
            raise BadRequestException("User already exists with this email")

        # Check if user exists with username
        user = await self.user_repository.get_by_username(username)

        if user:
            raise BadRequestException("User already exists with this username")

        password = PasswordHandler.hash(password)

        return await self.user_repository.create(
            {
                "email": email,
                "password": password,
                "username": username,
            }
        )

    async def login(self, email: EmailStr, password: str) -> Token:
        user = await self.user_repository.get_by_email(email)

        if not user:
            raise BadRequestException("Invalid credentials")

        if not PasswordHandler.verify(user.password, password):
            raise BadRequestException("Invalid credentials")

        return Token(
            access_token=JWTHandler.encode(payload={"user_id": user.id}),
            refresh_token=JWTHandler.encode(payload={"sub": "refresh_token"}),
        )

    async def refresh_token(self, access_token: str, refresh_token: str) -> Token:
        token = JWTHandler.decode(access_token)
        refresh_token_decoded = JWTHandler.decode(refresh_token)
        if refresh_token_decoded.get("sub") != "refresh_token":
            raise UnauthorizedException("Invalid refresh token")

        return Token(
            access_token=JWTHandler.encode(payload={"user_id": token.get("user_id")}),
            refresh_token=JWTHandler.encode(payload={"sub": "refresh_token"}),
        )

    @Transactional(propagation=Propagation.REQUIRED)
    async def oauth_login(self, provider: str, token: str) -> Token:
        if provider == "google":
            user_info = await self._get_google_user_info(token)
        elif provider == "github":
            user_info = await self._get_github_user_info(token)
        elif provider == "wechat":
            user_info = await self._get_wechat_user_info(token)
        elif provider == "alipay":
            user_info = await self._get_alipay_user_info(token)
        else:
            raise BadRequestException("Unsupported OAuth provider")

        # Check if user exists with email
        user = await self.user_repository.get_by_email(user_info["email"])

        # Create user if not exists
        if not user:
            username = user_info["email"].split("@")[0]
            # Ensure username is unique
            existing_user = await self.user_repository.get_by_username(username)
            if existing_user:
                username = f"{username}_{user_info['id']}"

            user = await self.user_repository.create(
                {
                    "email": user_info["email"],
                    "username": username,
                    "password": PasswordHandler.hash(provider + str(user_info["id"])),
                }
            )

        return Token(
            access_token=JWTHandler.encode(payload={"user_id": user.id}),
            refresh_token=JWTHandler.encode(payload={"sub": "refresh_token"}),
        )

    async def _get_google_user_info(self, token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code != 200:
                raise BadRequestException("Invalid Google token")

            user_info = response.json()
            return {
                "id": user_info["id"],
                "email": user_info["email"],
            }

    async def _get_github_user_info(self, token: str) -> dict:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {token}"},
            )
            if response.status_code != 200:
                raise BadRequestException("Invalid GitHub token")

            user_info = response.json()

            # Get email as it's not always returned in the main user endpoint
            email_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {token}"},
            )
            emails = email_response.json()
            primary_email = next((email["email"] for email in emails if email["primary"]), None)

            if not primary_email:
                raise BadRequestException("No email found for GitHub user")

            return {
                "id": user_info["id"],
                "email": primary_email,
            }

    async def _get_wechat_user_info(self, code: str) -> dict:
        # Get access token from WeChat
        async with httpx.AsyncClient() as client:
            token_response = await client.get(
                "https://api.weixin.qq.com/sns/oauth2/access_token",
                params={
                    "appid": config.WECHAT_APP_ID,
                    "secret": config.WECHAT_APP_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                raise BadRequestException("Failed to get WeChat access token")

            token_data = token_response.json()

            if "errcode" in token_data:
                raise BadRequestException(f"WeChat API error: {token_data['errmsg']}")

            # Get user info
            user_response = await client.get(
                "https://api.weixin.qq.com/sns/userinfo",
                params={"access_token": token_data["access_token"], "openid": token_data["openid"], "lang": "zh_CN"},
            )

            if user_response.status_code != 200:
                raise BadRequestException("Failed to get WeChat user info")

            user_info = user_response.json()

            if "errcode" in user_info:
                raise BadRequestException(f"WeChat API error: {user_info['errmsg']}")

            return {
                "id": user_info["openid"],
                "email": f"{user_info['openid']}@wechat.com",  # WeChat doesn't provide email by default
            }

    async def _get_alipay_user_info(self, auth_code: str) -> dict:
        # For simplicity, we'll simulate the Alipay OAuth process
        # In a real implementation, you would need to use the Alipay SDK
        # to exchange the auth_code for an access token and then get user info

        # This is a simplified implementation that just validates the auth_code format
        if not auth_code or len(auth_code) < 10:
            raise BadRequestException("Invalid Alipay auth code")

        # In a real implementation, you would make requests to Alipay APIs here
        # For now, we'll simulate a successful response
        return {
            "id": f"alipay_user_{auth_code[:10]}",
            "email": f"{auth_code[:10]}@alipay.com",  # Alipay doesn't always provide email
        }
