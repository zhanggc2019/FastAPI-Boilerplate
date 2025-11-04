from __future__ import annotations

from dataclasses import dataclass
from itertools import zip_longest
from typing import Iterable

from fastapi import APIRouter, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import ASGIApp

from app.core.config import config
from app.core.logging import logger


def _normalise_version(version: str | None) -> list[int]:
    """将版本字符串转换为整数列表，便于比较。"""
    if not version:
        return []
    cleaned = version.lower().lstrip("v")
    parts: list[int] = []
    for part in cleaned.split("."):
        try:
            parts.append(int(part))
        except ValueError:
            parts.append(0)
    return parts


@dataclass(slots=True)
class APIVersionManager:
    """管理 API 版本的读取、校验及迁移策略。"""

    current_version: str = config.API_CURRENT_VERSION
    supported_versions: list[str] = None  # type: ignore[assignment]
    version_header: str = config.API_VERSION_HEADER

    def __post_init__(self) -> None:
        if self.supported_versions is None:
            self.supported_versions = [self.current_version]
        else:
            self.supported_versions = list(self.supported_versions)
        if self.current_version not in self.supported_versions:
            raise ValueError(
                f"Current version {self.current_version!r} is not in supported versions {self.supported_versions!r}"
            )
        self.default_version: str = self.current_version

    def extract_version_from_request(self, request: Request) -> str:
        """从请求头读取版本号，大小写不敏感，不合法时回退到默认版本。"""
        header_name = self.version_header.lower()
        for key, value in request.headers.items():
            if key.lower() == header_name and value:
                candidate = value.strip()
                if self.is_version_supported(candidate):
                    return candidate
        return self.default_version

    def is_version_supported(self, version: str | None) -> bool:
        """校验版本是否在受支持列表内。"""
        return bool(version) and version in self.supported_versions

    def should_route_to_current_version(self, version: str | None) -> bool:
        """判断是否应该路由到当前版本。"""
        return bool(version) and version == self.current_version

    def compare_versions(self, lhs: str | None, rhs: str | None) -> int:
        """比较两个版本号，返回 -1/0/1。"""
        left_parts = _normalise_version(lhs)
        right_parts = _normalise_version(rhs)
        for l, r in zip_longest(left_parts, right_parts, fillvalue=0):
            if l < r:
                return -1
            if l > r:
                return 1
        return 0

    def is_version_deprecated(self, version: str | None) -> bool:
        """判断给定版本是否已被弃用。"""
        if not version:
            return True
        if not self.is_version_supported(version):
            return True
        return self.compare_versions(version, self.current_version) < 0

    def check_version_deprecation(self, version: str | None) -> None:
        """如版本已弃用则记录告警日志。"""
        if self.is_version_deprecated(version):
            migration = " -> ".join(self.get_migration_path(version or "", self.current_version))
            logger.warning(
                "API version %s is deprecated. Please migrate to %s%s",
                version,
                self.current_version,
                f" via {migration}" if migration else "",
            )

    def get_migration_path(self, start: str, target: str) -> list[str]:
        """根据受支持版本顺序计算迁移路径。"""
        try:
            start_index = self.supported_versions.index(start)
            end_index = self.supported_versions.index(target)
        except ValueError:
            return []
        if start_index >= end_index:
            return []
        return self.supported_versions[start_index + 1 : end_index + 1]


class VersionMiddleware(BaseHTTPMiddleware):
    """在请求生命周期中注入 API 版本并补齐响应头。"""

    def __init__(self, app: ASGIApp, *, version_manager: APIVersionManager | None = None) -> None:
        super().__init__(app)
        self.version_manager = version_manager or APIVersionManager()

    async def dispatch(self, request: Request, call_next) -> Response:
        """为请求解析版本并在响应头写入版本信息。"""
        header_version = self.version_manager.extract_version_from_request(request)
        path_version = self._extract_version_from_path(request.url.path)

        effective_version = header_version
        if path_version and self.version_manager.is_version_supported(path_version):
            effective_version = path_version

        self.version_manager.check_version_deprecation(effective_version)
        request.state.api_version = effective_version

        response = await call_next(request)
        response.headers[self.version_manager.version_header] = effective_version
        return response

    @staticmethod
    def _extract_version_from_path(path: str) -> str | None:
        """从请求路径前缀解析版本号。"""
        for segment in path.split("/"):
            if not segment:
                continue
            lowered = segment.lower()
            if lowered.startswith("v") and any(ch.isdigit() for ch in lowered[1:]):
                return segment
            break
        return None


class VersionedAPIRouter(APIRouter):
    """带版本前缀的 FastAPI 路由器。"""

    def __init__(
        self,
        *,
        version: str | None = None,
        prefix: str | None = None,
        version_manager: APIVersionManager | None = None,
        **kwargs,
    ):
        self.version_manager = version_manager or APIVersionManager()
        self.version = version or self.version_manager.current_version

        computed_prefix = self._resolve_prefix(prefix)
        self._emit_version_warnings()

        super().__init__(prefix=computed_prefix, **kwargs)

    def _resolve_prefix(self, custom_prefix: str | None) -> str:
        """确定路由前缀并同步版本信息。"""
        if custom_prefix:
            normalised = custom_prefix if custom_prefix.startswith("/") else f"/{custom_prefix}"
            extracted = VersionMiddleware._extract_version_from_path(normalised)
            if extracted:
                self.version = extracted
            return normalised
        return f"/{self.version}"

    def _emit_version_warnings(self) -> None:
        """根据版本状态打印提示信息。"""
        if not self.version_manager.is_version_supported(self.version):
            logger.warning("API version %s is not in the supported list %s.", self.version, self.version_manager.supported_versions)
        if self.version_manager.is_version_deprecated(self.version):
            logger.warning("API version %s is deprecated; current version is %s.", self.version, self.version_manager.current_version)


__all__ = ["APIVersionManager", "VersionMiddleware", "VersionedAPIRouter"]

