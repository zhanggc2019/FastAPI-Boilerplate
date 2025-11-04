import asyncio
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Set

from app.core.cache.cache_stats import cache_stats_collector
from app.core.logging import logger


@dataclass
class CacheWarmupTask:
    """缓存预热任务"""
    key: str
    function: Callable
    args: tuple
    kwargs: dict
    priority: int = 1
    estimated_duration: float = 1.0  # 预估执行时间（秒）
    dependencies: Optional[List[str]] = None


class CacheWarmer:
    """
    缓存预热器，支持智能预热和批量预热
    """

    def __init__(
        self,
        max_concurrent_tasks: int = 10,
        max_worker_threads: int = 5,
        batch_size: int = 50,
        retry_attempts: int = 3,
        retry_delay: float = 1.0
    ):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.max_worker_threads = max_worker_threads
        self.batch_size = batch_size
        self.retry_attempts = retry_attempts
        self.retry_delay = retry_delay

        self._warmup_tasks: Dict[str, CacheWarmupTask] = {}
        self._completed_tasks: Set[str] = set()
        self._failed_tasks: Dict[str, int] = {}  # key -> failure_count
        self._executor = ThreadPoolExecutor(max_workers=max_worker_threads)
        self._semaphore = asyncio.Semaphore(max_concurrent_tasks)

        self._stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'start_time': None,
            'end_time': None
        }

    def add_warmup_task(
        self,
        key: str,
        function: Callable,
        args: tuple = (),
        kwargs: dict = None,
        priority: int = 1,
        estimated_duration: float = 1.0,
        dependencies: Optional[List[str]] = None
    ) -> None:
        """添加预热任务"""
        if kwargs is None:
            kwargs = {}

        task = CacheWarmupTask(
            key=key,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            estimated_duration=estimated_duration,
            dependencies=dependencies
        )

        self._warmup_tasks[key] = task
        self._stats['total_tasks'] += 1
        logger.info(f"Added warmup task: {key} (priority: {priority})")

    def remove_warmup_task(self, key: str) -> None:
        """移除预热任务"""
        if key in self._warmup_tasks:
            del self._warmup_tasks[key]
            self._stats['total_tasks'] -= 1
            logger.info(f"Removed warmup task: {key}")

    async def warmup_all(self, parallel: bool = True) -> Dict[str, Any]:
        """
        执行所有预热任务

        :param parallel: 是否并行执行
        :return: 预热结果统计
        """
        if not self._warmup_tasks:
            logger.info("No warmup tasks to execute")
            return self.get_stats()

        self._stats['start_time'] = time.time()
        logger.info(f"Starting cache warmup with {len(self._warmup_tasks)} tasks")

        try:
            if parallel:
                await self._execute_parallel()
            else:
                await self._execute_sequential()

            self._stats['end_time'] = time.time()

            # 处理失败任务的重试
            if self._failed_tasks:
                await self._retry_failed_tasks()

            logger.info(f"Cache warmup completed. Success: {self._stats['completed_tasks']}, "
                       f"Failed: {self._stats['failed_tasks']}")

            return self.get_stats()

        except Exception as e:
            logger.error(f"Cache warmup failed: {str(e)}")
            self._stats['end_time'] = time.time()
            return self.get_stats()

    async def warmup_by_pattern(self, pattern: str, cache_backend: Any) -> int:
        """
        根据模式预热缓存（用于预热符合特定模式的键）

        :param pattern: 键模式（支持通配符）
        :param cache_backend: 缓存后端实例
        :return: 预热的键数量
        """
        warmed_keys = 0

        try:
            # 扫描匹配的键
            keys_to_warmup = []
            async for key in cache_backend.scan_iter(match=pattern):
                keys_to_warmup.append(key)

            if not keys_to_warmup:
                logger.info(f"No keys found matching pattern: {pattern}")
                return 0

            logger.info(f"Found {len(keys_to_warmup)} keys matching pattern: {pattern}")

            # 批量预热
            for i in range(0, len(keys_to_warmup), self.batch_size):
                batch = keys_to_warmup[i:i + self.batch_size]
                tasks = []

                for key in batch:
                    task = asyncio.create_task(self._warmup_key(key, cache_backend))
                    tasks.append(task)

                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                warmed_keys += sum(1 for result in batch_results if result is True)

                logger.info(f"Warmed up batch {i//self.batch_size + 1}: "
                           f"{sum(1 for r in batch_results if r is True)}/{len(batch)} keys")

            return warmed_keys

        except Exception as e:
            logger.error(f"Pattern warmup failed: {str(e)}")
            return warmed_keys

    async def _execute_parallel(self) -> None:
        """并行执行预热任务"""
        # 按优先级排序任务
        sorted_tasks = sorted(
            self._warmup_tasks.values(),
            key=lambda x: x.priority,
            reverse=True
        )

        # 分批处理，避免一次性创建过多任务
        for i in range(0, len(sorted_tasks), self.batch_size):
            batch = sorted_tasks[i:i + self.batch_size]
            tasks = []

            for task in batch:
                if self._can_execute_task(task):
                    warmup_task = asyncio.create_task(self._execute_single_task(task))
                    tasks.append(warmup_task)

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_sequential(self) -> None:
        """顺序执行预热任务"""
        sorted_tasks = sorted(
            self._warmup_tasks.values(),
            key=lambda x: x.priority,
            reverse=True
        )

        for task in sorted_tasks:
            if self._can_execute_task(task):
                await self._execute_single_task(task)

    async def _execute_single_task(self, task: CacheWarmupTask) -> bool:
        """执行单个预热任务"""
        async with self._semaphore:
            try:
                start_time = time.time()

                # 执行预热函数
                result = await task.function(*task.args, **task.kwargs)

                # 记录成功
                execution_time = time.time() - start_time
                self._completed_tasks.add(task.key)
                self._stats['completed_tasks'] += 1

                # 记录统计信息
                cache_stats_collector.record_hit(
                    key=task.key,
                    response_time=execution_time,
                    size_bytes=self._estimate_size(result)
                )

                logger.info(f"Warmup task completed: {task.key} "
                           f"(took {execution_time:.2f}s, estimated: {task.estimated_duration}s)")

                return True

            except Exception as e:
                # 记录失败
                self._failed_tasks[task.key] = self._failed_tasks.get(task.key, 0) + 1
                self._stats['failed_tasks'] += 1

                logger.error(f"Warmup task failed: {task.key} - {str(e)}")
                cache_stats_collector.record_error(
                    key=task.key,
                    response_time=time.time() - start_time,
                    error=str(e)
                )

                return False

    async def _retry_failed_tasks(self) -> None:
        """重试失败的任务"""
        retry_tasks = []

        for key, failure_count in self._failed_tasks.items():
            if failure_count < self.retry_attempts:
                task = self._warmup_tasks.get(key)
                if task:
                    retry_tasks.append(task)

        if retry_tasks:
            logger.info(f"Retrying {len(retry_tasks)} failed warmup tasks")

            for task in retry_tasks:
                await asyncio.sleep(self.retry_delay)
                await self._execute_single_task(task)

    def _can_execute_task(self, task: CacheWarmupTask) -> bool:
        """检查是否可以执行任务（检查依赖）"""
        if task.dependencies:
            for dependency in task.dependencies:
                if dependency not in self._completed_tasks:
                    return False
        return True

    async def _warmup_key(self, key: str, cache_backend: Any) -> bool:
        """预热单个键（通过访问它来加载到缓存）"""
        try:
            # 简单地访问键来触发缓存加载
            await cache_backend.get(key)
            return True
        except Exception:
            return False

    def _estimate_size(self, obj: Any) -> int:
        """估算对象大小（简化版）"""
        try:
            import sys
            return sys.getsizeof(obj)
        except Exception:
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """获取预热统计"""
        duration = None
        if self._stats['start_time'] and self._stats['end_time']:
            duration = self._stats['end_time'] - self._stats['start_time']

        return {
            'total_tasks': self._stats['total_tasks'],
            'completed_tasks': self._stats['completed_tasks'],
            'failed_tasks': self._stats['failed_tasks'],
            'success_rate': round(
                (self._stats['completed_tasks'] / max(self._stats['total_tasks'], 1)) * 100,
                2
            ),
            'duration_seconds': duration,
            'failed_tasks_list': list(self._failed_tasks.keys())
        }

    def get_recommendations(self) -> List[str]:
        """获取预热优化建议"""
        recommendations = []

        if self._stats['failed_tasks'] > 0:
            failure_rate = self._stats['failed_tasks'] / max(self._stats['total_tasks'], 1)
            if failure_rate > 0.1:  # 失败率超过10%
                recommendations.append(
                    f"High failure rate ({failure_rate*100:.1f}%) detected. "
                    "Consider increasing retry_attempts or investigating function reliability."
                )

        if self._stats['total_tasks'] > 0:
            avg_duration = (self._stats['end_time'] - self._stats['start_time']) / self._stats['total_tasks']
            if avg_duration > 5:  # 平均任务执行时间超过5秒
                recommendations.append(
                    f"Slow average task execution time ({avg_duration:.1f}s). "
                    "Consider optimizing functions or increasing max_concurrent_tasks."
                )

        return recommendations


