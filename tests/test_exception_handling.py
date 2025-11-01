import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from core.exceptions import (
    CustomException,
    BadRequestException,
    NotFoundException,
    UnauthorizedException,
    ForbiddenException,
    ConflictException,
    DataValidationException,
    ResourceNotFoundException,
    InvalidOperationException,
    ExternalServiceException,
    ExternalServiceTimeoutException,
    CacheException,
    InternalServerException,
    ServiceUnavailableException,
)
from core.exceptions.handler import ExceptionHandler, ErrorResponse, create_exception_handlers


class TestExceptionHandling:
    """异常处理测试"""

    @pytest.fixture
    def app(self):
        """创建测试应用"""
        app = FastAPI()

        # 添加异常处理器
        handlers = create_exception_handlers()
        for exc_class, handler in handlers.items():
            app.add_exception_handler(exc_class, handler)

        return app

    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return TestClient(app)

    def test_custom_exception_base(self):
        """测试自定义异常基类"""
        exc = CustomException("Test message", detail="Test detail")

        assert exc.message == "Test message"
        assert exc.detail == "Test detail"
        assert exc.code == 502
        assert exc.error_code == 502

    def test_bad_request_exception(self):
        """测试400异常"""
        exc = BadRequestException("Bad request test")

        assert exc.message == "Bad request test"
        assert exc.code == 400
        assert exc.error_code == 400

    def test_not_found_exception(self):
        """测试404异常"""
        exc = NotFoundException("Resource not found")

        assert exc.message == "Resource not found"
        assert exc.code == 404
        assert exc.error_code == 404

    def test_unauthorized_exception(self):
        """测试401异常"""
        exc = UnauthorizedException("Unauthorized access")

        assert exc.message == "Unauthorized access"
        assert exc.code == 401
        assert exc.error_code == 401

    def test_forbidden_exception(self):
        """测试403异常"""
        exc = ForbiddenException("Forbidden access")

        assert exc.message == "Forbidden access"
        assert exc.code == 403
        assert exc.error_code == 403

    def test_conflict_exception(self):
        """测试409异常"""
        exc = ConflictException("Resource conflict")

        assert exc.message == "Resource conflict"
        assert exc.code == 409
        assert exc.error_code == 409

    def test_data_validation_exception(self):
        """测试数据验证异常"""
        exc = DataValidationException("Validation failed", field="email")

        assert exc.message == "Validation failed"
        assert exc.detail == "email"
        assert exc.code == 400
        assert exc.error_code == 40003

    def test_resource_not_found_exception(self):
        """测试资源未找到异常"""
        exc = ResourceNotFoundException("Task not found")

        assert exc.message == "Task not found"
        assert exc.code == 404
        assert exc.error_code == 40402

    def test_invalid_operation_exception(self):
        """测试无效操作异常"""
        exc = InvalidOperationException("Cannot complete completed task")

        assert exc.message == "Cannot complete completed task"
        assert exc.code == 400
        assert exc.error_code == 40002

    def test_external_service_exception(self):
        """测试外部服务异常"""
        exc = ExternalServiceException("External API failed")

        assert exc.message == "External API failed"
        assert exc.code == 502
        assert exc.error_code == 50201

    def test_external_service_timeout_exception(self):
        """测试外部服务超时异常"""
        exc = ExternalServiceTimeoutException("External service timeout")

        assert exc.message == "External service timeout"
        assert exc.code == 504
        assert exc.error_code == 50401

    def test_cache_exception(self):
        """测试缓存异常"""
        exc = CacheException("Cache operation failed")

        assert exc.message == "Cache operation failed"
        assert exc.code == 500
        assert exc.error_code == 50001

    def test_internal_server_exception(self):
        """测试内部服务器异常"""
        exc = InternalServerException("Internal server error")

        assert exc.message == "Internal server error"
        assert exc.code == 500
        assert exc.error_code == 500

    def test_service_unavailable_exception(self):
        """测试服务不可用异常"""
        exc = ServiceUnavailableException("Service unavailable")

        assert exc.message == "Service unavailable"
        assert exc.code == 503
        assert exc.error_code == 503

    def test_exception_handler_creation(self):
        """测试异常处理器创建"""
        handlers = create_exception_handlers()

        assert len(handlers) > 0
        assert CustomException in handlers
        assert BadRequestException in handlers
        assert NotFoundException in handlers

    def test_error_response_structure(self):
        """测试错误响应结构"""
        error_response = ErrorResponse(
            success=False,
            message="Test error",
            error_code=40001,
            details={"field": "email", "reason": "invalid format"},
        )

        assert error_response.success is False
        assert error_response.message == "Test error"
        assert error_response.error_code == 40001
        assert error_response.details == {"field": "email", "reason": "invalid format"}

    @pytest.mark.asyncio
    async def test_exception_handler_execution(self):
        """测试异常处理器执行"""
        handler = ExceptionHandler()

        exc = BadRequestException("Bad request test")

        # 模拟请求上下文
        mock_request = AsyncMock()

        response = await handler.handle_exception(exc, mock_request)

        assert response.status_code == 400
        assert response.content is not None

    def test_fastapi_exception_handlers(self, app, client):
        """测试FastAPI异常处理器"""

        @app.get("/test-bad-request")
        def test_bad_request():
            raise BadRequestException("Bad request from endpoint")

        @app.get("/test-not-found")
        def test_not_found():
            raise NotFoundException("Resource not found from endpoint")

        @app.get("/test-unauthorized")
        def test_unauthorized():
            raise UnauthorizedException("Unauthorized from endpoint")

        @app.get("/test-forbidden")
        def test_forbidden():
            raise ForbiddenException("Forbidden from endpoint")

        @app.get("/test-conflict")
        def test_conflict():
            raise ConflictException("Conflict from endpoint")

        # 测试400错误
        response = client.get("/test-bad-request")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "Bad request from endpoint" in data["message"]

        # 测试404错误
        response = client.get("/test-not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert "Resource not found from endpoint" in data["message"]

        # 测试401错误
        response = client.get("/test-unauthorized")
        assert response.status_code == 401
        data = response.json()
        assert data["success"] is False
        assert "Unauthorized from endpoint" in data["message"]

        # 测试403错误
        response = client.get("/test-forbidden")
        assert response.status_code == 403
        data = response.json()
        assert data["success"] is False
        assert "Forbidden from endpoint" in data["message"]

        # 测试409错误
        response = client.get("/test-conflict")
        assert response.status_code == 409
        data = response.json()
        assert data["success"] is False
        assert "Conflict from endpoint" in data["message"]

    def test_business_exception_handlers(self, app, client):
        """测试业务异常处理器"""

        @app.get("/test-resource-not-found")
        def test_resource_not_found():
            raise ResourceNotFoundException("Task with ID 123 not found")

        @app.get("/test-data-validation")
        def test_data_validation():
            raise DataValidationException("Email format is invalid", field="email")

        @app.get("/test-invalid-operation")
        def test_invalid_operation():
            raise InvalidOperationException("Cannot delete completed task")

        @app.get("/test-external-service")
        def test_external_service():
            raise ExternalServiceException("External payment service is down")

        # 测试资源未找到
        response = client.get("/test-resource-not-found")
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == 40402

        # 测试数据验证错误
        response = client.get("/test-data-validation")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == 40003

        # 测试无效操作
        response = client.get("/test-invalid-operation")
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == 40002

        # 测试外部服务错误
        response = client.get("/test-external-service")
        assert response.status_code == 502
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == 50201

    def test_exception_with_details(self, app, client):
        """测试带详细信息的异常"""

        @app.post("/test-validation-with-details")
        def test_validation_with_details(user_data: dict):
            errors = []

            if not user_data.get("email"):
                errors.append({"field": "email", "message": "Email is required"})
            elif "@" not in user_data["email"]:
                errors.append({"field": "email", "message": "Invalid email format"})

            if not user_data.get("password"):
                errors.append({"field": "password", "message": "Password is required"})
            elif len(user_data["password"]) < 8:
                errors.append({"field": "password", "message": "Password must be at least 8 characters"})

            if errors:
                raise DataValidationException("Validation failed", field=errors)

            return {"success": True}

        # 测试验证错误
        response = client.post("/test-validation-with-details", json={})
        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert data["error_code"] == 40003
        assert "details" in data

    def test_unhandled_exception_fallback(self, app, client):
        """测试未处理异常的回退处理"""

        @app.get("/test-unhandled-exception")
        def test_unhandled_exception():
            raise ValueError("This is an unhandled exception")

        response = client.get("/test-unhandled-exception")
        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "Internal server error" in data["message"]

    @pytest.mark.asyncio
    async def test_exception_logging(self):
        """测试异常日志记录"""

        with patch("core.exceptions.handler.logger") as mock_logger:
            handler = ExceptionHandler()

            exc = BadRequestException("Test logging")
            mock_request = AsyncMock()

            await handler.handle_exception(exc, mock_request)

            # 验证日志记录
            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args[0]
            assert "Test logging" in call_args[0]

    def test_exception_inheritance(self):
        """测试异常继承关系"""

        # 所有业务异常都应该继承自CustomException
        assert issubclass(ResourceNotFoundException, CustomException)
        assert issubclass(DataValidationException, CustomException)
        assert issubclass(InvalidOperationException, CustomException)
        assert issubclass(ExternalServiceException, CustomException)
        assert issubclass(CacheException, CustomException)

        # 基础异常也应该继承自CustomException
        assert issubclass(BadRequestException, CustomException)
        assert issubclass(NotFoundException, CustomException)
        assert issubclass(UnauthorizedException, CustomException)
        assert issubclass(ForbiddenException, CustomException)
        assert issubclass(ConflictException, CustomException)
        assert issubclass(InternalServerException, CustomException)
        assert issubclass(ServiceUnavailableException, CustomException)

    def test_exception_error_codes(self):
        """测试异常错误代码"""

        # 测试错误代码的唯一性和合理性
        exceptions = [
            BadRequestException(),
            NotFoundException(),
            UnauthorizedException(),
            ForbiddenException(),
            ConflictException(),
            DataValidationException(),
            ResourceNotFoundException(),
            InvalidOperationException(),
            ExternalServiceException(),
            ExternalServiceTimeoutException(),
            CacheException(),
            InternalServerException(),
            ServiceUnavailableException(),
        ]

        error_codes = []
        for exc in exceptions:
            error_codes.append(exc.error_code)

        # 错误代码应该是唯一的
        assert len(error_codes) == len(set(error_codes))

        # 错误代码应该在合理范围内
        for code in error_codes:
            assert 400 <= code <= 599  # HTTP错误代码范围
