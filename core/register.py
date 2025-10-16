from asyncio import create_task
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi_limiter import FastAPILimiter
from fastapi_pagination import add_pagination
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from core.cache import Cache, CustomKeyMaker, RedisBackend
from core.config import config as settings
from core.database.redis import redis_client
from core.database.session import create_tables
from core.exceptions import CustomException
from core.fastapi.middlewares import (
    AuthBackend,
    AuthenticationMiddleware,
    ResponseLoggerMiddleware,
    SQLAlchemyMiddleware,
)
from core.fastapi.middlewares.access_middleware import AccessMiddleware
from core.fastapi.middlewares.opera_log_middleware import OperaLogMiddleware
from core.log import set_custom_logfile, setup_logging
from core.utils.health_check import ensure_unique_route_names, http_limit_callback


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
    await redis_client.open()

    # 初始化 limiter
    await FastAPILimiter.init(
        redis=redis_client,
        prefix=settings.REQUEST_LIMITER_REDIS_PREFIX,
        http_callback=http_limit_callback,
    )

    # 创建操作日志任务
    create_task(OperaLogMiddleware.consumer())

    yield

    # 关闭 redis 连接
    await redis_client.aclose()


def init_listeners(app_: FastAPI) -> None:
    @app_.exception_handler(CustomException)
    async def custom_exception_handler(request: Request, exc: CustomException):
        return JSONResponse(
            status_code=exc.code,
            content={"error_code": exc.error_code, "message": exc.message},
        )


def on_auth_error(request: Request, exc: Exception):
    status_code, error_code, message = 401, None, str(exc)
    if isinstance(exc, CustomException):
        status_code = int(exc.code)
        error_code = exc.error_code
        message = exc.message

    return JSONResponse(
        status_code=status_code,
        content={"error_code": error_code, "message": message},
    )


def init_cache() -> None:
    "暂时没用"
    Cache.init(backend=RedisBackend(), key_maker=CustomKeyMaker())


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

    :param app: FastAPI 应用实例
    :return:
    """
    if settings.MIDDLEWARE_CORS:
        (
            app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            ),
        )
    # Opera log
    app.add_middleware(OperaLogMiddleware)
    # JWT auth
    app.add_middleware(
        AuthenticationMiddleware,
        backend=AuthBackend(),
        on_error=on_auth_error,
    )
    app.add_middleware(SQLAlchemyMiddleware)
    # Access log
    # app.add_middleware(AccessMiddleware)  # Disabled as it causes issues with /docs

    app.add_middleware(ResponseLoggerMiddleware)  # Re-enabled since it's not the issue

    # Trace ID
    app.add_middleware(CorrelationIdMiddleware, validator=False)


def register_router(app: FastAPI) -> None:
    """
    注册路由

    :param app: FastAPI 应用实例
    :return:
    """
    from api import router

    app.include_router(router)
    # Extra
    ensure_unique_route_names(app)


def register_page(app: FastAPI) -> None:
    """
    注册分页查询功能

    :param app: FastAPI 应用实例
    :return:
    """
    add_pagination(app)
