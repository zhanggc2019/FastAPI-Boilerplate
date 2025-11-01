"""
业务异常定义
包含常见的业务逻辑异常
"""

from http import HTTPStatus

from .base import CustomException


# 用户相关异常
class UserNotFoundException(CustomException):
    code = HTTPStatus.NOT_FOUND
    error_code = 40401
    message = "用户不存在"


class UserAlreadyExistsException(CustomException):
    code = HTTPStatus.CONFLICT
    error_code = 40901
    message = "用户已存在"


class InvalidCredentialsException(CustomException):
    code = HTTPStatus.UNAUTHORIZED
    error_code = 40101
    message = "用户名或密码错误"


class UserNotActiveException(CustomException):
    code = HTTPStatus.FORBIDDEN
    error_code = 40301
    message = "用户账户未激活"


# 认证授权异常
class InvalidTokenException(CustomException):
    code = HTTPStatus.UNAUTHORIZED
    error_code = 40102
    message = "无效的访问令牌"


class TokenExpiredException(CustomException):
    code = HTTPStatus.UNAUTHORIZED
    error_code = 40103
    message = "访问令牌已过期"


class InsufficientPermissionsException(CustomException):
    code = HTTPStatus.FORBIDDEN
    error_code = 40302
    message = "权限不足"


# 资源相关异常
class ResourceNotFoundException(CustomException):
    code = HTTPStatus.NOT_FOUND
    error_code = 40402
    message = "请求的资源不存在"


class ResourceAlreadyExistsException(CustomException):
    code = HTTPStatus.CONFLICT
    error_code = 40902
    message = "资源已存在"


class ResourceNotAvailableException(CustomException):
    code = HTTPStatus.SERVICE_UNAVAILABLE
    error_code = 50301
    message = "资源暂不可用"


# 业务逻辑异常
class BusinessRuleViolationException(CustomException):
    code = HTTPStatus.BAD_REQUEST
    error_code = 40001
    message = "违反业务规则"


class InvalidOperationException(CustomException):
    code = HTTPStatus.BAD_REQUEST
    error_code = 40002
    message = "无效的操作"


class DataValidationException(CustomException):
    code = HTTPStatus.BAD_REQUEST
    error_code = 40003
    message = "数据验证失败"


# 外部服务异常
class ExternalServiceException(CustomException):
    code = HTTPStatus.BAD_GATEWAY
    error_code = 50201
    message = "外部服务调用失败"


class ExternalServiceTimeoutException(CustomException):
    code = HTTPStatus.GATEWAY_TIMEOUT
    error_code = 50401
    message = "外部服务调用超时"


# 系统异常
class SystemMaintenanceException(CustomException):
    code = HTTPStatus.SERVICE_UNAVAILABLE
    error_code = 50302
    message = "系统维护中"


class RateLimitExceededException(CustomException):
    code = HTTPStatus.TOO_MANY_REQUESTS
    error_code = 42901
    message = "请求频率超限"
