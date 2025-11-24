"""
缓存模块 - 核心功能

提供基础的Redis缓存功能，包括：
- Cache: 基础缓存管理器
- RedisBackend: Redis后端实现
- CustomKeyMaker: 自定义键生成器
- CacheTag: 缓存标签管理

注意：高级功能（监控、统计、预热、增强管理器）已移除以简化代码。
如需这些功能，请参考 Git 历史记录恢复。
"""

from .cache_manager import Cache
from .cache_tag import CacheTag
from .custom_key_maker import CustomKeyMaker
from .redis_backend import RedisBackend

__all__ = [
    "Cache",
    "RedisBackend",
    "CustomKeyMaker",
    "CacheTag",
]
