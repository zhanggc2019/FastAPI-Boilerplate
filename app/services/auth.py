import httpx
from pydantic import EmailStr

from app.models import User
from app.repositories import UserRepository
from app.schemas.extras.token import Token
from app.core.config import config
from app.services.base import BaseService
from app.db import Propagation, Transactional
from app.core.exceptions import (
    BadRequestException,
    UnauthorizedException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
    ExternalServiceException,
    ExternalServiceTimeoutException,
)
from app.core.security import JWTHandler, PasswordHandler


class AuthService(BaseService[User]):
    """认证与授权服务。"""
    def __init__(self, user_repository: UserRepository):
        super().__init__(model=User, repository=user_repository)
        self.user_repository = user_repository

    @Transactional(propagation=Propagation.REQUIRED)
    async def register(self, email: EmailStr, password: str, username: str) -> User:
        # 验证输入参数
        if not email or not password or not username:
            raise BadRequestException("邮箱、密码和用户名是必需的")

        if len(password) < 8:
            raise BadRequestException("密码长度至少为8个字符")

        if len(username) < 3 or len(username) > 30:
            raise BadRequestException("用户名长度必须在3到30个字符之间")

        # 检查邮箱是否已存在
        user = await self.user_repository.get_by_email(email)

        if user:
            raise UserAlreadyExistsException("该邮箱已被注册")

        # 检查用户名是否已存在
        user = await self.user_repository.get_by_username(username)

        if user:
            raise UserAlreadyExistsException("该用户名已被使用")

        password = PasswordHandler.hash(password)

        return await self.user_repository.create(
            {
                "email": email,
                "password": password,
                "username": username,
            }
        )

    async def login(self, email: EmailStr, password: str) -> Token:
        # 验证输入参数
        if not email or not password:
            raise BadRequestException("邮箱和密码是必需的")

        user = await self.user_repository.get_by_email(email)

        if not user:
            raise InvalidCredentialsException("用户名或密码错误")

        if not PasswordHandler.verify(user.password, password):
            raise InvalidCredentialsException("用户名或密码错误")

        # 检查用户状态
        if not user.is_active:
            raise UnauthorizedException("用户账户未激活", "ACCOUNT_INACTIVE")

        return Token(
            access_token=JWTHandler.encode(payload={"user_id": user.id}),
            refresh_token=JWTHandler.encode(payload={"sub": "refresh_token"}),
        )

    async def refresh_token(self, access_token: str, refresh_token: str) -> Token:
        token = JWTHandler.decode(access_token)
        refresh_token_decoded = JWTHandler.decode(refresh_token)
        if refresh_token_decoded.get("sub") != "refresh_token":
            raise UnauthorizedException("无效的刷新令牌")

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
            raise BadRequestException("不支持的OAuth提供商")

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
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://www.googleapis.com/oauth2/v2/userinfo",
                    headers={"Authorization": f"Bearer {token}"},
                )

                if response.status_code != 200:
                    raise ExternalServiceException(f"Google API error: {response.status_code}")

                user_info = response.json()

                # 验证必需字段
                if not user_info.get("id") or not user_info.get("email"):
                    raise ExternalServiceException("无效的Google用户信息响应")

                return {
                    "id": user_info["id"],
                    "email": user_info["email"],
                }

        except httpx.TimeoutException as err:
            raise ExternalServiceTimeoutException("Google API request timeout") from err
        except httpx.RequestError as e:
            raise ExternalServiceException(f"Google API request failed: {str(e)}") from e
        except Exception as e:
            raise ExternalServiceException(f"Failed to get Google user info: {str(e)}") from e

    async def _get_github_user_info(self, token: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 获取用户信息
                response = await client.get(
                    "https://api.github.com/user",
                    headers={"Authorization": f"Bearer {token}"},
                )
                if response.status_code != 200:
                    raise ExternalServiceException(f"GitHub API error: {response.status_code}")

                user_info = response.json()

                # 获取邮箱信息
                email_response = await client.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {token}"},
                )

                if email_response.status_code != 200:
                    raise ExternalServiceException(f"GitHub email API error: {email_response.status_code}")

                emails = email_response.json()
                primary_email = next((email["email"] for email in emails if email["primary"]), None)

                if not primary_email:
                    raise ExternalServiceException("未找到GitHub用户的主邮箱")

                # 验证必需字段
                if not user_info.get("id"):
                    raise ExternalServiceException("无效的GitHub用户信息响应")

                return {
                    "id": user_info["id"],
                    "email": primary_email,
                }

        except httpx.TimeoutException as err:
            raise ExternalServiceTimeoutException("GitHub API request timeout") from err
        except httpx.RequestError as e:
            raise ExternalServiceException(f"GitHub API request failed: {str(e)}") from e
        except Exception as e:
            raise ExternalServiceException(f"Failed to get GitHub user info: {str(e)}") from e

    async def _get_wechat_user_info(self, code: str) -> dict:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Get access token from WeChat
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
                    raise ExternalServiceException(f"WeChat token API error: {token_response.status_code}")

                token_data = token_response.json()

                if "errcode" in token_data:
                    raise ExternalServiceException(f"WeChat API error: {token_data['errmsg']}")

                # Get user info
                user_response = await client.get(
                    "https://api.weixin.qq.com/sns/userinfo",
                    params={
                        "access_token": token_data["access_token"],
                        "openid": token_data["openid"],
                        "lang": "zh_CN"
                    },
                )

                if user_response.status_code != 200:
                    raise ExternalServiceException(f"WeChat user info API error: {user_response.status_code}")

                user_info = user_response.json()

                if "errcode" in user_info:
                    raise ExternalServiceException(f"WeChat API error: {user_info['errmsg']}")

                # 验证必需字段
                if not user_info.get("openid"):
                    raise ExternalServiceException("无效的微信用户信息响应")

                return {
                    "id": user_info["openid"],
                    "email": f"{user_info['openid']}@wechat.com",  # WeChat doesn't provide email by default
                }

        except httpx.TimeoutException as err:
            raise ExternalServiceTimeoutException("WeChat API request timeout") from err
        except httpx.RequestError as e:
            raise ExternalServiceException(f"WeChat API request failed: {str(e)}") from e
        except Exception as e:
            raise ExternalServiceException(f"Failed to get WeChat user info: {str(e)}") from e

    async def _get_alipay_user_info(self, auth_code: str) -> dict:
        try:
            # For simplicity, we'll simulate the Alipay OAuth process
            # In a real implementation, you would need to use the Alipay SDK
            # to exchange the auth_code for an access token and then get user info

            # 这是一个简化的实现，仅验证授权码格式
            if not auth_code or len(auth_code) < 10:
                raise BadRequestException("无效的支付宝授权码")

            # 模拟支付宝API调用，添加超时控制
            async with httpx.AsyncClient(timeout=10.0):
                # 模拟支付宝API验证
                # 在实际实现中，这里应该调用支付宝的真实API
                if not auth_code.startswith("auth_"):
                    raise ExternalServiceException("无效的支付宝授权码格式")

                # 模拟成功响应
                return {
                    "id": f"alipay_user_{auth_code[:10]}",
                    "email": f"{auth_code[:10]}@alipay.com",  # Alipay doesn't always provide email
                }

        except httpx.TimeoutException as err:
            raise ExternalServiceTimeoutException("Alipay API request timeout") from err
        except httpx.RequestError as e:
            raise ExternalServiceException(f"Alipay API request failed: {str(e)}") from e
        except Exception as e:
            raise ExternalServiceException(f"Failed to get Alipay user info: {str(e)}") from e
