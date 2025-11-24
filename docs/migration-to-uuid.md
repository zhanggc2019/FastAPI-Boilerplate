# 迁移到 UUID 主键指南

## 概述

本文档说明如何将数据库从使用 `id` (BigInteger) 主键迁移到使用 `uuid` (UUID) 主键。

## 迁移日期

**2025-11-24**

## 变更内容

### 1. 数据库模型变更

#### BaseModel
```python
# 之前
class BaseModel(Base, TimestampMixin):
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    uuid = Column(UUID(as_uuid=True), default=uuid4, unique=True, nullable=False)

# 之后
class BaseModel(Base, TimestampMixin):
    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
```

#### 外键变更

**User 模型**:
- 主键从 `id` 改为 `uuid`

**Task 模型**:
- 主键从 `id` 改为 `uuid`
- 外键从 `task_author_id` 改为 `task_author_uuid`
- 外键引用从 `users.id` 改为 `users.uuid`

**ApiKey 模型**:
- 主键从 `id` 改为 `uuid`
- 外键从 `user_id` 改为 `user_uuid`
- 外键引用从 `users.id` 改为 `users.uuid`

### 2. Repository 变更

**ApiKeyRepository**:
```python
# 之前
async def get_by_user_id(self, user_id: int) -> list[ApiKey]

# 之后
async def get_by_user_uuid(self, user_uuid: UUID) -> list[ApiKey]
```

**TaskRepository**:
```python
# 之前
async def get_by_author_id(self, author_id: int, join_: set[str] | None = None) -> list[Task]
async def set_completed(self, task_id: int, completed: bool = True) -> Task

# 之后
async def get_by_author_uuid(self, author_uuid: UUID, join_: set[str] | None = None) -> list[Task]
async def set_completed(self, task_uuid: UUID, completed: bool = True) -> Task
```

### 3. Service 变更

**BaseService**:
```python
# 之前
async def get_by_id(self, id_: int, join_: set[str] | None = None) -> ModelType

# 之后
async def get_by_uuid(self, uuid_: UUID, join_: set[str] | None = None) -> ModelType
```

**ApiKeyService**:
```python
# 之前
async def create_api_key(self, user_id: int, data: ApiKeyCreate) -> ApiKey
async def get_user_api_keys(self, user_id: int) -> list[ApiKey]
async def revoke_api_key(self, user_id: int, key_id: int) -> bool

# 之后
async def create_api_key(self, user_uuid: UUID, data: ApiKeyCreate) -> ApiKey
async def get_user_api_keys(self, user_uuid: UUID) -> list[ApiKey]
async def revoke_api_key(self, user_uuid: UUID, key_uuid: UUID) -> bool
```

**TaskService**:
```python
# 之前
async def get_by_author_id(self, author_id: int) -> list[Task]
async def add(self, title: str, description: str, author_id: int) -> Task
async def complete(self, task_id: int) -> Task

# 之后
async def get_by_author_uuid(self, author_uuid: UUID) -> list[Task]
async def add(self, title: str, description: str, author_uuid: UUID) -> Task
async def complete(self, task_uuid: UUID) -> Task
```

### 4. API Routes 变更

**API Keys**:
```python
# 之前
@router.delete("/{key_id}")
async def revoke_api_key(key_id: int, ...)

# 之后
@router.delete("/{key_uuid}")
async def revoke_api_key(key_uuid: UUID, ...)
```

**Tasks**:
```python
# 之前
await task_service.add(author_id=request.user.id, ...)

# 之后
await task_service.add(author_uuid=request.user.uuid, ...)
```

### 5. 权限控制变更

**User 模型**:
```python
# 之前
(Allow, UserPrincipal(value=self.id), self_permissions)

# 之后
(Allow, UserPrincipal(value=self.uuid), self_permissions)
```

**Task 模型**:
```python
# 之前
(Allow, UserPrincipal(self.task_author_id), self_permissions)

# 之后
(Allow, UserPrincipal(self.task_author_uuid), self_permissions)
```

## 迁移完成状态 ✅

### 已完成的工作

✅ **数据库迁移**: 已完成
- 所有表的主键从 `id` (BigInteger) 改为 `uuid` (UUID)
- 所有外键从 `*_id` 改为 `*_uuid`
- 旧数据完整保留并迁移

