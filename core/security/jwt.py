import warnings
from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt

from core.config import config
from core.exceptions import CustomException


class JWTDecodeError(CustomException):
    code = 401
    message = "Invalid token"


class JWTExpiredError(CustomException):
    code = 401
    message = "Token expired"


class SecurityWarning(UserWarning):
    """安全相关警告"""
    pass


class JWTHandler:
    secret_key = config.SECRET_KEY
    algorithm = config.JWT_ALGORITHM
    expire_minutes = config.JWT_EXPIRE_MINUTES

    @staticmethod
    def _validate_secret_key() -> None:
        """验证JWT密钥安全性"""
        if not JWTHandler.secret_key or JWTHandler.secret_key == "super-secret-key":
            raise ValueError(
                "JWT密钥未配置或使用了不安全的默认值。请在环境变量中设置JWT_SECRET_KEY，"
                "生产环境建议使用至少32位的随机字符串。"
            )
        if len(JWTHandler.secret_key) < 16:
            warnings.warn(
                "JWT密钥长度小于16位，建议在生产环境使用更长的密钥以提高安全性。",
                SecurityWarning,
                stacklevel=3
            )

    @staticmethod
    def encode(payload: dict) -> str:
        JWTHandler._validate_secret_key()
        expire = datetime.now(timezone.utc) + timedelta(minutes=JWTHandler.expire_minutes)
        payload.update({"exp": expire})
        return jwt.encode(payload, JWTHandler.secret_key, algorithm=JWTHandler.algorithm)

    @staticmethod
    def decode(token: str) -> dict:
        JWTHandler._validate_secret_key()
        try:
            return jwt.decode(token, JWTHandler.secret_key, algorithms=[JWTHandler.algorithm])
        except ExpiredSignatureError as exception:
            raise JWTExpiredError() from exception
        except JWTError as exception:
            raise JWTDecodeError() from exception

    @staticmethod
    def decode_expired(token: str) -> dict:
        JWTHandler._validate_secret_key()
        try:
            return jwt.decode(
                token,
                JWTHandler.secret_key,
                algorithms=[JWTHandler.algorithm],
                options={"verify_exp": False},
            )
        except JWTError as exception:
            raise JWTDecodeError() from exception
