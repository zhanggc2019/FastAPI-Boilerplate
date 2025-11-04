import asyncio
import time
from functools import wraps
from typing import Any, Callable, Optional, Type

from app.core.cache.base import BaseBackend, BaseKeyMaker
from app.core.cache.cache_tag import CacheTag
from app.core.exceptions import ExternalServiceTimeoutException
from app.core.logging import logger


class EnhancedCacheManager:
    """
    增强版缓存管理器，提供更完善的缓存策略和错误处理
    """

    def __init__(self):
        self.backend = None
        self.key_maker = None
        self._stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'total_requests': 0
        }
        self._circuit_breaker = CircuitBreaker()

    def init(self, backend: Type[BaseBackend], key_maker: Type[BaseKeyMaker]) -> None:
        """初始化缓存后端和键生成器"""
        self.backend = backend
        self.key_maker = key_maker

    def cached(
        self,
        prefix: str = None,
        tag: CacheTag = None,
        ttl: int = 60,
        stale_while_revalidate: int = 300,
        cache_null_values: bool = True,
        null_ttl: int = 300,
        circuit_breaker_threshold: int = 5,
        fallback_function: Optional[Callable] = None
    ):
        """
        增强版缓存装饰器，支持多种缓存策略

        :param prefix: 缓存键前缀
        :param tag: 缓存标签
        :param ttl: 正常缓存时间（秒）
        :param stale_while_revalidate: 过期后仍可使用的时间（秒）
        :param cache_null_values: 是否缓存空值
        :param null_ttl: 空值缓存时间（秒）
        :param circuit_breaker_threshold: 熔断器阈值
        :param fallback_function: 降级函数
        """
        def _cached(function):
            @wraps(function)
            async def __cached(*args, **kwargs):
                if not self.backend or not self.key_maker:
                    logger.warning("Cache backend or key maker not initialized, executing function directly")
                    return await function(*args, **kwargs)

                self._stats['total_requests'] += 1

                # 检查熔断器状态
                if not self._circuit_breaker.is_available():
                    logger.warning("Cache circuit breaker is open, executing function directly")
                    if fallback_function:
                        return await fallback_function(*args, **kwargs)
                    return await function(*args, **kwargs)

                try:
                    key = await self.key_maker.make(
                        function=function,
                        prefix=prefix if prefix else tag.value,
                    )

                    # 尝试获取缓存
                    cached_response = await self._get_with_timeout(key)

                    if cached_response is not None:
                        # 检查是否是空值缓存
                        if cached_response == '__NULL__':
                            self._stats['hits'] += 1
                            logger.debug(f"Cache hit for null value: {key}")
                            return None

                        # 检查缓存是否过期但仍在stale期间
                        if self._is_stale_cache_valid(cached_response, ttl):
                            self._stats['hits'] += 1
                            logger.debug(f"Cache hit (stale): {key}")
                            # 异步刷新缓存
                            asyncio.create_task(self._refresh_cache(function, key, ttl, *args, **kwargs))
                            return cached_response.get('data')

                        self._stats['hits'] += 1
                        logger.debug(f"Cache hit: {key}")
                        return cached_response

                    # 缓存未命中
                    self._stats['misses'] += 1
                    logger.debug(f"Cache miss: {key}")

                    # 执行原函数
                    response = await function(*args, **kwargs)

                    # 缓存结果
                    if response is not None:
                        await self._set_with_timeout(key, response, ttl)
                    elif cache_null_values:
                        await self._set_with_timeout(key, '__NULL__', null_ttl)

                    return response

                except ExternalServiceTimeoutException:
                    self._circuit_breaker.record_failure()
                    logger.error(f"Cache timeout for function: {function.__name__}")
                    if fallback_function:
                        return await fallback_function(*args, **kwargs)
                    return await function(*args, **kwargs)

                except Exception as e:
                    self._circuit_breaker.record_failure()
                    self._stats['errors'] += 1
                    logger.error(f"Cache error for function {function.__name__}: {str(e)}")
                    if fallback_function:
                        return await fallback_function(*args, **kwargs)
                    return await function(*args, **kwargs)

            return __cached

        return _cached

    async def _get_with_timeout(self, key: str, timeout: float = 5.0) -> Any:
        """带超时的缓存获取"""
        try:
            return await asyncio.wait_for(self.backend.get(key=key), timeout=timeout)
        except asyncio.TimeoutError as err:
            raise ExternalServiceTimeoutException(f"Cache get timeout for key: {key}") from err

    async def _set_with_timeout(self, key: str, value: Any, ttl: int, timeout: float = 5.0) -> None:
        """带超时的缓存设置"""
        try:
            await asyncio.wait_for(self.backend.set(key=key, response=value, ttl=ttl), timeout=timeout)
        except asyncio.TimeoutError as err:
            raise ExternalServiceTimeoutException(f"Cache set timeout for key: {key}") from err

    def _is_stale_cache_valid(self, cached_response: Any, ttl: int) -> bool:
        """检查过期缓存是否仍然有效"""
        if isinstance(cached_response, dict) and 'timestamp' in cached_response:
            current_time = time.time()
            cache_time = cached_response['timestamp']
            return (current_time - cache_time) < ttl * 2  # 2倍TTL内仍然有效
        return False

    async def _refresh_cache(self, function: Callable, key: str, ttl: int, *args, **kwargs) -> None:
        """异步刷新缓存"""
        try:
            response = await function(*args, **kwargs)
            if response is not None:
                cache_data = {
                    'data': response,
                    'timestamp': time.time()
                }
                await self._set_with_timeout(key, cache_data, ttl)
        except Exception as e:
            logger.error(f"Failed to refresh cache for key {key}: {str(e)}")

    async def remove_by_tag(self, tag: CacheTag) -> None:
        """根据标签删除缓存"""
        if self.backend:
            try:
                await self.backend.delete_startswith(value=tag.value)
            except Exception as e:
                logger.error(f"Failed to remove cache by tag {tag.value}: {str(e)}")

    async def remove_by_prefix(self, prefix: str) -> None:
        """根据前缀删除缓存"""
        if self.backend:
            try:
                await self.backend.delete_startswith(value=prefix)
            except Exception as e:
                logger.error(f"Failed to remove cache by prefix {prefix}: {str(e)}")

    def get_stats(self) -> dict:
        """获取缓存统计信息"""
        hit_rate = (self._stats['hits'] / max(self._stats['total_requests'], 1)) * 100
        return {
            **self._stats,
            'hit_rate': round(hit_rate, 2),
            'circuit_breaker_status': 'closed' if self._circuit_breaker.is_available() else 'open'
        }

    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            'hits': 0,
            'misses': 0,
            'errors': 0,
            'total_requests': 0
        }


class CircuitBreaker:
    """熔断器实现"""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open

    def is_available(self) -> bool:
        """检查服务是否可用"""
        if self.state == 'closed':
            return True
        elif self.state == 'open':
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.recovery_timeout:
                self.state = 'half_open'
                return True
            return False
        else:  # half_open
            return True

    def record_failure(self) -> None:
        """记录失败"""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")

    def record_success(self) -> None:
        """记录成功"""
        if self.state == 'half_open':
            self.state = 'closed'
            self.failure_count = 0
            logger.info("Circuit breaker closed after successful request")


# 创建增强版缓存管理器实例
enhanced_cache = EnhancedCacheManager()
