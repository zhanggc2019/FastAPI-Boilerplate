from enum import Enum
from pathlib import Path

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录
BASE_PATH = Path(__file__).resolve().parent.parent
print(f"项目根目录: {BASE_PATH}")


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    # FastAPI
    FASTAPI_API_V1_PATH: str = "/api/v1"
    FASTAPI_TITLE: str = "FastAPI Best Boilerplate"
    FASTAPI_DESCRIPTION: str = "FastAPI 脚手架"
    FASTAPI_DOCS_URL: str = "/docs"
    FASTAPI_REDOC_URL: str = "/redoc"
    FASTAPI_OPENAPI_URL: str | None = "/openapi"
    FASTAPI_STATIC_FILES: bool = True

    # API versioning
    API_VERSION_HEADER: str = "X-API-Version"
    API_CURRENT_VERSION: str = "v1"
    API_SUPPORTED_VERSIONS: list[str] = ["v1"]

    MIDDLEWARE_CORS: bool = True

    # 日志文件路径
    LOG_DIR: Path = BASE_PATH / "logs"
    if not LOG_DIR.exists():
        LOG_DIR.mkdir(parents=True)
    LOG_STD_LEVEL: str = "INFO"
    TRACE_ID_REQUEST_HEADER_KEY: str = "X-Request-ID"
    TRACE_ID_LOG_LENGTH: int = 32  # UUID 长度，必须小于等于 32
    TRACE_ID_LOG_DEFAULT_VALUE: str = "-"
    # 日志（文件）
    LOG_FILE_ACCESS_LEVEL: str = "INFO"
    LOG_FILE_ERROR_LEVEL: str = "ERROR"
    LOG_ACCESS_FILENAME: str = "access.log"
    LOG_ERROR_FILENAME: str = "error.log"
    # 日志
    LOG_FORMAT: str = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</> | <lvl>{level: <8}</> | <cyan>{correlation_id}</> | <lvl>{message}</>"
    )

    # 静态资源目录
    STATIC_DIR: Path = BASE_PATH / "static"
    DEFAULT_LOCALE: str = "zh_CN"
    # 时间配置
    DATETIME_TIMEZONE: str = "Asia/Shanghai"
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    ENVIRONMENT: str = EnvironmentType.DEVELOPMENT
    POSTGRES_URL: PostgresDsn = Field(
        default=PostgresDsn("postgresql+asyncpg://user:password@127.0.0.1:5432/db-name"),
        validation_alias="POSTGRES_URL",
    )
    RELEASE_VERSION: str = "0.1"
    SHOW_SQL_ALCHEMY_QUERIES: int = 0
    DATABASE_POOL_ECHO: int = 0

    # 数据库连接池配置 - 基于环境动态调整
    DATABASE_POOL_SIZE: int = Field(default=10, validation_alias="DATABASE_POOL_SIZE")
    DATABASE_MAX_OVERFLOW: int = Field(default=20, validation_alias="DATABASE_MAX_OVERFLOW")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, validation_alias="DATABASE_POOL_TIMEOUT")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, validation_alias="DATABASE_POOL_RECYCLE")
    DATABASE_POOL_PRE_PING: bool = Field(default=True, validation_alias="DATABASE_POOL_PRE_PING")
    DATABASE_POOL_USE_LIFO: bool = Field(default=False, validation_alias="DATABASE_POOL_USE_LIFO")

    @property
    def database_pool_config(self) -> dict:
        """根据环境返回优化的数据库连接池配置"""
        if self.ENVIRONMENT == EnvironmentType.PRODUCTION:
            return {
                "pool_size": max(self.DATABASE_POOL_SIZE, 20),  # 生产环境最小20
                "max_overflow": max(self.DATABASE_MAX_OVERFLOW, 40),  # 生产环境最小40
                "pool_timeout": max(self.DATABASE_POOL_TIMEOUT, 60),  # 生产环境最小60秒
                "pool_recycle": min(self.DATABASE_POOL_RECYCLE, 3600),  # 生产环境最大1小时
                "pool_pre_ping": True,  # 生产环境必须启用
                "pool_use_lifo": True,  # 生产环境启用LIFO
            }
        elif self.ENVIRONMENT == EnvironmentType.TEST:
            return {
                "pool_size": min(self.DATABASE_POOL_SIZE, 5),  # 测试环境最大5
                "max_overflow": min(self.DATABASE_MAX_OVERFLOW, 10),  # 测试环境最大10
                "pool_timeout": min(self.DATABASE_POOL_TIMEOUT, 10),  # 测试环境最大10秒
                "pool_recycle": self.DATABASE_POOL_RECYCLE,
                "pool_pre_ping": self.DATABASE_POOL_PRE_PING,
                "pool_use_lifo": False,  # 测试环境禁用LIFO
            }
        else:  # DEVELOPMENT
            return {
                "pool_size": self.DATABASE_POOL_SIZE,
                "max_overflow": self.DATABASE_MAX_OVERFLOW,
                "pool_timeout": self.DATABASE_POOL_TIMEOUT,
                "pool_recycle": self.DATABASE_POOL_RECYCLE,
                "pool_pre_ping": self.DATABASE_POOL_PRE_PING,
                "pool_use_lifo": self.DATABASE_POOL_USE_LIFO,
            }
    # jwt 配置 - 强制从环境变量读取，移除硬编码默认值
    SECRET_KEY: str = Field("change-me")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    # .env Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_DATABASE: int
    REDIS_TIMEOUT: int = 5

    # .env RabbitMQ/Celery
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "rabbit"
    RABBITMQ_PASSWORD: str = "password"
    RABBITMQ_VHOST: str = "/"

    # 请求限制配置
    REQUEST_LIMITER_REDIS_PREFIX: str = "fastapi:limiter"

    # OAuth settings
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/v1/users/oauth/google/callback"

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""
    GITHUB_REDIRECT_URI: str = "http://localhost:8000/v1/users/oauth/github/callback"

    # WeChat OAuth settings
    WECHAT_APP_ID: str = ""
    WECHAT_APP_SECRET: str = ""
    WECHAT_REDIRECT_URI: str = "http://localhost:8000/v1/users/oauth/wechat/callback"

    # Alipay OAuth settings
    ALIPAY_APP_ID: str = ""
    ALIPAY_PRIVATE_KEY: str = ""
    ALIPAY_PUBLIC_KEY: str = ""
    ALIPAY_REDIRECT_URI: str = "http://localhost:8000/v1/users/oauth/alipay/callback"

    OPERA_LOG_ENCRYPT_KEY_INCLUDE: list[str] = [  # 将加密接口入参参数对应的值
        "password",
        "old_password",
        "new_password",
        "confirm_password",
    ]

    # 操作日志
    OPERA_LOG_PATH_EXCLUDE: list[str] = [
        "/favicon.ico",
        "/docs",
        "/redoc",
        "/openapi",
    ]

    @property
    def postgres_url_str(self) -> str:
        return str(self.POSTGRES_URL)

    @property
    def redis_url_str(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"

    @property
    def celery_broker_url(self) -> str:
        if self.RABBITMQ_PASSWORD:
            return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"
        return f"amqp://{self.RABBITMQ_USER}@{self.RABBITMQ_HOST}:{self.RABBITMQ_PORT}/{self.RABBITMQ_VHOST}"

    @property
    def celery_backend_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"


config: Config = Config()
# Backwards compatibility alias for legacy imports
settings: Config = config
