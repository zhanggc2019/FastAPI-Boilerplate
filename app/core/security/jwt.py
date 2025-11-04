import warnings
from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt

from app.core.config import config
from app.core.exceptions import CustomException


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
        """Validate security of the configured JWT secret key."""
        insecure_defaults = {"super-secret-key", "change-me"}
        if not JWTHandler.secret_key or JWTHandler.secret_key in insecure_defaults:
            raise ValueError(
                "JWT secret key missing or set to an insecure default. Please define SECRET_KEY"
                " as a random string of at least 32 characters."
            )
        if len(JWTHandler.secret_key) < 16:
            warnings.warn(
                "JWT secret key is shorter than 16 characters; consider using a longer value for better security.",
                SecurityWarning,
                stacklevel=3,
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