class SmartCacheWarmer(CacheWarmer):
    """
    智能缓存预热器，基于使用模式自动预热
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._usage_patterns: Dict[str, Dict[str, Any]] = {}
        self._peak_hours: List[int] = [9, 10, 11, 14, 15, 16, 17]  # 假设的高峰期

    def analyze_usage_pattern(self, key: str, access_time: datetime) -> None:
        """分析使用模式"""
        if key not in self._usage_patterns:
            self._usage_patterns[key] = {
                'access_times': deque(maxlen=1000),
                'access_count': 0,
                'last_access': None,
                'peak_usage': False
            }

        pattern = self._usage_patterns[key]
        pattern['access_times'].append(access_time)
        pattern['access_count'] += 1
        pattern['last_access'] = access_time

        # 检查是否在高峰期使用
        if access_time.hour in self._peak_hours:
            pattern['peak_usage'] = True

    def get_warmup_recommendations(self) -> List[CacheWarmupTask]:
        """基于使用模式获取预热建议"""
        recommendations = []
        current_time = datetime.now()

        for key, pattern in self._usage_patterns.items():
            # 基于访问频率推荐
            if pattern['access_count'] > 10:
                # 基于最后访问时间推荐
                if pattern['last_access']:
                    time_since_last_access = (current_time - pattern['last_access']).total_seconds() / 3600
                    if time_since_last_access < 24:  # 24小时内访问过
                        priority = min(pattern['access_count'], 10)

                        # 如果在高峰期使用，提高优先级
                        if pattern['peak_usage']:
                            priority *= 2

                        recommendations.append(
                            CacheWarmupTask(
                                key=f"smart_warmup_{key}",
                                function=self._create_dummy_function(),
                                args=(),
                                kwargs={'key': key},
                                priority=priority,
                                estimated_duration=0.5
                            )
                        )

        return sorted(recommendations, key=lambda x: x.priority, reverse=True)

    def _create_dummy_function(self) -> Callable:
        """创建虚拟函数用于智能预热"""
        async def dummy_function(key: str):
            # 这里可以集成实际的缓存获取逻辑
            logger.debug(f"Smart warmup for key: {key}")
            return True

        return dummy_function


# 创建全局缓存预热器实例
cache_warmer = CacheWarmer()
smart_cache_warmer = SmartCacheWarmer()
