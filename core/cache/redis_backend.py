import pickle
from typing import Any

import redis.asyncio as aioredis
import ujson

from core.cache.base import BaseBackend
from core.config import config

redis = aioredis.from_url(url=config.redis_url_str)


class RedisBackend(BaseBackend):
    async def get(self, key: str) -> Any:
        result = await redis.get(key)
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
        if isinstance(response, (dict, list, str, int, float, bool)) or response is None:
            # 对于基本数据类型，使用 ujson（更安全）
            response = ujson.dumps(response, ensure_ascii=False).encode("utf8")
        else:
            # 对于复杂对象，使用 pickle（但需要注意安全风险）
            # 在生产环境中，建议实现自定义序列化方法
            response = pickle.dumps(response)

        await redis.set(name=key, value=response, ex=ttl)

    async def delete_startswith(self, value: str) -> None:
        async for key in redis.scan_iter(f"{value}::*"):
            await redis.delete(key)
