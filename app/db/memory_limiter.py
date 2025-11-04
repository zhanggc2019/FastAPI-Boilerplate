"""
内存限流器 - 用于开发环境替代 Redis
"""

import time
from collections import defaultdict, deque
from typing import Dict

from fastapi import Request

from app.core.logging import logger


class MemoryRateLimiter:
    """内存限流器-本项目暂时未使用"""

    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())
        self.logger = logger

    async def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """
        检查是否允许请求

        :param key: 限流键
        :param limit: 限制次数
        :param window: 时间窗口（秒）
        :return: (是否允许, 剩余重试时间)
        """
        current_time = time.time()
        request_times = self.requests[key]

        # 清理过期的请求记录
        while request_times and request_times[0] <= current_time - window:
            request_times.popleft()

        # 检查是否超过限制
        if len(request_times) >= limit:
            oldest_request = request_times[0]
            retry_after = int(oldest_request + window - current_time) + 1
            return False, retry_after

        # 记录当前请求
        request_times.append(current_time)
        return True, 0

    def get_key(self, request: Request) -> str:
        """生成限流键"""
        # 使用 IP 地址作为限流键
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            ip = forwarded_for.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"rate_limit:{ip}"


# 创建全局内存限流器实例
memory_limiter = MemoryRateLimiter()


async def demo_memory_limiter(request: Request, limit: int = 60, window: int = 60) -> tuple[bool, int]:
    """
    使用内存限流器的示例函数，通常可作为 FastAPI 依赖调用。

    Args:
        request: 当前请求对象，用于生成限流标识。
        limit: 允许的最大请求次数。
        window: 计算窗口长度（秒）。

    Returns:
        包含是否允许继续请求及需要等待的秒数的二元组。
    """
    key = memory_limiter.get_key(request)
    allowed, retry_after = await memory_limiter.is_allowed(key=key, limit=limit, window=window)

    if not allowed:
        logger.warning("Memory rate limiter triggered for key=%s; retry after %s seconds.", key, retry_after)

    return allowed, retry_after
