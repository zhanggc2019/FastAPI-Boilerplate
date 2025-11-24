"""
迁移现有 API Keys 数据到新的加密格式

这个脚本会:
1. 读取备份表中的旧数据
2. 对每个 key 进行加密
3. 插入到新表中
"""
import asyncio
import os
from sqlalchemy import text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64

# 从环境变量获取数据库连接
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres3.14@214.10.8.251:5432/fastapi-db-pro")

# 初始化加密
def init_encryption():
    """初始化加密器"""
    encryption_key = os.getenv('ENCRYPTION_KEY', b'development_key_32_bytes_long!!')
    if isinstance(encryption_key, str):
        encryption_key = encryption_key.encode()

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b'fastapi_boilerplate_salt',
        iterations=100000,
        backend=default_backend()
    )
    key = base64.urlsafe_b64encode(kdf.derive(encryption_key))
    return Fernet(key)

cipher = init_encryption()


async def migrate_api_keys():
    """迁移 API Keys 数据"""
    print("开始迁移 API Keys 数据...")

    # 创建异步引擎和会话
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            # 1. 检查备份表是否存在
            result = await session.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'api_keys_backup'
                )
            """))
            backup_exists = result.scalar()
            
            if not backup_exists:
                print("❌ 备份表 api_keys_backup 不存在,请先执行 SQL 迁移脚本")
                return
            
            # 2. 获取备份数据
            result = await session.execute(text("""
                SELECT uuid, key, user_uuid, name, is_active, expires_at, created_at, updated_at
                FROM api_keys_backup
            """))
            old_keys = result.fetchall()
            
            if not old_keys:
                print("✅ 没有需要迁移的数据")
                return
            
            print(f"找到 {len(old_keys)} 条记录需要迁移")
            
            # 3. 迁移每条记录
            migrated = 0
            for row in old_keys:
                uuid, plaintext_key, user_uuid, name, is_active, expires_at, created_at, updated_at = row

                # 加密 key
                encrypted_bytes = cipher.encrypt(plaintext_key.encode())
                encrypted_key = encrypted_bytes.decode()
                
                # 插入新表
                await session.execute(text("""
                    INSERT INTO api_keys (key, user_uuid, name, is_active, expires_at, created_at, updated_at)
                    VALUES (:key, :user_uuid, :name, :is_active, :expires_at, :created_at, :updated_at)
                """), {
                    "key": encrypted_key,
                    "user_uuid": user_uuid,
                    "name": name,
                    "is_active": is_active,
                    "expires_at": expires_at,
                    "created_at": created_at,
                    "updated_at": updated_at
                })
                
                migrated += 1
                print(f"  迁移 {migrated}/{len(old_keys)}: {name} (user: {user_uuid})")
            
            # 4. 提交事务
            await session.commit()
            
            print(f"\n✅ 成功迁移 {migrated} 条记录!")
            print("\n⚠️  重要提示:")
            print("1. 请验证新数据是否正确")
            print("2. 验证通过后可以删除备份表: DROP TABLE api_keys_backup;")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ 迁移失败: {e}")
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(migrate_api_keys())

