import asyncio
import os
from typing import Generator

import pytest
import pytest_asyncio
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

import app.db.transactional as transactional
from app.models import Base
from app.core.config import config

# Load environment variables from .env file
load_dotenv(".env")

# 优先使用环境变量，其次使用 YAML 配置中的 test_url
TEST_DATABASE_URL = os.getenv("TEST_POSTGRES_URL") or str(config.TEST_POSTGRES_URL) if config.TEST_POSTGRES_URL else str(config.POSTGRES_URL)

# Convert to asyncpg format if needed
if TEST_DATABASE_URL and not TEST_DATABASE_URL.startswith("postgresql+asyncpg://"):
    TEST_DATABASE_URL = TEST_DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")

print(f"Using test database URL: {TEST_DATABASE_URL}")


@pytest.fixture(scope="session")
def event_loop(request) -> Generator:  # noqa: F401
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncSession:
    async_engine = create_async_engine(config.POSTGRES_URL)
    session = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

    async with session() as s:
        async with async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        transactional.session = s
        yield s

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        pass

    await async_engine.dispose()
