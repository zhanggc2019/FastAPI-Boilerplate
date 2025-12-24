from pydantic import EmailStr

from app.models import User
from app.repositories import UserRepository
from app.schemas.extras.token import Token
from app.services.base import BaseService
from app.db import Propagation, Transactional
from app.core.exceptions import (
    BadRequestException,
    UnauthorizedException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
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
            access_token=JWTHandler.encode(payload={"user_uuid": str(user.uuid)}),
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
