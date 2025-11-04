import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from datetime import datetime

from app.core.cache import cache_warmer, cache_monitor, cache_stats_collector, enhanced_cache, smart_cache_warmer
from app.core.exceptions import CacheException
from tests.enhanced_test_data import generate_test_user, generate_test_task


class TestCacheIntegration:
    """缓存集成测试"""

    @pytest.fixture(autouse=True)
    async def setup(self):
        """测试前清理缓存"""
        await enhanced_cache.clear()
        cache_stats_collector.reset_stats()
        yield
        await enhanced_cache.clear()

    async def test_basic_cache_operations(self):
        """测试基本缓存操作"""
        # 测试设置和获取
        key = "test_key"
        value = {"data": "test_value", "timestamp": datetime.now().isoformat()}

        await enhanced_cache.set(key, value, ttl=60)
        cached_value = await enhanced_cache.get(key)

        assert cached_value == value

        # 测试删除
        await enhanced_cache.delete(key)
        cached_value = await enhanced_cache.get(key)
        assert cached_value is None

    async def test_cache_with_complex_data(self):
        """测试复杂数据类型的缓存"""
        user_data = generate_test_user()
        task_data = generate_test_task()

        # 缓存用户数据
        await enhanced_cache.set(f"user:{user_data['id']}", user_data, ttl=300)
        cached_user = await enhanced_cache.get(f"user:{user_data['id']}")
        assert cached_user == user_data

        # 缓存任务数据
        await enhanced_cache.set(f"task:{task_data['id']}", task_data, ttl=300)
        cached_task = await enhanced_cache.get(f"task:{task_data['id']}")
        assert cached_task == task_data

    async def test_cache_ttl_expiration(self):
        """测试缓存过期"""
        key = "ttl_test_key"
        value = "test_value"

        # 设置1秒过期
        await enhanced_cache.set(key, value, ttl=1)

        # 立即获取应该存在
        cached_value = await enhanced_cache.get(key)
        assert cached_value == value

        # 等待过期
        await asyncio.sleep(2)

        # 过期后应该不存在
        cached_value = await enhanced_cache.get(key)
        assert cached_value is None

    async def test_cache_decorator_functionality(self):
        """测试缓存装饰器功能"""
        call_count = 0

        @enhanced_cache.cached(ttl=60, key_prefix="test_decorator")
        async def expensive_function(user_id: int, include_details: bool = False):
            nonlocal call_count
            call_count += 1

            # 模拟耗时操作
            await asyncio.sleep(0.1)

            return {
                "user_id": user_id,
                "include_details": include_details,
                "data": f"expensive_data_{user_id}",
                "computed_at": datetime.now().isoformat(),
            }

        # 第一次调用应该执行函数
        result1 = await expensive_function(123, include_details=True)
        assert call_count == 1
        assert result1["user_id"] == 123
        assert result1["include_details"] is True

        # 第二次调用应该使用缓存
        result2 = await expensive_function(123, include_details=True)
        assert call_count == 1  # 不应该增加
        assert result2 == result1

        # 不同参数应该执行函数
        result3 = await expensive_function(456, include_details=False)
        assert call_count == 2
        assert result3["user_id"] == 456
        assert result3["include_details"] is False

    async def test_cache_warmer_functionality(self):
        """测试缓存预热器"""
        # 添加预热任务
        warmup_data = [
            {"id": 1, "name": "User 1", "email": "user1@example.com"},
            {"id": 2, "name": "User 2", "email": "user2@example.com"},
            {"id": 3, "name": "User 3", "email": "user3@example.com"},
        ]

        for user in warmup_data:
            await cache_warmer.add_warmup_task(f"user:{user['id']}", lambda u=user: u, ttl=300)

        # 执行预热
        await cache_warmer.execute_warmup()

        # 验证数据已缓存
        for user in warmup_data:
            cached_user = await enhanced_cache.get(f"user:{user['id']}")
            assert cached_user == user

    async def test_smart_cache_warmer(self):
        """测试智能缓存预热器"""
        # 模拟访问模式
        access_patterns = [("user:1", 100), ("user:2", 80), ("user:3", 60), ("user:4", 40), ("user:5", 20)]

        # 记录访问模式
        for key, count in access_patterns:
            for _ in range(count):
                await smart_cache_warmer.record_access(key)

        # 基于访问模式生成预热建议
        recommendations = await smart_cache_warmer.generate_warmup_recommendations(min_access_count=50, top_k=3)

        assert len(recommendations) == 3
        assert "user:1" in recommendations
        assert "user:2" in recommendations
        assert "user:3" in recommendations

    async def test_cache_monitor_alerts(self):
        """测试缓存监控警报"""
        # 启动监控
        await cache_monitor.start_monitoring()

        # 模拟低命中率
        for i in range(100):
            await enhanced_cache.get(f"non_existent_key_{i}")

        # 等待监控检查
        await asyncio.sleep(2)

        # 获取警报
        alerts = cache_monitor.get_active_alerts()

        # 应该有关低命中率的警报
        hit_rate_alerts = [alert for alert in alerts if "hit_rate" in alert.alert_type]
        assert len(hit_rate_alerts) > 0

        # 停止监控
        await cache_monitor.stop_monitoring()

    async def test_cache_circuit_breaker(self):
        """测试缓存熔断器"""
        # 模拟Redis故障
        with patch.object(enhanced_cache, "get", side_effect=Exception("Redis connection failed")):
            with patch.object(enhanced_cache, "set", side_effect=Exception("Redis connection failed")):
                # 多次失败后应该触发熔断
                for i in range(10):
                    try:
                        await enhanced_cache.get(f"test_key_{i}")
                    except Exception:
                        pass

                # 检查熔断器状态
                assert enhanced_cache.circuit_breaker.state == "OPEN"

                # 等待熔断器进入半开状态
                await asyncio.sleep(6)

                # 重置mock
                enhanced_cache.get = AsyncMock(return_value="test_value")
                enhanced_cache.set = AsyncMock(return_value=True)

                # 应该可以尝试恢复
                result = await enhanced_cache.get("recovery_test")
                assert result == "test_value"

    async def test_cache_stats_collection(self):
        """测试缓存统计收集"""
        # 重置统计
        cache_stats_collector.reset_stats()

        # 执行一些缓存操作
        await enhanced_cache.set("key1", "value1", ttl=60)
        await enhanced_cache.get("key1")
        await enhanced_cache.get("non_existent")
        await enhanced_cache.delete("key1")

        # 获取统计信息
        stats = cache_stats_collector.get_cache_efficiency()

        assert stats["total_requests"] > 0
        assert stats["cache_hits"] >= 1
        assert stats["cache_misses"] >= 1
        assert "hit_rate" in stats

        # 获取性能指标
        performance = cache_stats_collector.get_performance_metrics()
        assert "avg_response_time" in performance
        assert "total_operations" in performance

    async def test_cache_bulk_operations(self):
        """测试缓存批量操作"""
        # 准备批量数据
        bulk_data = {}
        for i in range(100):
            bulk_data[f"bulk_key_{i}"] = f"bulk_value_{i}"

        # 批量设置
        await enhanced_cache.set_many(bulk_data, ttl=300)

        # 批量获取
        keys = list(bulk_data.keys())
        cached_values = await enhanced_cache.get_many(keys)

        assert len(cached_values) == len(bulk_data)
        for key, expected_value in bulk_data.items():
            assert cached_values[key] == expected_value

        # 批量删除
        await enhanced_cache.delete_many(keys)

        # 验证删除
        cached_values = await enhanced_cache.get_many(keys)
        assert all(value is None for value in cached_values.values())

    async def test_cache_tag_operations(self):
        """测试缓存标签操作"""
        # 设置带标签的缓存
        await enhanced_cache.set("user:1", {"id": 1, "name": "User 1"}, tags=["users", "active"])
        await enhanced_cache.set("user:2", {"id": 2, "name": "User 2"}, tags=["users", "active"])
        await enhanced_cache.set("user:3", {"id": 3, "name": "User 3"}, tags=["users", "inactive"])

        # 按标签删除
        await enhanced_cache.delete_by_tag("inactive")

        # 验证删除
        assert await enhanced_cache.get("user:1") is not None
        assert await enhanced_cache.get("user:2") is not None
        assert await enhanced_cache.get("user:3") is None

    async def test_cache_memory_management(self):
        """测试缓存内存管理"""
        # 设置大量数据
        large_data = {}
        for i in range(1000):
            large_data[f"memory_test_{i}"] = {
                "id": i,
                "data": "x" * 1000,  # 1KB数据
                "metadata": {"created": datetime.now().isoformat()},
            }

        # 分批缓存
        batch_size = 100
        for i in range(0, len(large_data), batch_size):
            batch = dict(list(large_data.items())[i : i + batch_size])
            await enhanced_cache.set_many(batch, ttl=60)

        # 检查内存使用情况
        memory_stats = await enhanced_cache.get_memory_stats()
        assert "used_memory" in memory_stats
        assert "total_memory" in memory_stats

        # 清理过期缓存
        await enhanced_cache.cleanup_expired()

    async def test_cache_error_handling(self):
        """测试缓存错误处理"""
        # 测试无效操作
        with pytest.raises(CacheException):
            await enhanced_cache.set("", "value")  # 空键

        with pytest.raises(CacheException):
            await enhanced_cache.set("key", None)  # None值

        # 测试超大值
        large_value = "x" * (1024 * 1024 * 10)  # 10MB
        with pytest.raises(CacheException):
            await enhanced_cache.set("large_key", large_value)

    async def test_cache_concurrent_access(self):
        """测试缓存并发访问"""
        key = "concurrent_test"
        results = []

        async def access_cache(value: str):
            await enhanced_cache.set(key, value, ttl=10)
            cached = await enhanced_cache.get(key)
            results.append(cached)

        # 并发访问
        tasks = []
        for i in range(50):
            tasks.append(access_cache(f"value_{i}"))

        await asyncio.gather(*tasks)

        # 所有结果应该一致（最后的写入获胜）
        assert len(set(results)) == 1
        assert all(result == results[0] for result in results)

    async def test_cache_performance_under_load(self):
        """测试缓存负载下的性能"""
        import time

        # 准备测试数据
        test_keys = [f"perf_test_{i}" for i in range(1000)]
        test_values = [f"value_{i}" for i in range(1000)]

        # 批量设置
        start_time = time.time()
        data = dict(zip(test_keys, test_values, strict=False))
        await enhanced_cache.set_many(data, ttl=300)
        set_time = time.time() - start_time

        # 批量获取
        start_time = time.time()
        results = await enhanced_cache.get_many(test_keys)
        get_time = time.time() - start_time

        # 性能验证
        assert set_time < 5.0  # 5秒内完成设置
        assert get_time < 2.0  # 2秒内完成获取
        assert len(results) == 1000

        # 验证统计数据
        stats = cache_stats_collector.get_performance_metrics()
        assert stats["avg_response_time"] < 0.1  # 平均响应时间小于100ms
