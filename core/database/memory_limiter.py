"""
内存限流器 - 用于开发环境替代 Redis
"""

import time
from collections import defaultdict, deque
from typing import Dict, Optional
from fastapi import Request, Response
from core.log import logger

class MemoryRateLimiter:
    """内存限流器"""

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