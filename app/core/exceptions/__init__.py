from .base import (
    BadRequestException,
    ConflictException,
    CustomException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    UnprocessableEntity,
    DuplicateValueException,
    HTTPError,
    RequestError,
    ServerError,
    InternalServerException,
    ServiceUnavailableException,
    CacheException,
)

from .business_exceptions import (
    # 用户相关异常
    UserNotFoundException,
    UserAlreadyExistsException,
    InvalidCredentialsException,
    UserNotActiveException,
    # 认证授权异常
    InvalidTokenException,
    TokenExpiredException,
    InsufficientPermissionsException,
    # 资源相关异常
    ResourceNotFoundException,
    ResourceAlreadyExistsException,
    ResourceNotAvailableException,
    # 业务逻辑异常
    BusinessRuleViolationException,
    InvalidOperationException,
    DataValidationException,
    # 外部服务异常
    ExternalServiceException,
    ExternalServiceTimeoutException,
    # 系统异常
    SystemMaintenanceException,
    RateLimitExceededException,
)
from .handler import ExceptionHandler, ErrorResponse, create_exception_handlers

__all__ = [
    # 基础异常
    "CustomException",
    "BadRequestException",
    "NotFoundException",
    "UnauthorizedException",
    "ForbiddenException",
    "UnprocessableEntity",
    "ConflictException",
    "DuplicateValueException",
    "HTTPError",
    "RequestError",
    "ServerError",
    "InternalServerException",
    "ServiceUnavailableException",
    "CacheException",
    # 异常处理器
    "ExceptionHandler",
    "ErrorResponse",
    "create_exception_handlers",
    # 用户相关异常
    "UserNotFoundException",
    "UserAlreadyExistsException",
    "InvalidCredentialsException",
    "UserNotActiveException",
    # 认证授权异常
    "InvalidTokenException",
    "TokenExpiredException",
    "InsufficientPermissionsException",
    # 资源相关异常
    "ResourceNotFoundException",
    "ResourceAlreadyExistsException",
    "ResourceNotAvailableException",
    # 业务逻辑异常
    "BusinessRuleViolationException",
    "InvalidOperationException",
    "DataValidationException",
    # 外部服务异常
    "ExternalServiceException",
    "ExternalServiceTimeoutException",
    # 系统异常
    "SystemMaintenanceException",
    "RateLimitExceededException",
]
