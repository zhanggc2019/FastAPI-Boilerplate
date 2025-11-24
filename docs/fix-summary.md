# 用户注册、登录和 API Key 功能修复总结

## 问题描述

在使用过程中遇到了以下问题:

1. **注册功能**: 前端显示 "Registration failed. Please try again." 错误,但没有显示具体的验证错误信息
2. **登录功能**: 前端显示 "Invalid credentials. Please try again" 错误,即使使用正确的凭据也无法登录
3. **API Key 功能**: 后端报错 `TypeError: BaseRepository.__init__() missing 1 required positional argument: 'db_session'`

## 修复内容

### 1. 注册功能修复

#### 前端改进 (`web/src/pages/Register.tsx`)
- 添加了 `fieldErrors` 状态来跟踪每个字段的错误
- 改进了错误处理逻辑,解析后端返回的 `field_errors`
- 为每个输入字段添加了错误消息显示
- 为有错误的输入框添加红色边框
- 添加了密码和用户名的格式提示

#### 后端改进 (`app/schemas/requests/users.py`)
- 修改用户名验证正则表达式,允许字母、数字、下划线和连字符: `^[a-zA-Z0-9_-]+$`
- 将所有密码验证错误消息改为中文

### 2. 登录功能修复

#### 前端修复 (`web/src/pages/Login.tsx`)
- 移除了 FormData 的使用
- 直接发送 JSON 对象: `{ email, password }`
- 改进了错误处理,根据不同的状态码显示不同的错误消息

### 3. API Key 功能修复

#### 问题分析
`ApiKeyRepository` 和 `ApiKeyService` 的初始化和方法调用不符合 `BaseRepository` 的规范:
1. `ApiKeyRepository` 初始化时缺少 `model` 参数
2. `ApiKeyRepository` 的方法接受 `session` 参数,但应该使用 `self.session`
3. `ApiKeyService` 的方法向 repository 传递 `session` 参数,但 repository 已经有了 session
4. `ApiKeyService` 的方法缺少 `@Transactional` 装饰器,导致数据未提交到数据库,返回的对象缺少 `id`、`created_at` 等字段

#### 解决方案

**修复 `app/api/v1/api_keys/api_keys.py`**:
```python
from app.models.api_key import ApiKey

async def get_api_key_service(session: AsyncSession = Depends(get_session)) -> ApiKeyService:
    return ApiKeyService(ApiKeyRepository(model=ApiKey, db_session=session))
```

**修复 `app/repositories/api_key.py`**:
```python
class ApiKeyRepository(BaseRepository[ApiKey]):
    async def get_by_key(self, key: str) -> ApiKey | None:
        stmt = select(ApiKey).where(ApiKey.key == key)
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_user_id(self, user_id: int) -> list[ApiKey]:
        stmt = select(ApiKey).where(ApiKey.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
```

**修复 `app/services/api_key.py`**:
```python
from app.db import Propagation, Transactional

class ApiKeyService:
    @Transactional(propagation=Propagation.REQUIRED)
    async def create_api_key(self, user_id: int, data: ApiKeyCreate) -> ApiKey:
        key = f"sk_{secrets.token_urlsafe(32)}"
        return await self.repository.create({
            "user_id": user_id,
            "key": key,
            "name": data.name,
            "expires_at": data.expires_at
        })

    async def get_user_api_keys(self, user_id: int) -> list[ApiKey]:
        return await self.repository.get_by_user_id(user_id)

    @Transactional(propagation=Propagation.REQUIRED)
    async def revoke_api_key(self, user_id: int, key_id: int) -> bool:
        api_key = await self.repository.get_by(field="id", value=key_id, unique=True)
        if not api_key or api_key.user_id != user_id:
            return False
        await self.repository.delete(api_key)
        return True
```

**修复 `app/api/v1/api_keys/api_keys.py` 路由**:
移除所有路由中的 `session` 参数,因为 repository 已经包含了 session

## 验证规则

### 密码要求
- 最少 8 个字符,最多 64 个字符
- 必须包含至少一个大写字母、小写字母、数字和特殊字符
- 示例: `Test@123`, `MyPass123!`

### 用户名要求
- 3-64 个字符
- 只能包含字母、数字、下划线和连字符
- 示例: `test_user`, `user-123`, `myusername`

### 邮箱要求
- 必须是有效的邮箱格式
- 示例: `user@example.com`

## 测试验证

### 注册功能测试
```bash
curl -X POST http://localhost:8001/api/v1/users/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test100@example.com","username":"testuser100","password":"Test@123"}'
```

### 登录功能测试
```bash
curl -X POST http://localhost:8001/api/v1/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test100@example.com","password":"Test@123"}'
```

## 文件修改列表

### 后端文件
1. `app/schemas/requests/users.py` - 优化验证规则和错误消息
2. `app/api/v1/api_keys/api_keys.py` - 修复 repository 初始化和路由参数
3. `app/repositories/api_key.py` - 修复方法签名,使用 self.session
4. `app/services/api_key.py` - 修复方法签名,移除 session 参数

### 前端文件
1. `web/src/pages/Register.tsx` - 改进错误处理和显示
2. `web/src/pages/Login.tsx` - 修复请求格式和错误处理

## API Key 页面用户体验改进

### 前端改进 (`web/src/pages/Dashboard.tsx`)

**新增功能**:
1. **API Key 隐藏/显示**
   - 默认隐藏 API Key,显示为 `sk_xxxxx••••••••••••••••••••••••`
   - 点击眼睛图标可以切换显示/隐藏
   - 使用 `Eye` 和 `EyeOff` 图标

2. **一键复制功能**
   - 点击复制按钮可以复制完整的 API Key 到剪贴板
   - 复制成功后显示绿色对勾图标 2 秒
   - 使用 `Copy` 和 `Check` 图标

3. **必填字段提示**
   - API Key 名称标签显示红色星号 (*)
   - 输入框有示例文本: "例如: Production API Key"
   - 帮助文本: "为您的 API Key 设置一个易于识别的名称"

4. **输入验证**
   - 空值时显示错误: "请输入 API Key 名称"
   - 错误时输入框显示红色边框
   - 空值时禁用创建按钮

5. **其他改进**
   - 创建时显示加载状态: "创建中..."
   - 删除前显示确认对话框
   - 空列表时显示友好提示
   - 所有按钮都有 tooltip 提示

## 总结

✅ 正确显示验证错误
✅ 提供清晰的中文错误消息
✅ 使用正确的请求格式
✅ 提供良好的用户体验
✅ 支持更灵活的用户名格式
✅ API Key 功能正常工作
✅ Repository 模式正确实现
✅ API Key 默认隐藏,保护安全
✅ 一键复制功能,方便使用
✅ 必填字段清晰标注

所有功能都已通过测试验证,可以正常使用!

