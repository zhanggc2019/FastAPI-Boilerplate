import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import config


async def add_is_active_column():
    """直接向users表添加is_active列"""
    print("开始添加is_active列...")
    
    # 创建数据库引擎
    engine = create_async_engine(
        config.postgres_url_str,
        **config.database_pool_config
    )
    
    try:
        # 直接执行ALTER TABLE语句
        async with engine.begin() as conn:
            # 首先检查列是否已存在
            result = await conn.execute(
                text("SELECT column_name FROM information_schema.columns "
                     "WHERE table_name = 'users' AND column_name = 'is_active'")
            )
            
            if not result.scalar_one_or_none():
                # 列不存在，添加它
                await conn.execute(
                    text("ALTER TABLE users ADD COLUMN is_active BOOLEAN DEFAULT TRUE")
                )
                print("✅ is_active列添加成功")
            else:
                print("ℹ️ is_active列已存在")
    except Exception as e:
        print(f"❌ 添加is_active列时出错: {e}")
    finally:
        await engine.dispose()
        print("数据库连接已关闭")


if __name__ == "__main__":
    asyncio.run(add_is_active_column())