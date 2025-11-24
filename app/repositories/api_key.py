from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.repositories.base import BaseRepository

class ApiKeyRepository(BaseRepository[ApiKey]):
    async def get_by_key(self, session: AsyncSession, key: str) -> ApiKey | None:
        stmt = select(ApiKey).where(ApiKey.key == key)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_by_user_id(self, session: AsyncSession, user_id: int) -> list[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.user_id == user_id)
        result = await session.execute(stmt)
        return result.scalars().all()