✅ **模型修改**: 已完成
- `BaseModel`: 移除 `id`,使用 `uuid` 作为主键
- `User`: 更新 `__acl__()` 使用 `self.uuid`
- `ApiKey`: 外键 `user_id` → `user_uuid`
- `Task`: 外键 `task_author_id` → `task_author_uuid`

✅ **Repository 修改**: 已完成
- `ApiKeyRepository`: `get_by_user_id()` → `get_by_user_uuid()`
- `TaskRepository`: `get_by_author_id()` → `get_by_author_uuid()`

✅ **Service 修改**: 已完成
- `BaseService`: `get_by_id()` → `get_by_uuid()`
- `UserService`: `update_user()` 参数改为 `user_uuid: UUID`
- `ApiKeyService`: 所有方法使用 `UUID` 参数
- `TaskService`: 所有方法使用 `UUID` 参数
- `AuthService`: JWT payload 使用 `user_uuid`

✅ **API 路由修改**: 已完成
- `api_keys.py`: 使用 `current_user.uuid` 和 `key_uuid: UUID`
- `tasks.py`: 使用 `request.user.uuid`

✅ **Schema 修改**: 已完成
- `ApiKeyResponse`: `id` → `uuid`, `user_id` → `user_uuid`
- `CurrentUser`: `id: int` → `uuid: UUID`

✅ **认证中间件修改**: 已完成
- JWT 解析 `user_uuid` 而不是 `user_id`
- `current_user.uuid` 设置正确

✅ **依赖注入修改**: 已完成
- `get_current_user()`: 使用 `get_by_uuid()`
- `get_user_principals()`: 使用 `user.uuid`

✅ **测试验证**: 已完成
- 用户登录: ✅
- 获取用户信息: ✅
- 创建 API Key: ✅
- 获取 API Keys 列表: ✅
- 删除 API Key: ✅

**所有功能已成功迁移到 UUID 主键系统!**

详细测试结果请查看: [UUID 迁移测试结果](./uuid-migration-test-results.md)

## 迁移步骤

### 1. 备份数据库

**重要**: 在执行迁移之前,请务必备份数据库!

```bash
pg_dump -h 214.10.8.251 -U postgres -d fastapi_boilerplate > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 2. 运行迁移

```bash
# 进入项目目录
cd /home/zgc/FastAPI-Boilerplate

# 激活虚拟环境
source .venv/bin/activate

# 运行迁移
alembic upgrade head
```

### 3. 验证迁移

检查数据库结构:
```sql
-- 检查 users 表
\d users

-- 检查 tasks 表
\d tasks

-- 检查 api_keys 表
\d api_keys
```

预期结果:
- 所有表的主键都是 `uuid` (UUID 类型)
- 外键都引用 `uuid` 字段
- 不再有 `id` 字段

### 4. 测试 API

```bash
# 测试注册
curl -X POST http://localhost:8001/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","username":"testuser","password":"Test@123"}'

# 测试登录
curl -X POST http://localhost:8001/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123"}'

# 测试创建 API Key
curl -X POST http://localhost:8001/api/v1/api-keys \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"name":"Test Key"}'
```

## 回滚

如果迁移出现问题,可以回滚到之前的版本:

```bash
alembic downgrade -1
```

## 注意事项

1. **性能**: UUID 占用 16 字节,比 BigInteger (8 字节) 大,但对于大多数应用影响可以忽略
2. **索引**: PostgreSQL 对 UUID 有良好的索引支持
3. **兼容性**: 确保所有依赖此 API 的客户端都更新为使用 UUID
4. **日志**: 迁移过程中会保留所有数据,只是标识符类型改变

## 受影响的文件

### 模型文件
- `app/models/base.py`
- `app/models/user.py`
- `app/models/task.py`
- `app/models/api_key.py`

### Repository 文件
- `app/repositories/base.py`
- `app/repositories/api_key.py`
- `app/repositories/task.py`

### Service 文件
- `app/services/base.py`
- `app/services/api_key.py`
- `app/services/task.py`

### API 文件
- `app/api/v1/api_keys/api_keys.py`
- `app/api/v1/tasks/tasks.py`

### 迁移文件
- `migrations/versions/20251124_migrate_to_uuid_primary_key.py`

## 总结

迁移到 UUID 主键提供了:
- ✅ 更好的安全性 (无法遍历)
- ✅ 更好的分布式支持 (全局唯一)
- ✅ 更简洁的代码 (统一标识符)
- ✅ 符合现代 API 最佳实践

