#!/usr/bin/env python3
"""
简单的内存限流器测试脚本
用于测试限流逻辑是否正确
"""

import asyncio
import time
from collections import defaultdict, deque
from typing import Dict

class InMemoryRateLimiter:
    """内存限流器"""

    def __init__(self):
        # 使用字典存储每个键的请求时间队列
        self.requests: Dict[str, deque] = defaultdict(lambda: deque())

    async def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """
        检查是否允许请求

        :param key: 限流键（通常是IP地址）
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
            # 计算最早请求的剩余时间
            oldest_request = request_times[0]
            retry_after = int(oldest_request + window - current_time) + 1
            return False, retry_after

        # 记录当前请求
        request_times.append(current_time)
        return True, 0

# 全局限流器实例
limiter = InMemoryRateLimiter()

async def simulate_rate_limit_test(ip: str, request_count: int = 10):
    """
    模拟限流测试

    :param ip: 模拟的IP地址
    :param request_count: 请求次数
    """
    print(f"开始测试 IP: {ip}, 请求次数: {request_count}")
    print("-" * 50)

    for i in range(request_count):
        allowed, retry_after = await limiter.is_allowed(f"test:{ip}", 5, 60)  # 5次/分钟

        current_time = time.strftime("%H:%M:%S")
        if allowed:
            print(f"请求 {i+1:2d} [{current_time}] [允许] 访问成功")
        else:
            print(f"请求 {i+1:2d} [{current_time}] [限流] {retry_after}秒后重试")

        # 每次请求间隔1秒
        if i < request_count - 1:
            await asyncio.sleep(1)

    print("-" * 50)
    print()

async def main():
    """主函数"""
    print("限流测试开始")
    print("测试规则: 5次/分钟")
    print()

    # 测试单个IP的限流
    await simulate_rate_limit_test("192.168.1.100", 8)

    # 测试不同IP的限流（应该互不影响）
    print("同时测试不同IP的限流效果:")
    tasks = [
        simulate_rate_limit_test("192.168.1.101", 6),
        simulate_rate_limit_test("192.168.1.102", 6)
    ]
    await asyncio.gather(*tasks)

    print("限流测试完成")

if __name__ == "__main__":
    asyncio.run(main())