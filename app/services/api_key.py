import secrets
from datetime import datetime, timedelta
from uuid import UUID

from app.models.api_key import ApiKey
from app.repositories.api_key import ApiKeyRepository
from app.schemas.api_key import ApiKeyCreate
from app.db import Propagation, Transactional
from app.core.security.encryption import key_encryption

class ApiKeyService:
    def __init__(self, repository: ApiKeyRepository):
        self.repository = repository

    @Transactional(propagation=Propagation.REQUIRED)
    async def create_api_key(self, user_uuid: UUID, data: ApiKeyCreate) -> ApiKey:
        # 生成明文 key
        plaintext_key = f"sk_{secrets.token_urlsafe(32)}"

        # 加密 key 用于存储
        encrypted_key = key_encryption.encrypt(plaintext_key)

        api_key = await self.repository.create({
            "user_uuid": user_uuid,
            "key": encrypted_key,  # 存储加密后的 key
            "name": data.name,
            "expires_at": data.expires_at
        })

        # 返回时附加明文 key (用于首次显示给用户)
        api_key._plaintext_key = plaintext_key
        return api_key

    async def get_user_api_keys(self, user_uuid: UUID) -> list[ApiKey]:
        encrypted_keys = await self.repository.get_by_user_uuid(user_uuid)

        # 解密所有 key
        for api_key in encrypted_keys:
            api_key._plaintext_key = key_encryption.decrypt(api_key.key)

        return encrypted_keys

    @Transactional(propagation=Propagation.REQUIRED)
    async def revoke_api_key(self, user_uuid: UUID, encrypted_key: str) -> bool:
        api_key = await self.repository.get_by(field="key", value=encrypted_key, unique=True)
        if not api_key or api_key.user_uuid != user_uuid:
            return False

        await self.repository.delete(api_key)
        return True

    async def verify_api_key(self, plaintext_key: str) -> ApiKey | None:
        """
        验证 API Key (用于认证)

        Args:
            plaintext_key: 明文 API Key

        Returns:
            如果有效返回 ApiKey 对象,否则返回 None
        """
        # 加密后查询
        encrypted_key = key_encryption.encrypt(plaintext_key)
        api_key = await self.repository.get_by(field="key", value=encrypted_key, unique=True)

        if api_key and api_key.is_active:
            # 检查是否过期
            if api_key.expires_at and api_key.expires_at < datetime.utcnow():
                return None
            return api_key

        return None
