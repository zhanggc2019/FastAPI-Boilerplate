from contextvars import ContextVar, Token
from typing import Union

from sqlalchemy import URL
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_scoped_session,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.sql.expression import Delete, Insert, Update

from core.config import config
from core.log import logger

session_context: ContextVar[str] = ContextVar("session_context")


def get_session_context() -> str:
    return session_context.get()


def set_session_context(session_id: str) -> Token:
    return session_context.set(session_id)


def reset_session_context(context: Token) -> None:
    session_context.reset(context)


engines = {
    "writer": create_async_engine(config.postgres_url_str, **config.database_pool_config),
    "reader": create_async_engine(config.postgres_url_str, **config.database_pool_config),
}


class RoutingSession(Session):
    def get_bind(self, mapper=None, clause=None, **kwargs):
        if self._flushing or isinstance(clause, (Update, Delete, Insert)):
            return engines["writer"].sync_engine
        return engines["reader"].sync_engine


async_session_factory = async_sessionmaker(
    class_=AsyncSession,
    sync_session_class=RoutingSession,
    expire_on_commit=False,
)

session: Union[AsyncSession, async_scoped_session] = async_scoped_session(
    session_factory=async_session_factory,
    scopefunc=get_session_context,
)


def create_async_engine_and_session(url: str | URL) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    """
    创建数据库引擎和 Session

    :param url: 数据库连接 URL
    :return:
    """
    try:
        # 数据库引擎 - 使用基于环境的优化配置
        pool_config = config.database_pool_config
        engine = create_async_engine(
            url,
            echo=config.SHOW_SQL_ALCHEMY_QUERIES,
            echo_pool=config.DATABASE_POOL_ECHO,
            future=True,
            **pool_config  # 使用基于环境的连接池配置
        )
    except Exception as e:
        logger.error("❌ 数据库链接失败 {}", e)
        import sys

        sys.exit()
    else:
        db_session = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            autoflush=False,  # 禁用自动刷新
            expire_on_commit=False,  # 禁用提交时过期
        )
        return engine, db_session


async def get_session():
    """
    Get the database session.
    This can be used for dependency injection.

    :return: The database session.
    """
    try:
        yield session
    finally:
        await session.close()


async def create_tables() -> None:
    """创建数据库表（动态方式）"""
    print("开始创建数据库表...")

    # 导入所有模型，确保它们被注册到 Base.metadata 中
    from core.database import Base

    # 打印 Base 的元数据信息
    print(f"已注册的表: {list(Base.metadata.tables.keys())}")

    # 使用 metadata 创建所有表
    async with engines["writer"].begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    print("数据库表创建完成")


Base = declarative_base()
