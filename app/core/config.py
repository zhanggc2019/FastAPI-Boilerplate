import os
from enum import Enum
from pathlib import Path

import yaml
from pydantic import Field, PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict

# 项目根目录 (app/core/config.py -> parent.parent = 项目根目录)
# 实际: app/core/config.py -> parent = app -> parent = 项目根目录 -> parent = 真正的项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BASE_PATH = PROJECT_ROOT
CONFIG_FILE = os.environ.get("CONFIG_FILE", str(PROJECT_ROOT / "config.yaml"))


def _load_yaml_config() -> dict:
    """加载 YAML 配置文件"""
    config_path = Path(CONFIG_FILE)
    if config_path.exists():
        with open(config_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


# 加载 YAML 配置
_yaml_config = _load_yaml_config()

# 将嵌套的 YAML 配置展平为环境变量格式
def _flatten_dict(d: dict, parent_key: str = "", sep: str = "_") -> dict:
    """将嵌套字典展平为单层字典，键使用下划线连接"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key.upper(), v))
    return dict(items)


_flat_yaml_config = _flatten_dict(_yaml_config) if _yaml_config else {}
print(f"项目根目录: {BASE_PATH}")
if _flat_yaml_config:
    print(f"已加载配置文件: {CONFIG_FILE}")


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class Config(BaseSettings):
    """配置类，优先级: 环境变量 > YAML 配置 > 默认值"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    def __init__(self, **kwargs):
        # 先用 YAML 配置初始化
        if _flat_yaml_config:
            # 将 YAML 配置转换为 pydantic 需要的格式
            for key, value in _flat_yaml_config.items():
                # 跳过已经通过环境变量设置的值
                if key not in os.environ:
                    kwargs.setdefault(key, value)
        super().__init__(**kwargs)

    # Server
    SERVER_HOST: str = Field(default="localhost", validation_alias="SERVER_HOST")
    SERVER_PORT: int = Field(default=8000, validation_alias="SERVER_PORT")

    # FastAPI
    FASTAPI_API_V1_PATH: str = "/api/v1"
    FASTAPI_TITLE: str = "Knowledge Assistant"
    FASTAPI_DESCRIPTION: str = "Knowledge Base Assistant"
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
        validation_alias="DATABASE_URL",
    )
    TEST_POSTGRES_URL: PostgresDsn | None = Field(
        default=None,
        validation_alias="DATABASE_TEST_URL",
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

    # jwt 配置
    JWT_SECRET_KEY: str = Field(default="change-me", validation_alias="JWT_SECRET_KEY")
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7

    # 兼容旧配置名
    @property
    def SECRET_KEY(self) -> str:
        return self.JWT_SECRET_KEY

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DATABASE: int = 7
    REDIS_TIMEOUT: int = 5

    # Celery 配置 (使用 Redis 作为 broker)
    CELERY_REDIS_DATABASE: int = 8

    # 请求限制配置
    REQUEST_LIMITER_REDIS_PREFIX: str = "fastapi:limiter"

    # OAuth settings
    OAUTH_GOOGLE_CLIENT_ID: str = Field(default="", validation_alias="OAUTH_GOOGLE_CLIENT_ID")
    OAUTH_GOOGLE_CLIENT_SECRET: str = Field(default="", validation_alias="OAUTH_GOOGLE_CLIENT_SECRET")
    OAUTH_GOOGLE_REDIRECT_URI: str = Field(default="", validation_alias="OAUTH_GOOGLE_REDIRECT_URI")

    OAUTH_GITHUB_CLIENT_ID: str = Field(default="", validation_alias="OAUTH_GITHUB_CLIENT_ID")
    OAUTH_GITHUB_CLIENT_SECRET: str = Field(default="", validation_alias="OAUTH_GITHUB_CLIENT_SECRET")
    OAUTH_GITHUB_REDIRECT_URI: str = Field(default="", validation_alias="OAUTH_GITHUB_REDIRECT_URI")

    OAUTH_WECHAT_APP_ID: str = Field(default="", validation_alias="OAUTH_WECHAT_APP_ID")
    OAUTH_WECHAT_APP_SECRET: str = Field(default="", validation_alias="OAUTH_WECHAT_APP_SECRET")
    OAUTH_WECHAT_REDIRECT_URI: str = Field(default="", validation_alias="OAUTH_WECHAT_REDIRECT_URI")

    OAUTH_ALIPAY_APP_ID: str = Field(default="", validation_alias="OAUTH_ALIPAY_APP_ID")
    OAUTH_ALIPAY_PRIVATE_KEY: str = Field(default="", validation_alias="OAUTH_ALIPAY_PRIVATE_KEY")
    OAUTH_ALIPAY_PUBLIC_KEY: str = Field(default="", validation_alias="OAUTH_ALIPAY_PUBLIC_KEY")
    OAUTH_ALIPAY_REDIRECT_URI: str = Field(default="", validation_alias="OAUTH_ALIPAY_REDIRECT_URI")

    # 兼容旧配置名
    @property
    def GOOGLE_CLIENT_ID(self) -> str:
        return self.OAUTH_GOOGLE_CLIENT_ID

    @property
    def GOOGLE_CLIENT_SECRET(self) -> str:
        return self.OAUTH_GOOGLE_CLIENT_SECRET

    @property
    def GOOGLE_REDIRECT_URI(self) -> str:
        return self.OAUTH_GOOGLE_REDIRECT_URI

    @property
    def GITHUB_CLIENT_ID(self) -> str:
        return self.OAUTH_GITHUB_CLIENT_ID

    @property
    def GITHUB_CLIENT_SECRET(self) -> str:
        return self.OAUTH_GITHUB_CLIENT_SECRET

    @property
    def GITHUB_REDIRECT_URI(self) -> str:
        return self.OAUTH_GITHUB_REDIRECT_URI

    @property
    def WECHAT_APP_ID(self) -> str:
        return self.OAUTH_WECHAT_APP_ID

    @property
    def WECHAT_APP_SECRET(self) -> str:
        return self.OAUTH_WECHAT_APP_SECRET

    @property
    def WECHAT_REDIRECT_URI(self) -> str:
        return self.OAUTH_WECHAT_REDIRECT_URI

    @property
    def ALIPAY_APP_ID(self) -> str:
        return self.OAUTH_ALIPAY_APP_ID

    @property
    def ALIPAY_PRIVATE_KEY(self) -> str:
        return self.OAUTH_ALIPAY_PRIVATE_KEY

    @property
    def ALIPAY_PUBLIC_KEY(self) -> str:
        return self.OAUTH_ALIPAY_PUBLIC_KEY

    @property
    def ALIPAY_REDIRECT_URI(self) -> str:
        return self.OAUTH_ALIPAY_REDIRECT_URI

    # RAGFlow settings
    RAGFLOW_BASE_URL: str = Field(default="http://localhost:9380", validation_alias="RAGFLOW_BASE_URL")
    RAGFLOW_API_KEY: str = Field(default="", validation_alias="RAGFLOW_API_KEY")
    RAGFLOW_API_KEY_HEADER: str = Field(default="Authorization", validation_alias="RAGFLOW_API_KEY_HEADER")
    RAGFLOW_API_KEY_PREFIX: str = Field(default="Bearer", validation_alias="RAGFLOW_API_KEY_PREFIX")
    RAGFLOW_CHAT_PATH: str = Field(default="/api/v1/chats/{chat_id}/completions", validation_alias="RAGFLOW_CHAT_PATH")
    RAGFLOW_CHAT_ID: str = Field(default="", validation_alias="RAGFLOW_CHAT_ID")
    RAGFLOW_TIMEOUT: int = Field(default=30, validation_alias="RAGFLOW_TIMEOUT")

    # 操作日志加密字段
    OPERATION_LOG_ENCRYPT_KEY_INCLUDE: list[str] = Field(
        default=["password", "old_password", "new_password", "confirm_password"],
        validation_alias="OPERATION_LOG_ENCRYPT_KEY_INCLUDE",
    )

    # 兼容旧配置名
    @property
    def OPERA_LOG_ENCRYPT_KEY_INCLUDE(self) -> list[str]:
        return self.OPERATION_LOG_ENCRYPT_KEY_INCLUDE

    # 操作日志排除路径
    OPERATION_LOG_PATH_EXCLUDE: list[str] = Field(
        default=["/favicon.ico", "/docs", "/redoc", "/openapi"],
        validation_alias="OPERATION_LOG_PATH_EXCLUDE",
    )

    # 兼容旧配置名
    @property
    def OPERA_LOG_PATH_EXCLUDE(self) -> list[str]:
        return self.OPERATION_LOG_PATH_EXCLUDE

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
        """Celery broker URL，使用 Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.CELERY_REDIS_DATABASE}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.CELERY_REDIS_DATABASE}"

    @property
    def celery_backend_url(self) -> str:
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DATABASE}"

    @property
    def server_url(self) -> str:
        """返回服务器完整URL"""
        return f"http://{self.SERVER_HOST}:{self.SERVER_PORT}"

    @property
    def google_redirect_uri(self) -> str:
        """返回Google OAuth回调URI"""
        return self.OAUTH_GOOGLE_REDIRECT_URI or f"{self.server_url}/v1/users/oauth/google/callback"

    @property
    def github_redirect_uri(self) -> str:
        """返回GitHub OAuth回调URI"""
        return self.OAUTH_GITHUB_REDIRECT_URI or f"{self.server_url}/v1/users/oauth/github/callback"

    @property
    def wechat_redirect_uri(self) -> str:
        """返回WeChat OAuth回调URI"""
        return self.OAUTH_WECHAT_REDIRECT_URI or f"{self.server_url}/v1/users/oauth/wechat/callback"

    @property
    def alipay_redirect_uri(self) -> str:
        """返回Alipay OAuth回调URI"""
        return self.OAUTH_ALIPAY_REDIRECT_URI or f"{self.server_url}/v1/users/oauth/alipay/callback"


config: Config = Config()
# Backwards compatibility alias for legacy imports
settings: Config = config
