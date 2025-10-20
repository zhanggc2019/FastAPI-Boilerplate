## FastAPI 生产级模板

一个可扩展且生产就绪的 FastAPI 项目模板

### 目录

- [项目概述](#项目概述)
- [功能特性](#功能特性)
- [安装指南](#安装指南)
- [使用指南](#使用指南)
- [高级用法](#高级用法)
- [贡献指南](#贡献指南)
- [许可证](#许可证)
- [致谢](#致谢)

### 项目概述

本项目模板采用分层架构，包含模型层、仓储层、控制器层和API层。其目录结构设计旨在将样板代码隔离在 `core` 目录中，该目录需要最少的关注，从而促进快速便捷的功能开发。项目的目录结构也非常可预测。该项目的主要目标是提供一个具有更好开发体验和现成功能的生产就绪模板。它还包含一些广泛使用的功能，如身份验证、授权、数据库迁移、类型检查等，这些将在[功能特性](#功能特性)部分详细讨论。

### 功能特性

- Python 3.12+ 支持
- SQLAlchemy 2.0+ 支持
- 异步编程能力
- 使用 Alembic 进行数据库迁移
- 基于 JWT 的基础身份验证
- 行级访问控制权限管理
- Redis 缓存支持
- Celery 后台任务
- 测试套件
- 使用 mypy 进行类型检查
- 数据库和 redis 的 Docker 容器化
- 现成的 CRUD 操作
- 使用 pylint 进行代码检查
- 使用 black 进行代码格式化

### 安装指南

运行此项目需要以下工具：

- Python 3.12
- [Docker 和 Docker Compose](https://docs.docker.com/compose/install/)
- [uv](https://github.com/astral-sh/uv) - 快速的 Python 包安装器和解析器

我使用 [asdf](https://asdf-vm.com/#/) 来管理 Python 版本。你也可以使用它。但是，它只在 Linux 和 macOS 上受支持。对于 Windows，你可以使用 pyenv 等工具。

安装完上述工具并克隆仓库后，你可以按照以下步骤启动项目：

1. 使用 uv 创建虚拟环境并安装依赖：

```bash
uv sync
```

这将自动创建虚拟环境并安装所有依赖。

2. 启动数据库和 Redis 容器：

```bash
docker-compose up -d
```

3. 将 `.env.example` 文件复制为 `.env` 并根据需要更新配置值。

4. 运行数据库迁移：

```bash
make migrate
```

5. 启动服务器：

```bash
make run
```

或者在 Windows 上：

```powershell
pwsh scripts.ps1 start
```

服务器现在应该在 `http://localhost:8000` 上运行，API 文档可在 `http://localhost:8000/docs` 访问。

### 使用指南

该项目设计为模块化和可扩展的。项目中有 3 个主要目录：

1. `core`：此目录包含项目的核心部分。它包含大部分样板代码，如安全依赖、数据库连接、配置、中间件等。它还包含模型、仓储和控制器的基类。`core` 目录设计得尽可能精简，通常需要最少的关注。总的来说，`core` 目录设计得尽可能通用，可以在任何项目中使用。在构建额外功能时，你可能完全不需要修改此目录，除了在 `core/factory.py` 的 `Factory` 类中添加更多控制器。

2. `app`：此目录包含实际的应用程序代码。它包含应用程序的模型、仓储、控制器和模式。这是你在构建功能时将花费大部分时间的目录。该目录有以下子目录：

   - `models` 在这里添加新表
   - `repositories` 为每个模型创建一个仓储。在这里添加模型的 CRUD 操作
   - `controllers` 为应用程序的每个逻辑单元创建一个控制器。在这里添加应用程序的业务逻辑
   - `schemas` 这里添加应用程序的模式。模式用于数据的验证和序列化/反序列化

3. `api`：此目录包含应用程序的 API 层。它包含 API 路由器，是你添加 API 端点的地方。

### 高级用法

该模板包含许多功能，其中一些在应用程序中使用，一些没有。以下部分详细描述了这些功能。

#### 数据库迁移

迁移由 Alembic 处理。迁移存储在 `migrations` 目录中。要创建新迁移，可以运行以下命令：

```bash
make generate-migration
```

它会要求你输入迁移消息。输入消息后，它将在 `migrations` 目录中创建一个新的迁移文件。然后你可以使用以下命令运行迁移：

```bash
make migrate
```

如果需要降级数据库或重置它，你可以分别使用 `make rollback` 和 `make reset-database`。

#### 身份验证

使用的身份验证是基于 bearer token 的 JWT 基础实现。当在 `Authorization` 标头中提供 `bearer` token 时，token 被验证，用户通过使用中间件设置 `request.user.id` 自动进行身份验证。要在任何端点中使用用户模型，你可以使用 `get_current_user` 依赖。如果要对任何端点强制执行身份验证，可以使用 `AuthenticationRequired` 依赖。如果用户未通过身份验证，它将引发 `HTTPException`。

#### 行级访问控制

该模板包含一个自定义的行级权限管理模块。它受到 [fastapi-permissions](https://github.com/holgi/fastapi-permissions) 的启发。它位于 `core/security/access_control.py`。你可以使用它为不同的模型强制执行不同的权限。该模块基于 `Principals` 和 `permissions` 运行。每个用户都有自己的 principal 集合，需要使用函数设置。检查 `core/fastapi/dependencies/permissions.py` 中的示例。然后这些 principal 用于检查用户的权限。权限需要在模型级别定义。检查 `app/models/user.py` 中的示例。然后你可以直接在路由中使用依赖，如果用户没有所需权限，它将引发 `HTTPException`。下面是一个不完整的示例：

```python
from fastapi import APIRouter, Depends
from core.security.access_control import AccessControl, UserPrincipal, RolePrincipal, Allow
from core.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)
    role = Column(String)

    def __acl__(self):
        return [
            (Allow, UserPrincipal(self.id), "view"),
            (Allow, RolePrincipal("admin"), "delete"),
        ]

def get_user_principals(user: User = Depends(get_current_user)):
    return [UserPrincipal(user.id)]

Permission = AccessControl(get_user_principals)

router = APIRouter()

@router.get("/users/{user_id}")
def get_user(user_id: int, user: User = get_user(user_id), assert_access = Permission("view")):
    assert_access(user)
    return user
```

#### 缓存

你可以直接使用 `core.cache` 中的 `Cache.cached` 装饰器。示例

```python
from core.cache import Cache

@Cache.cached(prefix="user", ttl=60)
def get_user(user_id: int):
    ...
```

#### Celery

Celery worker 已经为应用程序配置好了。你可以在 `worker/` 中添加你的任务。要运行 celery worker，可以运行以下命令：

```bash
make celery-worker
```

#### 会话管理

会话已经由中间件和 `get_session` 依赖处理，后者通过 `core/factory.py` 中的 `Factory` 类中的 FastAPI 依赖注入注入到仓储中。还有 `Transactional` 装饰器，可用于包装需要在事务中执行的函数。示例：

```python
@Transactional()
async def some_mutating_function():
    ...
```

注意：装饰器已经处理了事务的提交和回滚。你不需要手动执行。

如果对于任何情况你需要独立的会话，可以使用 `core.database` 中的 `standalone_session` 装饰器。示例：

```python
@standalone_session
async def do_something():
    ...
```

#### 仓储模式

该模板使用仓储模式。每个模型都有一个仓储，所有仓储都继承自 `core/repository` 中的 `base` 仓储。仓储位于 `app/repositories`。仓储在 `core/factory/factory.py` 中的 `Factory` 类内部注入到控制器中。

基础仓储有基本的 CRUD 操作。所有客户操作都可以添加到特定仓储。示例：

```python
from core.repository import BaseRepository
from app.models.user import User
from sqlalchemy.sql.expression import select

class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str):
        return await select(User).filter(User.email == email).gino.first()
```

为了便于更容易地访问具有复杂连接的查询，`BaseRepository` 类有一个 `_query` 函数（以及其他方便的函数，如 `_all()` 和 `_one_or_none()`），可以用来非常容易地编写复杂查询。示例：

```python
async def get_user_by_email_join_tasks(email: str):
    query = await self._query(join_)
    query = query.filter(User.email == email)
    return await self._one_or_none(query)
```

注意：对于每个你想要进行的连接，你需要在同一个仓储中创建一个模式为 `_join_{name}` 的函数。示例：`tasks` 的 `_join_tasks`。示例：

```python
async def _join_tasks(self, query: Select) -> Select:
    return query.options(joinedload(User.tasks))
```

#### 控制器

与仓储类似，应用程序的每个逻辑单元都有一个控制器。控制器还有一个主仓储，它被注入其中。控制器位于 `app/controllers`。

这些控制器包含应用程序的所有业务逻辑。检查 `app/controllers/auth.py` 中的示例。

#### 模式

模式位于 `app/schemas`。模式用于验证请求体和响应体。模式也用于生成 OpenAPI 文档。模式继承自 `pydantic` 的 `BaseModel`。模式主要隔离为 `requests` 和 `responses`，这是不言自明的。

#### 格式化

你可以使用 `make format` 来使用 `ruff format` 格式化代码。

在 Windows 上：

```powershell
pwsh scripts.ps1 format
```

#### 代码检查

你可以使用 `make lint` 来使用 `pylint` 检查代码。

在 Windows 上：

```powershell
pwsh scripts.ps1 lint
```

#### 测试

该项目包含所有端点的测试、一些逻辑组件（如 `JWTHander` 和 `AccessControl`）的测试，以及测试复杂内部组件（如 `BaseRepository`）的示例。测试位于 `tests/`。你可以使用 `make test` 运行测试。

在 Windows 上：

```powershell
pwsh scripts.ps1 test
```

## 贡献指南

贡献是高度欢迎的。如果你想贡献，请打开 issue 或 PR。

## 许可证

本项目根据 MIT 许可证的条款获得许可。参见 LICENSE 文件。

## 致谢

- 本项目使用了 [teamhide/fastapi-boilerplate](https://github.com/teamhide/fastapi-boilerplate) 的几个组件
- 行级访问控制受到 [fastapi-permissions](https://github.com/holgi/fastapi-permissions) 的启发
- CRUD 模式受到 [full-stack-fastapi-postgresql](https://github.com/tiangolo/full-stack-fastapi-postgresql) 的启发