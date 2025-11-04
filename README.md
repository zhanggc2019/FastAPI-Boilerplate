## FastAPI Production Template

A scalable and production ready boilerplate for FastAPI

### Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Installation Guide](#installation-guide)
- [Usage Guide](#usage-guide)
- [Advanced Usage](#advanced-usage)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)

### Project Overview

This boilerplate follows a layered architecture that includes a model layer, a repository layer, a service layer, and an API layer. Its directory structure is designed to isolate boilerplate code within the core directory, which requires minimal attention, thereby facilitating quick and easy feature development. The directory structure is also generally very predictable. The project's primary objective is to offer a production-ready boilerplate with a better developer experience and readily available features. It also has some widely used features like authentication, authorization, database migrations, type checking, etc which are discussed in detail in the [Features](#features) section.

### Features

- Python 3.12+ support
- SQLAlchemy 2.0+ support
- Asynchoronous capabilities
- Database migrations using Alembic
- Basic Authentication using JWT
- Row Level Access Control for permissions
- Redis for caching
- Celery for background tasks
- Testing suite
- Type checking using mypy
- Dockerized database and redis
- Readily available CRUD operations
- Linting using pylint
- Formatting using black

### Installation Guide

You need following to run this project:

- Python 3.12
- [Docker with Docker Compose](https://docs.docker.com/compose/install/)
- [uv](https://github.com/astral-sh/uv) - Fast Python package installer and resolver

I use [asdf](https://asdf-vm.com/#/) to manage my python versions. You can use it too. However, it is only supported on Linux and macOS. For Windows, you can use something like pyenv.

Once you have installed the above and have cloned the repository, you can follow the following steps to get the project up and running:

1. Create a virtual environment and install dependencies using uv:

```bash
uv sync
```

This will create a virtual environment and install all dependencies automatically.

2. Run the database and redis containers:

```bash
docker-compose up -d
```

3. Copy the `.env.example` file to `.env` and update the values as per your needs.

4. Run the migrations:

```bash
make migrate
```

5. Run the server:

```bash
make run
```

or on Windows:

```powershell
pwsh scripts.ps1 start
```

The server should now be running on `http://localhost:8000` and the API documentation should be available at `http://localhost:8000/docs`.

### Usage Guide

The project is designed to be modular and scalable. All runtime code now lives under `app/` and is organised by responsibility:

- `app/core`: cross-cutting infrastructure such as configuration, logging, security, middlewares, caching, and the FastAPI bootstrap helpers.
- `app/api`: versioned FastAPI routers and dependency definitions.
- `app/services`: business services that encapsulate domain logic and orchestrate repositories.
- `app/repositories`: persistence layer built on top of SQLAlchemy sessions.
- `app/models`: SQLAlchemy models registered on the shared metadata.
- `app/schemas`: Pydantic request/response contracts.
- `app/db`: database configuration, async engine/session factories, and transactional helpers.
- `app/common`: shared domain helpers (enums, pagination, dataclasses, timezone utilities, etc.).
- `app/worker`: Celery bootstrap and task entrypoints.
- `docs/examples`: optional demo routers that are not mounted by default.

### Advanced Usage

The boilerplate contains a lot of features some of which are used in the application and some of which are not. The following sections describe the features in detail.

#### Database Migrations

The migrations are handled by Alembic. The migrations are stored in the `migrations` directory. To create a new migration, you can run the following command:

```bash
make generate-migration
```

It will ask you for a message for the migration. Once you enter the message, it will create a new migration file in the `migrations` directory. You can then run the migrations using the following command:

```bash
make migrate
```

If you need to downgrade the database or reset it. You can use `make rollback` and `make reset-database` respectively.

#### Authentication

The authentication used is basic implementation of JWT with bearer token. When the `bearer` token is supplied in the `Authorization` header, the token is verified and the user is automatically authenticated by setting `request.user.id` using middleware. To use the user model in any endpoint you can use the `get_current_user` dependency. If for any endpoint you want to enforce authentication, you can use the `AuthenticationRequired` dependency. It will raise a `HTTPException` if the user is not authenticated.

#### Row Level Access Control

The boilerplate contains a custom row level permissions management module. It is inspired by [fastapi-permissions](https://github.com/holgi/fastapi-permissions). It is located in `app/core/security/access_control.py`. You can use this to enforce different permissions for different models. The module operates based on `Principals` and `permissions`. Every user has their own set of principals which need to be set using a function. Check `app/api/deps/permissions.py` for an example. The principals are then used to check the permissions for the user. The permissions need to be defined at the model level. Check `app/models/user.py` for an example. Then you can use the dependency directly in the route to raise a `HTTPException` if the user does not have the required permissions. Below is an incomplete example:

```python
from fastapi import APIRouter, Depends
from app.core.security.access_control import AccessControl, UserPrincipal, RolePrincipal, Allow
from app.db import Base

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

#### Caching

You can directly use the `Cache.cached` decorator from `app.core.cache`. Example

```python
from app.core.cache import Cache

@Cache.cached(prefix="user", ttl=60)
def get_user(user_id: int):
    ...
```

#### Celery

The celery worker is already configured for the app. You can add your tasks in `worker/` to run the celery worker, you can run the following command:

```bash
make celery-worker
```

#### Session Management

The sessions are already handled by the middleware and `get_session` dependency which injected into the repositories through fastapi dependency injection inside the `Factory` class in `app/core/factory/factory.py`. There is also `Transactional` decorator which can be used to wrap the functions which need to be executed in a transaction. Example:

```python
@Transactional()
async def some_mutating_function():
    ...
```

Note: The decorator already handles the commit and rollback of the transaction. You do not need to do it manually.

If for any case you need an isolated sessions you can use `standalone_session` decorator from `app.db`. Example:

```python
@standalone_session
async def do_something():
    ...
```

#### Repository Pattern

The boilerplate uses the repository pattern. Every model has a repository and all of them inherit `base` repository from `app/repositories/base.py`. The repositories are located in `app/repositories`. The repositories are injected into the services inside the `Factory` class in `app/core/factory/factory.py`.

The base repository has the basic crud operations. All customer operations can be added to the specific repository. Example:

```python
from app.repositories import BaseRepository
from app.models.user import User
from sqlalchemy.sql.expression import select

class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str):
        return await select(User).filter(User.email == email).gino.first()

```

To facilitate easier access to queries with complex joins, the `BaseRepository` class has a `_query` function (along with other handy functions like `_all()` and `_one_or_none()`) which can be used to write compplex queries very easily. Example:

```python
async def get_user_by_email_join_tasks(email: str):
    query = await self._query(join_)
    query = query.filter(User.email == email)
    return await self._one_or_none(query)
```

Note: For every join you want to make you need to create a function in the same repository with pattern `_join_{name}`. Example: `_join_tasks` for `tasks`. Example:

```python
async def _join_tasks(self, query: Select) -> Select:
    return query.options(joinedload(User.tasks))
```

#### Services

Kind of to repositories, every logical unit of the application has a service layer component. Each service depends on a primary repository injected through the factory. The services are located in `app/services`.

These services contain all the business logic of the application. Check `app/services/auth.py` for an example.

#### Schemas

The schemas are located in `app/schemas`. The schemas are used to validate the request body and response body. The schemas are also used to generate the OpenAPI documentation. The schemas are inherited from `BaseModel` from `pydantic`. The schemas are primarily isolated into `requests` and `responses` which are pretty self explainatory.

#### Formatting

You can use `make format` to format the code using `ruff format`.

On Windows:

```powershell
pwsh scripts.ps1 format
```

#### Linting

You can use `make lint` to lint the code using `pylint`.

On Windows:

```powershell
pwsh scripts.ps1 lint
```

#### Testing

The project contains tests for all endpoints, some of the logical components like `JWTHander` and `AccessControl` and an example of testing complex inner components like `BaseRepository`. The tests are located in `tests/`. You can run the tests using `make test`.

On Windows:

```powershell
pwsh scripts.ps1 test
```

## Contributing

Contributions are higly welcome. Please open an issue or a PR if you want to contribute.

## License

This project is licensed under the terms of the MIT license. See the LICENSE file.

## Acknowledgements

- This project uses several components from [teamhide/fastapi-boilerplate](https://github.com/teamhide/fastapi-boilerplate)
- The row level access control is inspired by [fastapi-permissions](https://github.com/holgi/fastapi-permissions)
- CRUD pattern is inspired by [full-stack-fastapi-postgresql](https://github.com/tiangolo/full-stack-fastapi-postgresql)
