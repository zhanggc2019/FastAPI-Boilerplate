import asyncio
import json
import logging
import random
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api import router as api_router
from app.core.cache import enhanced_cache, cache_warmer, cache_monitor
from app.core.cache.redis_backend import redis_backend
from app.core.config import config
from app.db.session import Base, create_async_engine_and_session
from app.core.exceptions import (
    ResourceNotFoundException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    DataValidationException,
    InternalServerException,
    ServiceUnavailableException,
)
from tests.enhanced_test_data import test_data_manager, generate_test_user, generate_test_task

async_engine, async_session_factory = create_async_engine_and_session(config.postgres_url_str)
async_session = async_session_factory
redis_client = redis_backend.redis


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 全局测试配置
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_environment():
    """设置测试环境"""
    logger.info("Setting up test environment...")

    # 清理Redis缓存
    try:
        await redis_client.flushdb()
        logger.info("Redis cache flushed")
    except Exception as e:
        logger.warning(f"Failed to flush Redis: {e}")

    # 清理缓存监控器状态
    cache_monitor.reset_stats()

    yield

    # 清理工作
    logger.info("Tearing down test environment...")
    await redis_client.close()
    await enhanced_cache.close()


@pytest.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """创建数据库会话"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        yield session
        await session.rollback()

    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture(scope="function")
async def test_app() -> FastAPI:
    """创建测试应用实例"""
    test_app = FastAPI(title="Test App", version="1.0.0")
    test_app.include_router(api_router)
    return test_app


@pytest.fixture(scope="function")
async def async_client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """创建异步HTTP客户端"""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture(scope="function")
async def authenticated_client(async_client: AsyncClient, test_user: Dict[str, Any]) -> AsyncClient:
    """创建已认证的客户端"""
    # 模拟登录获取token
    login_data = {
        "email": test_user["email"],
        "password": "testpassword123",  # 假设这是测试用户的密码
    }

    response = await async_client.post("/api/v1/auth/login", json=login_data)
    if response.status_code == 200:
        token_data = response.json()
        async_client.headers.update({"Authorization": f"Bearer {token_data.get('access_token', 'test_token')}"})

    return async_client


# 测试数据fixture
@pytest.fixture(scope="function")
async def test_user() -> Dict[str, Any]:
    """创建测试用户"""
    user_data = generate_test_user()
    user_data["password"] = "testpassword123"  # 设置固定密码用于测试
    return await test_data_manager.create_test_user(**user_data)


@pytest.fixture(scope="function")
async def test_users() -> List[Dict[str, Any]]:
    """创建多个测试用户"""
    users = []
    for i in range(5):
        user_data = generate_test_user(username=f"testuser_{i}", email=f"test{i}@example.com")
        user_data["password"] = f"testpassword{i}"
        user = await test_data_manager.create_test_user(**user_data)
        users.append(user)
    return users


@pytest.fixture(scope="function")
async def test_task(test_user: Dict[str, Any]) -> Dict[str, Any]:
    """创建测试任务"""
    task_data = generate_test_task(author_id=test_user.get("id", 1))
    return await test_data_manager.create_test_task(author_id=test_user.get("id", 1), **task_data)


@pytest.fixture(scope="function")
async def test_tasks(test_user: Dict[str, Any]) -> List[Dict[str, Any]]:
    """创建多个测试任务"""
    tasks = []
    for i in range(10):
        task_data = generate_test_task(
            author_id=test_user.get("id", 1),
            title=f"Test Task {i}",
            status=random.choice(["pending", "in_progress", "completed"]),
        )
        task = await test_data_manager.create_test_task(author_id=test_user.get("id", 1), **task_data)
        tasks.append(task)
    return tasks


@pytest.fixture(scope="function")
async def test_data_set() -> Dict[str, List[Dict[str, Any]]]:
    """创建完整的测试数据集"""
    return await test_data_manager.create_test_data_set(users=3, tasks_per_user=5)


# 缓存相关fixture
@pytest.fixture(scope="function")
async def cache_enabled():
    """启用缓存的测试环境"""
    original_enabled = enhanced_cache.enabled
    enhanced_cache.enabled = True
    yield
    enhanced_cache.enabled = original_enabled


@pytest.fixture(scope="function")
async def cache_disabled():
    """禁用缓存的测试环境"""
    original_enabled = enhanced_cache.enabled
    enhanced_cache.enabled = False
    yield
    enhanced_cache.enabled = original_enabled


@pytest.fixture(scope="function")
async def warmed_cache():
    """预热缓存"""
    # 添加一些预热任务
    warmup_tasks = [
        {"key": "user_profile_1", "data": {"id": 1, "name": "Test User", "email": "test@example.com"}, "ttl": 3600},
        {"key": "task_list_page_1", "data": [{"id": i, "title": f"Task {i}"} for i in range(1, 6)], "ttl": 1800},
    ]

    for task in warmup_tasks:
        await cache_warmer.add_warmup_task(task["key"], lambda d=task["data"]: d, ttl=task["ttl"])

    await cache_warmer.execute_warmup()
    yield

    # 清理预热数据
    for task in warmup_tasks:
        await enhanced_cache.delete(task["key"])


# 异常相关fixture
@pytest.fixture(scope="function")
def custom_exceptions():
    """提供各种异常实例用于测试"""
    return {
        "not_found": ResourceNotFoundException("Test resource not found"),
        "bad_request": BadRequestException("Bad request test"),
        "unauthorized": UnauthorizedException("Unauthorized test"),
        "forbidden": ForbiddenException("Forbidden test"),
        "conflict": ConflictException("Conflict test"),
        "validation": DataValidationException("Validation failed", field="test_field"),
        "server_error": InternalServerException("Server error test"),
        "service_unavailable": ServiceUnavailableException("Service unavailable"),
    }


# Mock fixture
@pytest.fixture(scope="function")
def mock_redis_client():
    """Mock Redis客户端"""
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=None)
    mock_client.set = AsyncMock(return_value=True)
    mock_client.delete = AsyncMock(return_value=1)
    mock_client.flushdb = AsyncMock(return_value=True)
    mock_client.close = AsyncMock(return_value=None)
    return mock_client


@pytest.fixture(scope="function")
def mock_external_api():
    """Mock外部API"""
    mock_api = AsyncMock()
    mock_api.get = AsyncMock(return_value={"status": "success", "data": {"id": 123, "name": "External Data"}})
    mock_api.post = AsyncMock(return_value={"status": "created", "data": {"id": 456}})
    return mock_api


# 性能测试fixture
@pytest.fixture(scope="function")
def performance_monitor():
    """性能监控器"""
    stats = {"requests": [], "errors": [], "start_time": datetime.now()}

    class PerformanceMonitor:
        def record_request(self, endpoint: str, duration: float, status_code: int):
            stats["requests"].append(
                {"endpoint": endpoint, "duration": duration, "status_code": status_code, "timestamp": datetime.now()}
            )

        def record_error(self, error: Exception, endpoint: str):
            stats["errors"].append({"error": str(error), "endpoint": endpoint, "timestamp": datetime.now()})

        def get_stats(self):
            total_requests = len(stats["requests"])
            total_errors = len(stats["errors"])

            if total_requests == 0:
                return {"error_rate": 0, "avg_duration": 0}

            durations = [r["duration"] for r in stats["requests"]]
            avg_duration = sum(durations) / len(durations)
            error_rate = total_errors / total_requests

            return {
                "total_requests": total_requests,
                "total_errors": total_errors,
                "error_rate": error_rate,
                "avg_duration": avg_duration,
                "max_duration": max(durations) if durations else 0,
                "min_duration": min(durations) if durations else 0,
            }

    monitor = PerformanceMonitor()
    yield monitor

    # 打印性能统计
    final_stats = monitor.get_stats()
    logger.info(f"Performance Stats: {json.dumps(final_stats, indent=2, default=str)}")


# 清理fixture
@pytest.fixture(scope="function", autouse=True)
async def cleanup_test_data():
    """在每个测试后清理测试数据"""
    yield
    test_data_manager.cleanup_data()

    # 清理缓存
    try:
        await redis_client.flushdb()
    except Exception as e:
        logger.warning(f"Failed to cleanup Redis: {e}")


# 辅助函数
def assert_api_response(response, expected_status: int = 200, expected_success: bool = True):
    """断言API响应"""
    assert response.status_code == expected_status

    if response.headers.get("content-type", "").startswith("application/json"):
        data = response.json()

        if expected_success:
            assert data.get("success") is True
        else:
            assert data.get("success") is False

        assert "message" in data
        assert "timestamp" in data


def assert_pagination_response(response, expected_items: int = None):
    """断言分页响应"""
    data = response.json()

    assert "data" in data
    assert "pagination" in data

    pagination = data["pagination"]
    assert "total" in pagination
    assert "page" in pagination
    assert "per_page" in pagination
    assert "total_pages" in pagination
    assert "has_next" in pagination
    assert "has_prev" in pagination

    if expected_items is not None:
        assert len(data["data"]) == expected_items


def assert_cache_hit(cache_key: str, should_exist: bool = True):
    """断言缓存命中"""
    # 这里可以集成实际的缓存检查逻辑
    pass


# 导出主要fixture
__all__ = [
    "event_loop",
    "db_session",
    "test_app",
    "async_client",
    "authenticated_client",
    "test_user",
    "test_users",
    "test_task",
    "test_tasks",
    "test_data_set",
    "cache_enabled",
    "cache_disabled",
    "warmed_cache",
    "custom_exceptions",
    "mock_redis_client",
    "mock_external_api",
    "performance_monitor",
    "cleanup_test_data",
    "assert_api_response",
    "assert_pagination_response",
    "assert_cache_hit",
]
