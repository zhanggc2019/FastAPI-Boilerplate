from asyncio import create_task
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import ORJSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from app.core.cache import Cache, CustomKeyMaker, RedisBackend
from app.core.cache.redis_backend import redis_backend
from app.core.config import config as settings
from app.db.session import create_tables
from app.core.exceptions import CustomException, create_exception_handlers
from app.core.middlewares import (
    AuthBackend,
    AuthenticationMiddleware,
    ResponseLoggerMiddleware,
    SQLAlchemyMiddleware,
)
from app.core.middlewares.access_middleware import AccessMiddleware
from app.core.middlewares.opera_log_middleware import OperaLogMiddleware
from app.core.logging import set_custom_logfile, setup_logging
from app.core.utils.health_check import ensure_unique_route_names, http_limit_callback


@asynccontextmanager
async def register_init(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    启动初始化

    :param app: FastAPI 应用实例
    :return:
    """
    # 创建数据库表
    try:
        await create_tables()
        print("数据库表创建成功")
    except Exception as e:
        print(f"创建数据库表时出错: {e}")

    # 初始化 redis
    await redis_backend.open()

    # 初始化缓存
    Cache.init(backend=RedisBackend, key_maker=CustomKeyMaker)

    # 初始化 limiter（暂时禁用）
    try:
        await FastAPILimiter.init(
            redis=redis_backend.redis,
            prefix=settings.REQUEST_LIMITER_REDIS_PREFIX,
            http_callback=http_limit_callback,
        )
        print("FastAPI Limiter 初始化成功")
    except Exception as e:
        print(f"FastAPI Limiter 初始化失败: {e}")

    # 创建操作日志任务
    create_task(OperaLogMiddleware.consumer())

    yield

    # 关闭 redis 连接
    await redis_backend.aclose()


def init_listeners(app_: FastAPI) -> None:
    # 使用统一的异常处理器
    exception_handlers = create_exception_handlers()

    for exc_class, handler_func in exception_handlers.items():
        def create_handler(exc_class=exc_class, handler_func=handler_func):
            @app_.exception_handler(exc_class)
            async def exception_handler_wrapper(request: Request, exc: Exception):
                return await handler_func(request, exc)
            return exception_handler_wrapper
        create_handler()


def on_auth_error(request: Request, exc: Exception):
    """
    认证错误处理函数

    :param request: FastAPI 请求对象
    :param exc: 异常对象
    :return: JSON响应
    """
    status_code, error_code, message = 401, None, str(exc)
    if isinstance(exc, CustomException):
        status_code = int(exc.code)
        error_code = exc.error_code
        message = exc.message

    return ORJSONResponse(
        status_code=status_code,
        content={"error_code": error_code, "message": message},
    )


def register_app() -> FastAPI:
    """注册 FastAPI 应用"""

    app = FastAPI(
        title=settings.FASTAPI_TITLE,
        version=settings.RELEASE_VERSION,
        description=settings.FASTAPI_DESCRIPTION,
        docs_url=settings.FASTAPI_DOCS_URL,
        redoc_url=settings.FASTAPI_REDOC_URL,
        openapi_url=settings.FASTAPI_OPENAPI_URL,
        lifespan=register_init,
        default_response_class=ORJSONResponse
    )

    # 注册组件
    register_logger()
    register_static_file(app)
    register_middleware(app)
    register_router(app)
    init_listeners(app)
    register_page(app)

    return app


def register_logger() -> None:
    """注册日志"""
    setup_logging()
    set_custom_logfile()


def register_static_file(app: FastAPI) -> None:
    """
    注册静态资源服务

    :param app: FastAPI 应用实例
    :return:
    """
    # 固有静态资源
    if settings.FASTAPI_STATIC_FILES:
        if not settings.STATIC_DIR.exists():  # noqa
            settings.STATIC_DIR.mkdir(parents=True, exist_ok=True)
        app.mount("/static", StaticFiles(directory=settings.STATIC_DIR), name="static")


def register_middleware(app: FastAPI) -> None:
    """
    注册中间件（执行顺序从下往上）

    中间件执行顺序（从外到内）：
    1. CorrelationIdMiddleware - 最外层，为每个请求生成追踪ID
    2. CORSMiddleware - 处理跨域请求，应该在最外层
    3. ResponseLoggerMiddleware - 记录响应日志
    4. AccessMiddleware - 访问日志，记录所有访问尝试（包括未认证的请求）
    5. OperaLogMiddleware - 操作日志，在认证之后记录用户操作
    6. AuthenticationMiddleware - JWT认证
    7. SQLAlchemyMiddleware - 数据库会话管理，最内层

    :param app: FastAPI 应用实例
    :return:
    """
    # 1. 数据库会话中间件 - 最内层，确保每个请求都有独立的数据库会话
    app.add_middleware(SQLAlchemyMiddleware)

    # 2. JWT认证中间件 - 在数据库会话之后，因为认证可能需要查询数据库
    app.add_middleware(
        AuthenticationMiddleware,
        backend=AuthBackend(),
        on_error=on_auth_error,
    )

    # 3. 操作日志中间件 - 在认证之后，因为需要获取用户信息记录操作日志
    app.add_middleware(OperaLogMiddleware)

    # 4. 访问日志中间件 - 在认证之前，记录所有访问尝试（包括未认证的请求）
    # 这样可以追踪所有访问行为，包括失败的认证尝试
    app.add_middleware(AccessMiddleware)

    # 5. 响应日志中间件 - 记录响应信息
    app.add_middleware(ResponseLoggerMiddleware)

    # 6. CORS中间件 - 应该在外层，处理跨域请求
    if settings.MIDDLEWARE_CORS:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    # 7. 追踪ID中间件 - 最外层，为每个请求生成唯一的追踪ID
    app.add_middleware(CorrelationIdMiddleware, validator=False)


def register_router(app: FastAPI) -> None:
    """
    注册路由

    :param app: FastAPI 应用实例
    :return:
    """
    from app.api import router

    app.include_router(router)
    # Extra
    ensure_unique_route_names(app)


def register_page(app: FastAPI) -> None:
    """
    注册分页查询功能

    :param app: FastAPI 应用实例
    :return:
    """
    from fastapi import Request
    from fastapi.responses import HTMLResponse

    # 登录页面路由
    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request):
        """登录页面"""
        from pathlib import Path
        login_page_path = settings.STATIC_DIR / "login" / "index.html"
        if login_page_path.exists():
            with open(login_page_path, "r", encoding="utf-8") as f:
                return f.read()
        return HTMLResponse("<h1>Login page not found</h1>", status_code=404)

    add_pagination(app)
