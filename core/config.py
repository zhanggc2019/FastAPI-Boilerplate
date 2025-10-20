from enum import Enum
from pathlib import Path

from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录
BASE_PATH = Path(__file__).resolve().parent.parent


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

    DEBUG: int = 0
    DEFAULT_LOCALE: str = "zh_CN"
    # 时间配置
    DATETIME_TIMEZONE: str = "Asia/Shanghai"
    DATETIME_FORMAT: str = "%Y-%m-%d %H:%M:%S"

    ENVIRONMENT: str = EnvironmentType.DEVELOPMENT
    POSTGRES_URL: PostgresDsn = Field(
        default=PostgresDsn("postgresql+asyncpg://user:password@127.0.0.1:5432/db-name"),
        validation_alias="POSTGRES_URL",
    )
    # 注释掉原来的 REDIS_URL 行
    # REDIS_URL: RedisDsn = Field(default=RedisDsn("redis://localhost:6379/7"), validation_alias="REDIS_URL")
    RELEASE_VERSION: str = "0.1"
    SHOW_SQL_ALCHEMY_QUERIES: int = 0
    DATABASE_POOL_ECHO: int = 0
    SECRET_KEY: str = "super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    # .env Redis
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_PASSWORD: str
    REDIS_DATABASE: int

    # .env RabbitMQ/Celery
    RABBITMQ_HOST: str = "localhost"
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str = "rabbit"
    RABBITMQ_PASSWORD: str = "password"
    RABBITMQ_VHOST: str = "/"

    # Redis
    REDIS_TIMEOUT: int = 5

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
