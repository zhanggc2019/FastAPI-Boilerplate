import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.core.api_versioning import APIVersionManager, VersionedAPIRouter
from app.core.config import settings


class TestAPIVersioning:
    """API版本管理测试"""

    @pytest.fixture
    def version_manager(self):
        """创建版本管理器实例"""
        return APIVersionManager()

    @pytest.fixture
    def app(self):
        """创建测试应用"""
        return FastAPI()

    @pytest.fixture
    def client(self, app):
        """创建测试客户端"""
        return TestClient(app)

    def test_version_manager_initialization(self, version_manager):
        """测试版本管理器初始化"""

        assert version_manager.current_version == "v1"
        assert version_manager.supported_versions == ["v1"]
        assert version_manager.default_version == "v1"
        assert version_manager.version_header == "X-API-Version"

    def test_version_manager_with_custom_config(self):
        """测试自定义配置的版本管理器"""

        with patch.object(settings, "API_VERSION_HEADER", "X-My-API-Version"):
            with patch.object(settings, "API_CURRENT_VERSION", "v2"):
                with patch.object(settings, "API_SUPPORTED_VERSIONS", ["v1", "v2"]):
                    manager = APIVersionManager()

                    assert manager.version_header == "X-My-API-Version"
                    assert manager.current_version == "v2"
                    assert manager.supported_versions == ["v1", "v2"]
                    assert manager.default_version == "v2"

    def test_version_extraction_from_header(self, version_manager):
        """测试从请求头提取版本"""

        # 模拟请求对象
        class MockRequest:
            def __init__(self, headers=None):
                self.headers = headers or {}

        # 测试有效版本
        request = MockRequest({"X-API-Version": "v1"})
        version = version_manager.extract_version_from_request(request)
        assert version == "v1"

        # 测试自定义头
        request = MockRequest({"X-My-API-Version": "v2"})
        version = version_manager.extract_version_from_request(request)
        assert version == "v1"  # 使用默认版本，因为头名称不匹配

        # 测试无版本头
        request = MockRequest({})
        version = version_manager.extract_version_from_request(request)
        assert version == "v1"  # 使用默认版本

    def test_version_validation(self, version_manager):
        """测试版本验证"""

        # 测试有效版本
        assert version_manager.is_version_supported("v1") is True

        # 测试无效版本
        assert version_manager.is_version_supported("v3") is False
        assert version_manager.is_version_supported("invalid") is False

        # 测试空版本
        assert version_manager.is_version_supported("") is False
        assert version_manager.is_version_supported(None) is False

    def test_version_routing(self, version_manager):
        """测试版本路由"""

        # 测试路由到当前版本
        assert version_manager.should_route_to_current_version("v1") is True

        # 测试路由到旧版本
        assert version_manager.should_route_to_current_version("v0") is False

        # 测试路由到未来版本
        assert version_manager.should_route_to_current_version("v2") is False

    def test_version_deprecation_warning(self, version_manager):
        """测试版本弃用警告"""

        # 测试当前版本不触发警告
        with patch("app.core.api_versioning.logger") as mock_logger:
            version_manager.check_version_deprecation("v1")
            mock_logger.warning.assert_not_called()

        # 测试旧版本触发警告
        with patch("app.core.api_versioning.logger") as mock_logger:
            version_manager.check_version_deprecation("v0")
            mock_logger.warning.assert_called_once()
            call_args = mock_logger.warning.call_args[0]
            assert "deprecated" in call_args[0]

    def test_versioned_router_creation(self):
        """测试版本化路由器创建"""

        router = VersionedAPIRouter()

        assert router.version == "v1"
        assert router.prefix == "/v1"
        assert router.version_manager is not None

    def test_versioned_router_with_custom_version(self):
        """测试自定义版本的版本化路由器"""

        router = VersionedAPIRouter(version="v2")

        assert router.version == "v2"
        assert router.prefix == "/v2"

    def test_versioned_router_with_custom_prefix(self):
        """测试自定义前缀的版本化路由器"""

        router = VersionedAPIRouter(prefix="/api/v1")

        assert router.version == "v1"
        assert router.prefix == "/api/v1"

    def test_versioned_router_endpoint_registration(self, app):
        """测试版本化路由器端点注册"""

        router = VersionedAPIRouter()

        @router.get("/users")
        def get_users():
            return {"users": ["user1", "user2"]}

        @router.post("/users")
        def create_user(user_data: dict):
            return {"user": user_data, "id": 1}

        app.include_router(router)

        client = TestClient(app)

        # 测试GET端点
        response = client.get("/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert "users" in data

        # 测试POST端点
        response = client.post("/v1/users", json={"name": "test"})
        assert response.status_code == 200
        data = response.json()
        assert data["user"]["name"] == "test"

    def test_multiple_version_routers(self, app):
        """测试多版本路由器共存"""

        # 创建v1路由器
        v1_router = VersionedAPIRouter(version="v1")

        @v1_router.get("/users")
        def get_users_v1():
            return {"version": "v1", "users": ["user1"]}

        # 创建v2路由器
        v2_router = VersionedAPIRouter(version="v2")

        @v2_router.get("/users")
        def get_users_v2():
            return {"version": "v2", "users": ["user1", "user2"]}

        app.include_router(v1_router)
        app.include_router(v2_router)

        client = TestClient(app)

        # 测试v1端点
        response = client.get("/v1/users")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "v1"
        assert len(data["users"]) == 1

        # 测试v2端点
        response = client.get("/v2/users")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "v2"
        assert len(data["users"]) == 2

    def test_version_middleware_integration(self, app):
        """测试版本中间件集成"""

        from app.core.api_versioning import VersionMiddleware

        # 添加版本中间件
        version_manager = APIVersionManager()
        app.add_middleware(VersionMiddleware, version_manager=version_manager)

        # 添加版本化路由器
        router = VersionedAPIRouter()

        @router.get("/version-info")
        def get_version_info():
            return {"current_version": "v1"}

        app.include_router(router)

        client = TestClient(app)

        # 测试无版本头请求
        response = client.get("/v1/version-info")
        assert response.status_code == 200

        # 测试有版本头请求
        response = client.get("/v1/version-info", headers={"X-API-Version": "v1"})
        assert response.status_code == 200

    def test_version_header_in_response(self, app):
        """测试响应中的版本头"""

        from app.core.api_versioning import VersionMiddleware

        version_manager = APIVersionManager()
        app.add_middleware(VersionMiddleware, version_manager=version_manager)

        router = VersionedAPIRouter()

        @router.get("/test")
        def test_endpoint():
            return {"message": "test"}

        app.include_router(router)

        client = TestClient(app)

        response = client.get("/v1/test")
        assert response.status_code == 200

        # 检查响应头
        assert "X-API-Version" in response.headers
        assert response.headers["X-API-Version"] == "v1"

    def test_version_configuration_validation(self):
        """测试版本配置验证"""

        # 测试有效的版本配置
        manager = APIVersionManager(current_version="v2", supported_versions=["v1", "v2", "v3"])

        assert manager.current_version == "v2"
        assert manager.supported_versions == ["v1", "v2", "v3"]

        # 测试当前版本不在支持版本列表中
        with pytest.raises(ValueError):
            APIVersionManager(current_version="v4", supported_versions=["v1", "v2", "v3"])

    def test_version_comparison(self):
        """测试版本比较"""

        manager = APIVersionManager(current_version="v2", supported_versions=["v1", "v2", "v3"])

        # 测试版本比较
        assert manager.compare_versions("v1", "v2") == -1
        assert manager.compare_versions("v2", "v2") == 0
        assert manager.compare_versions("v3", "v2") == 1
        assert manager.compare_versions("v10", "v2") == 1  # v10 > v2

    def test_version_deprecation_policy(self):
        """测试版本弃用策略"""

        manager = APIVersionManager(current_version="v3", supported_versions=["v1", "v2", "v3"])

        # v1应该被弃用（距离当前版本2个版本）
        assert manager.is_version_deprecated("v1") is True

        # v2应该被弃用（距离当前版本1个版本）
        assert manager.is_version_deprecated("v2") is True

        # v3不应该被弃用（当前版本）
        assert manager.is_version_deprecated("v3") is False

    def test_version_migration_path(self):
        """测试版本迁移路径"""

        manager = APIVersionManager(current_version="v3", supported_versions=["v1", "v2", "v3", "v4"])

        # 测试从v1到v3的迁移路径
        migration_path = manager.get_migration_path("v1", "v3")
        assert migration_path == ["v2", "v3"]

        # 测试从v2到v4的迁移路径
        migration_path = manager.get_migration_path("v2", "v4")
        assert migration_path == ["v3", "v4"]

        # 测试相同版本的迁移路径
        migration_path = manager.get_migration_path("v3", "v3")
        assert migration_path == []

    def test_versioned_router_deprecation_warning(self, app):
        """测试版本化路由弃用警告"""

        # 创建v1路由器（应该触发弃用警告）
        with patch("app.core.api_versioning.logger") as mock_logger:
            v1_router = VersionedAPIRouter(version="v0")

            @v1_router.get("/test")
            def test_endpoint():
                return {"message": "test"}

            app.include_router(v1_router)

            # 应该记录弃用警告
            mock_logger.warning.assert_called()
            call_args = mock_logger.warning.call_args[0]
            assert "deprecated" in call_args[0]

    def test_version_header_case_insensitive(self, version_manager):
        """测试版本头大小写不敏感"""

        class MockRequest:
            def __init__(self, headers=None):
                self.headers = headers or {}

        # 测试不同大小写的版本头
        request = MockRequest({"x-api-version": "v1"})
        version = version_manager.extract_version_from_request(request)
        assert version == "v1"

        request = MockRequest({"X-API-VERSION": "v1"})
        version = version_manager.extract_version_from_request(request)
        assert version == "v1"

    def test_version_with_sub_versions(self):
        """测试带子版本的版本管理"""

        manager = APIVersionManager(current_version="v1.2", supported_versions=["v1.0", "v1.1", "v1.2", "v2.0"])

        assert manager.current_version == "v1.2"
        assert manager.is_version_supported("v1.1") is True
        assert manager.is_version_supported("v2.0") is True
        assert manager.is_version_supported("v1.3") is False

    def test_version_router_endpoint_documentation(self, app):
        """测试版本化路由器端点文档"""

        router = VersionedAPIRouter()

        @router.get("/users/{user_id}", summary="Get user by ID")
        def get_user(user_id: int):
            """Get a specific user by their ID."""
            return {"user_id": user_id, "name": "Test User"}

        app.include_router(router)

        client = TestClient(app)

        # 测试OpenAPI文档
        response = client.get("/openapi.json")
        assert response.status_code == 200

        openapi_schema = response.json()

        # 检查路径是否存在
        assert "/v1/users/{user_id}" in openapi_schema["paths"]

        # 检查端点信息
        endpoint_info = openapi_schema["paths"]["/v1/users/{user_id}"]["get"]
        assert endpoint_info["summary"] == "Get user by ID"
        assert "Get a specific user by their ID" in endpoint_info["description"]
