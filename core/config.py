from enum import Enum

from pydantic_settings import BaseSettings
from pydantic import PostgresDsn, RedisDsn, Field
from pydantic_settings import SettingsConfigDict


class EnvironmentType(str, Enum):
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", 
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    DEBUG: int = 0
    DEFAULT_LOCALE: str = "zh_CN"
    ENVIRONMENT: str = EnvironmentType.DEVELOPMENT
    POSTGRES_URL: PostgresDsn = Field(
        default=PostgresDsn("postgresql+asyncpg://user:password@127.0.0.1:5432/db-name"),
        validation_alias="POSTGRES_URL"
    )
    REDIS_URL: RedisDsn = Field(
        default=RedisDsn("redis://localhost:6379/7"),
        validation_alias="REDIS_URL"
    )
    RELEASE_VERSION: str = "0.1"
    SHOW_SQL_ALCHEMY_QUERIES: int = 0
    SECRET_KEY: str = "super-secret-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60 * 24 * 7
    CELERY_BROKER_URL: str = "amqp://rabbit:password@localhost:5672"
    CELERY_BACKEND_URL: str = "redis://localhost:6379/0"
    
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

    @property
    def postgres_url_str(self) -> str:
        return str(self.POSTGRES_URL)
    
    @property
    def redis_url_str(self) -> str:
        return str(self.REDIS_URL)


config: Config = Config()