from uuid import UUID
from app.models import User
from app.repositories import UserRepository
from app.services.base import BaseService
from app.core.exceptions import (
    UserNotFoundException,
    UserAlreadyExistsException,
    DataValidationException,
)


class UserService(BaseService[User]):
    """用户相关业务服务。"""
    def __init__(self, user_repository: UserRepository):
        super().__init__(model=User, repository=user_repository)
        self.user_repository = user_repository

    async def get_by_username(self, username: str) -> User:
        if not username or len(username.strip()) == 0:
            raise DataValidationException("Username cannot be empty")

        if len(username) < 3 or len(username) > 30:
            raise DataValidationException("Username must be between 3 and 30 characters")

        user = await self.user_repository.get_by_username(username)
        if not user:
            raise UserNotFoundException(f"User with username '{username}' not found")
        return user

    async def get_by_email(self, email: str) -> User:
        if not email or len(email.strip()) == 0:
            raise DataValidationException("Email cannot be empty")

        # 简单的邮箱格式验证
        if "@" not in email or "." not in email.split("@")[1]:
            raise DataValidationException("Invalid email format")

        user = await self.user_repository.get_by_email(email)
        if not user:
            raise UserNotFoundException(f"User with email '{email}' not found")
        return user

    async def create_user(self, user_data: dict) -> User:
        """创建用户，包含业务逻辑验证"""
        # 参数验证
        if not user_data.get("email"):
            raise DataValidationException("Email is required")

        if not user_data.get("username"):
            raise DataValidationException("Username is required")

        if not user_data.get("password"):
            raise DataValidationException("Password is required")

        # 验证邮箱格式
        email = user_data["email"]
        if "@" not in email or "." not in email.split("@")[1]:
            raise DataValidationException("Invalid email format")

        # 验证用户名格式
        username = user_data["username"]
        if len(username) < 3 or len(username) > 30:
            raise DataValidationException("Username must be between 3 and 30 characters")

        if not username.replace("_", "").replace("-", "").isalnum():
            raise DataValidationException("Username can only contain letters, numbers, underscores, and hyphens")

        # 验证密码强度
        password = user_data["password"]
        if len(password) < 8:
            raise DataValidationException("Password must be at least 8 characters long")

        # 检查用户是否已存在
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise UserAlreadyExistsException(f"User with email '{email}' already exists")

        existing_user = await self.user_repository.get_by_username(username)
        if existing_user:
            raise UserAlreadyExistsException(f"User with username '{username}' already exists")

        # 创建用户
        return await self.user_repository.create(user_data)

    async def update_user(self, user_uuid: UUID, update_data: dict) -> User:
        """更新用户信息，包含业务逻辑验证"""
        if not user_uuid:
            raise DataValidationException("User UUID is required")

        if not update_data:
            raise DataValidationException("Update data cannot be empty")

        # 检查用户是否存在
        existing_user = await self.user_repository.get_by("uuid", user_uuid, unique=True)
        if not existing_user:
            raise UserNotFoundException(f"User with UUID {user_uuid} not found")

        # 如果更新邮箱，验证格式和唯一性
        if "email" in update_data:
            email = update_data["email"]
            if "@" not in email or "." not in email.split("@")[1]:
                raise DataValidationException("Invalid email format")

            # 检查新邮箱是否已被其他用户使用
            email_user = await self.user_repository.get_by_email(email)
            if email_user and email_user.uuid != user_uuid:
                raise UserAlreadyExistsException(f"Email '{email}' is already used by another user")

        # 如果更新用户名，验证格式和唯一性
        if "username" in update_data:
            username = update_data["username"]
            if len(username) < 3 or len(username) > 30:
                raise DataValidationException("Username must be between 3 and 30 characters")

            if not username.replace("_", "").replace("-", "").isalnum():
                raise DataValidationException("Username can only contain letters, numbers, underscores, and hyphens")

            # 检查新用户名是否已被其他用户使用
            username_user = await self.user_repository.get_by_username(username)
            if username_user and username_user.uuid != user_uuid:
                raise UserAlreadyExistsException(f"Username '{username}' is already used by another user")

        # 如果更新密码，验证强度
        if "password" in update_data:
            password = update_data["password"]
            if len(password) < 8:
                raise DataValidationException("Password must be at least 8 characters long")

        # 更新用户信息
        return await self.user_repository.update(existing_user, update_data)
