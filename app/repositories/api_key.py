from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.repositories.base import BaseRepository

class ApiKeyRepository(BaseRepository[ApiKey]):
    async def get_by_key(self, key: str) -> ApiKey | None:
        stmt = select(ApiKey).where(ApiKey.key == key)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_user_uuid(self, user_uuid: UUID) -> list[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.user_uuid == user_uuid)
        result = await self.session.execute(stmt)
        return result.scalars().all()
