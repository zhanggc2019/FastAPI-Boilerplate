"""
统一异常处理模块
提供全局异常处理和错误响应标准化
"""

import traceback
from typing import Any, Dict, Optional, Union

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
    detail: Optional[Union[str, Dict[str, Any]]] = None
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
    def _translate_error_message(message: str) -> str:
        """将英文错误消息翻译为中文"""
        # 常见的Pydantic错误消息映射
        translations = {
            # 邮箱验证错误
            "value is not a valid email address": "邮箱格式无效",
            "An email address must have an @-sign": "邮箱地址必须包含@符号",
            
            # 字符串长度错误
            "ensure this value has at least": "确保此值至少有",
            "characters": "个字符",
            "ensure this value has at most": "确保此值最多有",
            "String should have at least 8 characters": "密码长度至少为8个字符",
            "String should have at most": "字符串长度最多",
            "String should have at least": "字符串长度至少为",
            
            # 必填字段错误
            "field required": "此字段为必填项",
            "none is not an allowed value": "不允许为空值",
            
            # 类型错误
            "value is not a valid boolean": "值不是有效的布尔值",
            "value is not a valid integer": "值不是有效的整数",
            "value is not a valid float": "值不是有效的浮点数",
            "value is not a valid string": "值不是有效的字符串",
            
            # 数字范围错误
            "ensure this value is greater than": "确保此值大于",
            "ensure this value is greater than or equal to": "确保此值大于或等于",
            "ensure this value is less than": "确保此值小于",
            "ensure this value is less than or equal to": "确保此值小于或等于",
        }
        
        # 应用翻译
        result = message
        for en_msg, zh_msg in translations.items():
            result = result.replace(en_msg, zh_msg)
        
        return result
    
    @staticmethod
    async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
        """处理Pydantic验证错误并返回中文错误消息"""
        # 获取详细错误信息
        error_details = []
        
        # 检查是否是RequestValidationError类型，尝试获取结构化错误信息
        if hasattr(exc, 'errors'):
            for error in exc.errors():
                # 构建错误详情，确保字段信息正确
                loc = error.get("loc", [])
                field_name = loc[-1] if loc else None
                
                # 确保ctx字段是可JSON序列化的
                ctx = error.get("ctx", {})
                if ctx and not isinstance(ctx, dict):
                    ctx = str(ctx)
                elif isinstance(ctx, dict):
                    # 确保ctx字典中的值都是可序列化的
                    serializable_ctx = {}
                    for key, value in ctx.items():
                        try:
                            # 尝试将值转换为字符串
                            serializable_ctx[key] = str(value)
                        except:
                            serializable_ctx[key] = "[unserializable]"
                    ctx = serializable_ctx
                
                # 获取原始错误消息并翻译为中文
                original_message = error.get("msg", "")
                translated_message = ExceptionHandler._translate_error_message(original_message)
                
                # 针对密码字段的特殊处理，使其错误消息更加具体
                if field_name == "password" and "字符串长度至少为" in translated_message:
                    translated_message = translated_message.replace("字符串长度至少为", "密码长度至少为")
                
                # 对于body字段的错误，确保显示正确的字段名称，避免input字段值混淆
                # 特别处理password和username字段的验证错误
                if field_name in ["password", "username"]:
                    # 为这些敏感字段创建更清晰的错误信息，不直接显示输入值
                    error_detail = {
                        "type": error.get("type"),
                        "field": field_name,
                        "message": translated_message,
                        # 避免显示敏感字段的实际值
                        "input": "[已隐藏]" if field_name == "password" else str(error.get("input", "")),
                    }
                else:
                    # 其他字段保持原样，但确保所有值都是可序列化的
                    error_detail = {
                        "type": error.get("type"),
                        "field": field_name,
                        "message": translated_message,
                        "input": str(error.get("input", "")),
                    }
                
                # 只在非空且可序列化的情况下添加ctx
                if ctx:
                    error_detail["ctx"] = ctx
                
                error_details.append(error_detail)
        
        # 记录验证错误日志
        logger.warning(
            f"验证错误 - 路径: {request.url.path}, 方法: {request.method}, "
            f"错误: {str(error_details) if error_details else str(exc)}"
        )

        # 创建更清晰的错误响应，确保前端能正确获取字段级别的错误信息
        # 重新组织错误信息，以字段名为键
        field_errors = {}
        for err in error_details:
            field_name = err.get("field")
            if field_name:
                if field_name not in field_errors:
                    field_errors[field_name] = []
                field_errors[field_name].append({
                    "message": err.get("message"),
                    "type": err.get("type")
                })

        # 简化响应格式，确保所有数据都是JSON可序列化的
        error_response = ErrorResponse(
            success=False,
            code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            message="请求参数验证失败",
            detail={
                "field_errors": field_errors
            },
            request_id=getattr(request.state, 'request_id', None) if request else None,
            path=str(request.url.path) if request else None,
            method=request.method if request else None
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
