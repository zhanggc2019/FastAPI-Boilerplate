import time
from datetime import datetime

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from core.common.context import ctx
from core.log import logger
from core.utils.request_parse import parse_ip_info, parse_user_agent_info


class AccessMiddleware(BaseHTTPMiddleware):
    """访问日志中间件"""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """
        处理请求并记录访问日志

        :param request: FastAPI 请求对象
        :param call_next: 下一个中间件或路由处理函数
        :return:
        """
        path = request.url.path if not request.url.query else request.url.path + "/" + request.url.query

        if request.method != "OPTIONS":
            logger.debug(f"--> 请求开始[{path}]")

        perf_time = time.perf_counter()
        ctx.perf_time = perf_time

        start_time = datetime.now()
        ctx.start_time = start_time

        response = await call_next(request)

        elapsed = (time.perf_counter() - perf_time) * 1000

        ip = await parse_ip_info(request)
        ctx.ip = ip

        ua_info = parse_user_agent_info(request)
        ctx.user_agent = ua_info.user_agent
        ctx.os = ua_info.os
        ctx.browser = ua_info.browser
        ctx.device = ua_info.device

        if request.method != "OPTIONS":
            logger.debug("<-- 请求结束")

            client_host = getattr(request.client, "host", "unknown") if request.client else "unknown"
            logger.info(
                f"{client_host: <15} | {request.method: <8} | {response.status_code: <6} | {path} | {elapsed:.3f}ms",
            )

        return response
