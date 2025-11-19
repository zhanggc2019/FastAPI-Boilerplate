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

from app.core.config import config
from app.core.logging import logger

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


# create_tables 函数已移至 init_db.py 文件


Base = declarative_base()
