import pickle
import sys
from typing import Any

import ujson
from redis.asyncio import Redis
from redis.exceptions import AuthenticationError, TimeoutError

from core.cache.base import BaseBackend
from core.config import config as settings
from core.log import logger


class RedisBackend(BaseBackend):
    """Redis 后端实现，集成 Redis 客户端功能"""
    
    def __init__(self) -> None:
        """初始化 Redis 客户端"""
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            password=settings.REDIS_PASSWORD,
            db=settings.REDIS_DATABASE,
            socket_timeout=settings.REDIS_TIMEOUT,
            socket_connect_timeout=settings.REDIS_TIMEOUT,
            socket_keepalive=True,  # 保持连接
            health_check_interval=30,  # 健康检查间隔
            decode_responses=True,  # 转码 utf-8
        )

    async def open(self) -> None:
        """触发初始化连接"""
        try:
            await self.redis.ping()
        except TimeoutError:
            logger.error("❌ 数据库 redis 连接超时")
            sys.exit()
        except AuthenticationError:
            logger.error("❌ 数据库 redis 连接认证失败")
            sys.exit()
        except Exception as e:
            logger.error("❌ 数据库 redis 连接异常 {}", e)
            sys.exit()

    async def aclose(self) -> None:
        """关闭 Redis 连接"""
        await self.redis.aclose()

    async def get(self, key: str) -> Any:
        """获取缓存值"""
        result = await self.redis.get(key)
        if not result:
            return

        try:
            # 尝试使用 ujson 解码（更安全）
            return ujson.loads(result.decode("utf8"))
        except (UnicodeDecodeError, ValueError):
            # 只有在必要时才使用 pickle（安全性较低）
            try:
                return pickle.loads(result)
            except (pickle.PickleError, TypeError, ValueError):
                # 如果 pickle 也失败，返回 None
                return None

    async def set(self, response: Any, key: str, ttl: int = 60) -> None:
        """设置缓存值"""
        if isinstance(response, (dict, list, str, int, float, bool)) or response is None:
            # 对于基本数据类型，使用 ujson（更安全）
            response = ujson.dumps(response, ensure_ascii=False).encode("utf8")
        else:
            # 对于复杂对象，使用 pickle（但需要注意安全风险）
            # 在生产环境中，建议实现自定义序列化方法
            response = pickle.dumps(response)

        await self.redis.set(name=key, value=response, ex=ttl)

    async def delete_startswith(self, value: str) -> None:
        """删除指定前缀的所有 key（兼容 BaseBackend 接口）"""
        # 使用 delete_prefix 方法实现，保持向后兼容
        await self.delete_prefix(prefix=value)

    async def delete_prefix(self, prefix: str, exclude: str | list[str] | None = None) -> None:
        """
        删除指定前缀的所有 key

        :param prefix: 前缀
        :param exclude: 排除的 key
        :return:
        """
        keys = []
        async for key in self.redis.scan_iter(match=f"{prefix}*"):
            if isinstance(exclude, str):
                if key != exclude:
                    keys.append(key)
            elif isinstance(exclude, list):
                if key not in exclude:
                    keys.append(key)
            else:
                keys.append(key)
        if keys:
            await self.redis.delete(*keys)

    async def ping(self) -> bool:
        """检查 Redis 连接状态"""
        try:
            await self.redis.ping()
            return True
        except Exception:
            return False


# 创建 RedisBackend 实例
redis_backend = RedisBackend()
