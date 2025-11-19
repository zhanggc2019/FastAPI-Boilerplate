from app.core.logging import logger
from app.db.session import engines
from app.db import Base


async def create_tables() -> None:
    """创建数据库表（动态方式）"""
    print("开始创建数据库表...")

    # 导入所有模型，确保它们被注册到 Base.metadata 中
    # 导入所有模型以确保它们被注册到 Base.metadata
    from app.models import user, task, opera_log  # 导入所有模型

    # 打印 Base 的元数据信息
    print(f"已注册的表: {list(Base.metadata.tables.keys())}")

    # 使用 metadata 创建所有表
    async with engines["writer"].begin() as conn:
        await conn.run_sync(Base.metadata.create_all, checkfirst=True)
    print("数据库表创建完成")