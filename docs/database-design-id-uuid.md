# 数据库设计: 使用 UUID 作为主键

## 概述

**重要更新 (2025-11-24)**: 本项目已从双主键模式迁移到**仅使用 UUID 作为主键**的设计。

在这个项目中,所有继承自 `BaseModel` 的数据表都使用 UUID 作为唯一的主键标识符:
- **`uuid`**: UUID 类型的主键,全局唯一标识符

## 字段定义

```python
# app/models/base.py
class BaseModel(Base, TimestampMixin):
    __abstract__ = True

    uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid4, nullable=False)
```

## 为什么使用 UUID 作为主键?

### **UUID 的优势**

**1. 安全性**:
- ✅ **无法猜测**: 防止遍历攻击,无法通过递增 ID 访问其他用户数据
- ✅ **隐藏信息**: 不暴露数据量和创建顺序

**2. 分布式友好**:
- ✅ **全局唯一**: 跨系统、跨数据库唯一,便于数据迁移和合并
- ✅ **应用层生成**: 可以在应用层生成,无需数据库协调,支持离线创建

**3. API 设计**:
- ✅ **统一标识**: 内部和外部使用同一个标识符,简化代码
- ✅ **RESTful**: 符合 RESTful API 最佳实践

**使用场景**:
```python
# 数据库关联
class ApiKey(BaseModel):
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)

# 权限控制
def __acl__(self):
    return [
        (Allow, UserPrincipal(value=self.uuid), self_permissions),
    ]

# 查询
user = await user_repository.get_by(field="uuid", value=user_uuid, unique=True)

# API 响应
class UserResponse(BaseUUIDResponse):
    uuid: UUID
    email: str
    username: str

# 注册响应示例
{
  "uuid": "5dd1c7c3-16de-42b1-90e1-90b9b68475f1",
  "email": "test@example.com",
  "username": "testuser"
}
```

## 设计模式对比

### ❌ 使用自增 ID 的问题

```python
# 不安全: 可以遍历所有用户
GET /api/users/1
GET /api/users/2
GET /api/users/3
...

# 暴露业务信息
# ID=1000 说明有 1000 个用户
# ID 连续说明最近创建了很多用户
```

### ✅ 使用 UUID 的优势

```python
# 安全: 无法遍历
GET /api/users/5dd1c7c3-16de-42b1-90e1-90b9b68475f1
GET /api/users/a7b2c8d4-9e3f-4a1b-8c2d-3e4f5a6b7c8d

# 外键关联
user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"))

# 统一标识,简化代码
```

### 📊 性能考虑

虽然 UUID 占用空间较大 (16 字节 vs 8 字节),但现代数据库对 UUID 索引的优化已经很好:
- PostgreSQL 对 UUID 有原生支持和优化
- 对于大多数应用,性能差异可以忽略不计
- 安全性和可维护性的提升远大于微小的性能损失

## 实际应用示例

### 用户注册流程

```python
# 1. 创建用户 (应用层生成 uuid)
user = await user_repository.create({
    "email": "test@example.com",
    "username": "testuser",
    "password": "hashed_password"
})
# user.uuid = "5dd1c7c3-16de-42b1-90e1-90b9b68475f1"

# 2. 返回给前端
return UserResponse.model_validate(user)
# {
#   "uuid": "5dd1c7c3-16de-42b1-90e1-90b9b68475f1",
#   "email": "test@example.com",
#   "username": "testuser"
# }
```

### API Key 关联

```python
# 数据库使用 uuid 关联
class ApiKey(BaseModel):
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"))

# 创建 API Key
api_key = await repository.create({
    "user_uuid": current_user.uuid,
    "key": "sk_xxx",
    "name": "Production Key"
})

# 查询用户的所有 API Keys
SELECT * FROM api_keys WHERE user_uuid = '5dd1c7c3-16de-42b1-90e1-90b9b68475f1';
```

## 最佳实践

### ✅ 推荐做法

1. **统一使用 UUID**
   - 数据库关联 (外键)
   - 权限控制
   - API 路径参数
   - API 响应
   - 前端显示

2. **代码规范**
   ```python
   # API 路径
   GET /api/users/{user_uuid}
   GET /api/tasks/{task_uuid}

   # 外键定义
   user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"))

   # 查询
   user = await repository.get_by("uuid", user_uuid, unique=True)
   ```

3. **日志记录**
   - 使用 UUID 便于追踪和关联
   - UUID 在分布式系统中全局唯一

### ❌ 避免的做法

1. ❌ 在 API 路径中暴露自增 ID
   ```python
   # 不安全
   GET /api/users/123

   # 安全
   GET /api/users/5dd1c7c3-16de-42b1-90e1-90b9b68475f1
   ```

2. ❌ 混用 ID 和 UUID
   ```python
   # 不一致,容易出错
   user_id = Column(BigInteger, ForeignKey("users.id"))

   # 统一使用 UUID
   user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"))
   ```

## 迁移指南

如果你的项目之前使用了 ID,可以按照以下步骤迁移到 UUID:

1. **运行迁移脚本**
   ```bash
   alembic upgrade head
   ```

2. **迁移脚本会自动**:
   - 将所有表的主键从 `id` 改为 `uuid`
   - 更新所有外键关联
   - 保留数据完整性

3. **验证迁移**:
   - 检查所有 API 是否正常工作
   - 验证数据关联是否正确

## 总结

| 特性 | 自增 ID | UUID |
|------|---------|------|
| **类型** | BigInteger (8 字节) | UUID (16 字节) |
| **生成** | 数据库自增 | 应用层生成 |
| **性能** | ⭐⭐⭐⭐⭐ 极快 | ⭐⭐⭐⭐ 快 |
| **安全性** | ⭐⭐ 可被遍历 | ⭐⭐⭐⭐⭐ 无法猜测 |
| **可读性** | ⭐⭐⭐⭐⭐ 简短 | ⭐⭐ 较长 |
| **分布式** | ⭐⭐ 需要协调 | ⭐⭐⭐⭐⭐ 全局唯一 |
| **推荐度** | ❌ 不推荐 | ✅ 推荐 |

**结论**: 使用 UUID 作为主键是现代 Web 应用的最佳实践,提供了更好的安全性、可扩展性和分布式支持。

