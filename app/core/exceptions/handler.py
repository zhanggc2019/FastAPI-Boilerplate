"""
统一异常处理模块
提供全局异常处理和错误响应标准化
"""

import traceback
from typing import Any, Dict, Optional

from fastapi import Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.core.config import config
from app.core.logging import logger

from .base import CustomException


class ErrorResponse(BaseModel):
    """标准错误响应格式"""
    success: bool = False
    code: int
    message: str
    detail: Optional[str] = None
    request_id: Optional[str] = None
    path: Optional[str] = None
    method: Optional[str] = None


class ExceptionHandler:
    """统一异常处理器"""

    @staticmethod
    def create_error_response(
        code: int,
        message: str,
        detail: Optional[str] = None,
        request: Optional[Request] = None
    ) -> ErrorResponse:
        """创建标准错误响应"""
        return ErrorResponse(
            success=False,
            code=code,
            message=message,
            detail=detail,
            request_id=getattr(request.state, 'request_id', None) if request else None,
            path=str(request.url.path) if request else None,
            method=request.method if request else None
        )

    @staticmethod
    async def handle_custom_exception(request: Request, exc: CustomException) -> JSONResponse:
        """处理自定义异常"""
        logger.warning(
            f"自定义异常 - 路径: {request.url.path}, 方法: {request.method}, "
            f"错误码: {exc.code}, 消息: {exc.message}"
        )

        error_response = ExceptionHandler.create_error_response(
            code=exc.code,
            message=exc.message,
            detail=getattr(exc, 'detail', None),
            request=request
        )

        return JSONResponse(
            status_code=exc.code,
            content=error_response.model_dump()
        )

    @staticmethod
    async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
        """处理Pydantic验证错误"""
        logger.warning(
            f"验证错误 - 路径: {request.url.path}, 方法: {request.method}, "
            f"错误: {str(exc)}"
        )

        error_response = ExceptionHandler.create_error_response(
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="请求参数验证失败",
            detail=str(exc),
            request=request
        )

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_response.model_dump()
        )

    @staticmethod
    async def handle_http_exception(request: Request, exc: Exception) -> JSONResponse:
        """处理HTTP异常"""
        logger.warning(
            f"HTTP异常 - 路径: {request.url.path}, 方法: {request.method}, "
            f"状态码: {getattr(exc, 'status_code', 500)}, 错误: {str(exc)}"
        )

        status_code = getattr(exc, 'status_code', status.HTTP_500_INTERNAL_SERVER_ERROR)
        detail = getattr(exc, 'detail', str(exc))

        error_response = ExceptionHandler.create_error_response(
            code=status_code,
            message="请求处理失败",
            detail=detail,
            request=request
        )

        return JSONResponse(
            status_code=status_code,
            content=error_response.model_dump()
        )

    @staticmethod
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        """处理未预期的异常"""
        logger.error(
            f"未预期异常 - 路径: {request.url.path}, 方法: {request.method}, "
            f"错误: {str(exc)}, 堆栈: {traceback.format_exc()}"
        )

        # 生产环境不暴露详细错误信息
        detail = "内部服务器错误" if config.ENVIRONMENT == "production" else str(exc)

        error_response = ExceptionHandler.create_error_response(
            code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="服务器内部错误",
            detail=detail,
            request=request
        )

        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_response.model_dump()
        )


def create_exception_handlers() -> Dict[type, Any]:
    """创建异常处理器映射"""
    from fastapi.exceptions import RequestValidationError
    from starlette.exceptions import HTTPException as StarletteHTTPException

    handler = ExceptionHandler()

    return {
        # 自定义异常
        CustomException: handler.handle_custom_exception,

        # FastAPI验证错误
        RequestValidationError: handler.handle_validation_error,

        # HTTP异常
        StarletteHTTPException: handler.handle_http_exception,

        # 捕获所有其他异常
        Exception: handler.handle_unexpected_error,
    }
