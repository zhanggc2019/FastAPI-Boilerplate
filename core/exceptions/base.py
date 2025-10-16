from http import HTTPStatus
from typing import Any

from fastapi import HTTPException


class CustomException(Exception):  # noqa: N818
    code = HTTPStatus.BAD_GATEWAY
    error_code = HTTPStatus.BAD_GATEWAY
    message = HTTPStatus.BAD_GATEWAY.description

    def __init__(self, message=None):
        if message:
            self.message = message


class BadRequestException(CustomException):
    code = HTTPStatus.BAD_REQUEST
    error_code = HTTPStatus.BAD_REQUEST
    message = HTTPStatus.BAD_REQUEST.description


class NotFoundException(CustomException):
    code = HTTPStatus.NOT_FOUND
    error_code = HTTPStatus.NOT_FOUND
    message = HTTPStatus.NOT_FOUND.description


class ForbiddenException(CustomException):
    code = HTTPStatus.FORBIDDEN
    error_code = HTTPStatus.FORBIDDEN
    message = HTTPStatus.FORBIDDEN.description


class UnauthorizedException(CustomException):
    code = HTTPStatus.UNAUTHORIZED
    error_code = HTTPStatus.UNAUTHORIZED
    message = HTTPStatus.UNAUTHORIZED.description


class UnprocessableEntity(CustomException):
    code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message = HTTPStatus.UNPROCESSABLE_ENTITY.description


class DuplicateValueException(CustomException):
    code = HTTPStatus.UNPROCESSABLE_ENTITY
    error_code = HTTPStatus.UNPROCESSABLE_ENTITY
    message = HTTPStatus.UNPROCESSABLE_ENTITY.description


class HTTPError(HTTPException):
    """HTTP 异常"""

    def __init__(self, *, code: int, message: Any = None, headers: dict[str, Any] | None = None) -> None:
        super().__init__(status_code=code, detail=message, headers=headers)


class RequestError(Exception):
    """请求异常"""

    def __init__(
        self,
        *,
        code: int = 400,
        message: str = "Bad Request",
    ) -> None:
        self.code = code
        super().__init__(msg=message)


class ServerError(Exception):
    """服务器异常"""

    code = 500
    error_code = 500

    def __init__(
        self,
        *,
        message: str = "Internal Server Error",
    ) -> None:
        super().__init__(message=message)
