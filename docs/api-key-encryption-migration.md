# API Key 加密存储迁移文档

## 📋 概述

将 API Key 表从使用 `uuid` 作为主键改为使用**加密后的 `key`** 作为主键，实现以下目标：

1. ✅ **使用 `key` 作为主键** - 移除冗余的 `uuid` 字段
2. ✅ **加密存储 `key`** - 数据库中存储加密后的 key
3. ✅ **显示时解密** - API 返回时解密 key 供用户查看
4. ✅ **安全的删除操作** - 使用加密后的 key 作为删除参数

## 🔧 技术实现

### 1. 加密工具类

**文件**: `app/core/security/encryption.py`

使用 **Fernet 对称加密**（基于 AES-128-CBC）:

```python
from cryptography.fernet import Fernet

class KeyEncryption:
    def encrypt(self, plaintext: str) -> str:
        """加密字符串"""
        encrypted_bytes = self.cipher.encrypt(plaintext.encode())
        return encrypted_bytes.decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """解密字符串"""
        decrypted_bytes = self.cipher.decrypt(ciphertext.encode())
        return decrypted_bytes.decode()
```

**加密密钥配置**:
- 开发环境: 使用固定密钥（不安全，仅用于开发）
- 生产环境: 必须在 `.env` 中配置 `ENCRYPTION_KEY`

### 2. 数据库模型

**文件**: `app/models/api_key.py`

```python
class ApiKey(Base, TimestampMixin):
    __tablename__ = "api_keys"
    
    # 使用加密后的 key 作为主键
    key = Column(String, primary_key=True, nullable=False)
    user_uuid = Column(UUID(as_uuid=True), ForeignKey("users.uuid"), nullable=False)
    name = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=True)
```

**数据库表结构**:
```sql
CREATE TABLE api_keys (
    key VARCHAR NOT NULL PRIMARY KEY,  -- 加密后的 key
    user_uuid UUID NOT NULL REFERENCES users(uuid),
    name VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT true,
    expires_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 3. 服务层逻辑

**文件**: `app/services/api_key.py`

**创建 API Key**:
```python
async def create_api_key(self, user_uuid: UUID, data: ApiKeyCreate) -> ApiKey:
    # 1. 生成明文 key
    plaintext_key = f"sk_{secrets.token_urlsafe(32)}"
    
    # 2. 加密后存储
    encrypted_key = key_encryption.encrypt(plaintext_key)
    
    api_key = await self.repository.create({
        "key": encrypted_key,  # 存储加密后的 key
        "user_uuid": user_uuid,
        "name": data.name,
    })
    
    # 3. 附加明文 key (仅用于首次显示)
    api_key._plaintext_key = plaintext_key
    return api_key
```

**获取 API Keys**:
```python
async def get_user_api_keys(self, user_uuid: UUID) -> list[ApiKey]:
    encrypted_keys = await self.repository.get_by_user_uuid(user_uuid)
    
    # 解密所有 key
    for api_key in encrypted_keys:
        api_key._plaintext_key = key_encryption.decrypt(api_key.key)
    
    return encrypted_keys
```

**删除 API Key**:
```python
async def revoke_api_key(self, user_uuid: UUID, encrypted_key: str) -> bool:
    # 使用加密后的 key 查询
    api_key = await self.repository.get_by(field="key", value=encrypted_key, unique=True)
    if not api_key or api_key.user_uuid != user_uuid:
        return False
    
    await self.repository.delete(api_key)
    return True
```

### 4. API 响应格式

**Schema**: `app/schemas/api_key.py`

```python
class ApiKeyResponse(ApiKeyBase):
    key: str  # 加密后的 key (用于删除等操作)
    plaintext_key: Optional[str] = None  # 明文 key (用于显示)
    is_active: bool
    created_at: datetime
    user_uuid: UUID
```

**API 响应示例**:
```json
{
  "key": "gAAAAABpJAbeIXS2bp1kkKe7wFeklvmg3vx7Ph2IAdqwrKirCm...",
  "plaintext_key": "sk_ptGlv7kp2QzGzWjPlHByuJr_RGYkm7eYgkKuBZiGHXc",
  "name": "Test API Key",
  "is_active": true,
  "created_at": "2025-11-24T05:29:58.467932",
  "user_uuid": "5dd1c7c3-16de-42b1-90e1-90b9b68475f1"
}
```

### 5. 前端显示

**文件**: `web/src/pages/Dashboard.tsx`

```typescript
interface ApiKey {
  key: string;  // 加密后的 key (用于删除)
  plaintext_key: string;  // 明文 key (用于显示和复制)
  name: string;
  created_at: string;
  is_active: boolean;
  user_uuid: string;
}

// 显示明文 key
const displayKey = apiKey.plaintext_key || apiKey.key;

// 删除时使用加密后的 key
await api.delete(`/api-keys/${encodeURIComponent(apiKey.key)}`);
```

## 📊 数据迁移

### 迁移步骤

1. **备份现有数据**:
```sql
CREATE TABLE api_keys_backup AS SELECT * FROM api_keys;
```

2. **删除旧表并创建新表**:
```bash
psql -f scripts/migrate_api_key_to_encrypted.sql
```

3. **迁移数据**:
```bash
python scripts/migrate_api_keys_data.py
```

### 迁移结果

✅ 成功迁移 **7 条记录**

```
找到 7 条记录需要迁移
  迁移 1/7: Test API Key (user: 5dd1c7c3-16de-42b1-90e1-90b9b68475f1)
  迁移 2/7: api (user: b3e760ea-c21c-4d54-be9b-5679ec21de69)
  ...
✅ 成功迁移 7 条记录!
```

## 🔒 安全性分析

### 优势

1. **数据库加密** 🔐
   - API Key 在数据库中以密文存储
   - 即使数据库泄露，攻击者也无法直接使用 key

2. **URL 安全** 🌐
   - 删除操作使用加密后的 key
   - 日志中不会记录明文 key

3. **简化设计** 📐
   - 移除了冗余的 `uuid` 字段
   - `key` 本身就是唯一标识符

### 注意事项

⚠️ **加密密钥管理**:
- 生产环境必须配置强加密密钥
- 密钥丢失将导致所有 API Key 无法解密
- 建议使用密钥管理服务（如 AWS KMS、HashiCorp Vault）

⚠️ **性能影响**:
- 每次查询需要解密 key
- 对于大量 API Key 的场景，可能有性能影响

## 📝 API 端点

### 创建 API Key
```http
POST /api/v1/api-keys
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "My API Key"
}
```

**响应**: 包含 `plaintext_key`（仅此一次显示）

### 获取 API Keys
```http
GET /api/v1/api-keys
Authorization: Bearer <token>
```

**响应**: 所有 key 都包含解密后的 `plaintext_key`

### 删除 API Key
```http
DELETE /api/v1/api-keys/{encrypted_key}
Authorization: Bearer <token>
```

**参数**: `encrypted_key` - 从列表接口获取的加密 key

## ✅ 测试验证

所有功能已测试通过:
- ✅ 用户登录
- ✅ 创建 API Key (返回明文 key)
- ✅ 获取 API Keys (所有 key 已解密)
- ✅ 删除 API Key (使用加密 key)
- ✅ 前端显示明文 key
- ✅ 前端复制明文 key

## 🎉 总结

成功实现了 API Key 的加密存储方案:
- 数据库中存储加密后的 key
- API 返回时自动解密
- 前端显示明文 key
- 删除操作使用加密 key
- 提升了系统安全性

