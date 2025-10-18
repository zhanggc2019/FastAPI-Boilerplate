#!/usr/bin/env python3
"""
调试用简化应用
"""

from fastapi import FastAPI, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
from core.database.redis import redis_client
from core.config import config as settings
from fastapi import Depends

app = FastAPI()

@app.on_event("startup")
async def startup():
    """初始化"""
    await redis_client.open()
    await FastAPILimiter.init(
        redis=redis_client,
        prefix=settings.REQUEST_LIMITER_REDIS_PREFIX,
    )
    print("调试应用启动成功")

@app.get("/simple")
async def simple():
    """简单端点"""
    return {"message": "简单测试成功"}

@app.get("/rate-limit-test", dependencies=[Depends(RateLimiter(times=5, seconds=60))])
async def rate_limit_test(request: Request):
    """限流测试端点（使用限流器）"""
    client_ip = request.client.host if request.client else "unknown"
    return {"message": "限流测试端点", "ip": client_ip}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)