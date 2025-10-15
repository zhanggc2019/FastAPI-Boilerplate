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

from core.common.model import MappedBase
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
    "writer": create_async_engine(config.postgres_url_str, pool_recycle=3600),
    "reader": create_async_engine(config.postgres_url_str, pool_recycle=3600),
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
        # 数据库引擎
        engine = create_async_engine(
            url,
            echo=config.SHOW_SQL_ALCHEMY_QUERIES,
            echo_pool=config.DATABASE_POOL_ECHO,
            future=True,
            # 中等并发
            pool_size=10,  # 低：- 高：+
            max_overflow=20,  # 低：- 高：+
            pool_timeout=30,  # 低：+ 高：-
            pool_recycle=3600,  # 低：+ 高：-
            pool_pre_ping=True,  # 低：False 高：True
            pool_use_lifo=False,  # 低：False 高：True
        )
    except Exception as e:
        logger.error('❌ 数据库链接失败 {}', e)
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
    """创建数据库表"""
    # 修复原有的 create_tables 方法
    print("开始创建数据库表...")
    
    # 确保模型被导入，这样它们会被注册到 MappedBase.metadata 中
    from app.models.user import User
    from app.models.task import Task
    
    # 手动触发模型的导入
    _ = User
    _ = Task
    
    # 打印 MappedBase 的元数据信息
    print(f"导入模型后，已注册的表: {list(MappedBase.metadata.tables.keys())}")
    print(f"MappedBase 类: {MappedBase}")
    print(f"MappedBase metadata: {MappedBase.metadata}")
    
    # 检查 User 和 Task 类的元数据
    print(f"User.__table__: {User.__table__}")
    print(f"Task.__table__: {Task.__table__}")
    
    # 直接使用 User 和 Task 的元数据来创建表
    async with engines["writer"].begin() as conn:
        await conn.run_sync(User.__table__.create, checkfirst=True)
        await conn.run_sync(Task.__table__.create, checkfirst=True)
    print("数据库表创建完成")



Base = declarative_base()