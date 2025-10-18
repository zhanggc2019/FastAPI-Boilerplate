#!/usr/bin/env python3
"""
测试中间件问题的简化应用
"""

from fastapi import FastAPI, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from core.database.redis import redis_client
from core.config import config as settings
from fastapi import Depends
from starlette.middleware.base import BaseHTTPMiddleware

app = FastAPI()

class TestOperaLogMiddleware(BaseHTTPMiddleware):
    """测试用的简化操作日志中间件"""

    async def dispatch(self, request, call_next):
        """模拟操作日志中间件的问题"""
        response = await call_next(request)

        # 这里模拟问题 - 试图访问不存在的 user 属性
        try:
            username = request.user.username  # 这里可能出错
        except AttributeError:
            username = None  # 正确处理应该是这样

        return response

@app.on_event("startup")
async def startup():
    """初始化"""
    await redis_client.open()
    await FastAPILimiter.init(
        redis=redis_client,
        prefix=settings.REQUEST_LIMITER_REDIS_PREFIX,
    )
    print("测试中间件应用启动成功")

@app.get("/simple")
async def simple():
    """简单端点"""
    return {"message": "简单测试成功"}

@app.get("/rate-limit-test", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def rate_limit_test(request: Request):
    """限流测试端点"""
    client_ip = request.client.host if request.client else "unknown"
    return {"message": "限流测试端点", "ip": client_ip}

# 添加有问题的中间件
app.add_middleware(TestOperaLogMiddleware)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8002)