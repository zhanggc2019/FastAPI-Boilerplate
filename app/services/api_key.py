import secrets
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.repositories.api_key import ApiKeyRepository
from app.schemas.api_key import ApiKeyCreate

class ApiKeyService:
    def __init__(self, repository: ApiKeyRepository):
        self.repository = repository

    async def create_api_key(self, session: AsyncSession, user_id: int, data: ApiKeyCreate) -> ApiKey:
        key = f"sk_{secrets.token_urlsafe(32)}"
        api_key = ApiKey(
            user_id=user_id,
            key=key,
            name=data.name,
            expires_at=data.expires_at
        )
        return await self.repository.create(session, api_key)

    async def get_user_api_keys(self, session: AsyncSession, user_id: int) -> list[ApiKey]:
        return await self.repository.get_by_user_id(session, user_id)

    async def revoke_api_key(self, session: AsyncSession, user_id: int, key_id: int) -> bool:
        api_key = await self.repository.get(session, key_id)
        if not api_key or api_key.user_id != user_id:
            return False
        
        await self.repository.delete(session, key_id)
        return True
