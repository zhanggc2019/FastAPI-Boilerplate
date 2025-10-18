from fastapi import APIRouter, Request
from loguru import logger

test_router = APIRouter()


@test_router.get("/rate-limit-test", summary="限流测试接口", description="测试接口功能（限流功能暂时禁用）")
async def rate_limit_test(request: Request):
    """
    限流测试接口（简化版）

    - 记录请求日志信息
    - 返回测试数据
    """
    # 记录访问日志
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")

    # 使用loguru记录详细日志
    logger.info(f"测试接口被访问 - IP: {client_ip}, User-Agent: {user_agent}")

    # 使用loguru记录详细日志
    logger.info(f"限流测试接口调用 - IP: {client_ip}, Path: {request.url.path}, Method: {request.method}")

    return {
        "message": "测试接口调用成功（限流功能暂时禁用）",
        "timestamp": "2025-10-17 14:00:00",
        "data": {"test_field": "这是一个测试数据", "rate_limit": "限流功能暂时禁用", "current_ip": client_ip},
        "status": "success",
    }


@test_router.get("/unlimited-test", summary="无限制测试接口", description="无限制的测试接口，用于对比测试")
async def unlimited_test(request: Request):
    """
    无限制测试接口

    - 无速率限制
    - 记录访问日志
    - 返回测试数据
    """
    # 记录访问日志
    client_ip = request.client.host if request.client else "unknown"

    logger.info(f"无限制测试接口被访问 - IP: {client_ip}")
    logger.info(f"无限制测试接口调用 - IP: {client_ip}")

    return {
        "message": "无限制测试接口调用成功",
        "timestamp": "2025-10-17 14:00:00",
        "data": {"test_field": "这是一个无限制测试数据", "current_ip": client_ip},
        "status": "success",
    }
