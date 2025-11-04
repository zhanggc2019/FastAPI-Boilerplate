# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Project Setup
```bash
# Install dependencies with uv
uv sync

# Start database and Redis containers
docker-compose up -d

# Copy and configure environment
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
make migrate

# Start the development server
make run
# or
uv run python main.py
```

### Database Operations
```bash
# Create new migration
make generate-migration

# Apply migrations
make migrate

# Rollback one migration
make rollback

# Reset all migrations
make reset-database
```

### Code Quality
```bash
# Format code (Black + iSort)
make format

# Lint code
make lint

# Check formatting without fixing
make check-format

# Run both format check and lint
make check
```

### Testing and Background Tasks
```bash
# Run tests
make test

# Start Celery worker
make celery-worker
```

## Architecture Overview

This is a **layered FastAPI application** following clean architecture with four main layers:

### Core Framework (`app/core/`)
Contains boilerplate code and infrastructure:
- **Configuration**: Centralized settings in `app/core/config.py` using Pydantic Settings
- **Database**: SQLAlchemy 2.0+ with async support, session management in `app/db/`
- **Security**: JWT authentication and row-level access control in `app/core/security/`
- **Caching**: Redis implementation in `app/core/cache/`
- **Factory**: Dependency injection system in `app/core/factory/`
- **Repository Pattern**: Base repository in `app/repositories/`

### Application Logic (`app/`)
Business logic layer:
- **Models**: SQLAlchemy ORM models in `app/models/`
- **Repositories**: Data access layer in `app/repositories/`
- **Controllers**: Business logic in `app/controllers/`
- **Schemas**: Pydantic models for validation in `app/schemas/`

### API Layer (`api/`)
RESTful endpoints organized by version:
- **Versioning**: URL-based (`/api/v1/`)
- **Authentication**: Bearer token required for protected routes
- **Auto-documentation**: OpenAPI/Swagger at `/docs`

### Background Tasks (`worker/`)
Celery background task configuration and implementations.

## Key Development Patterns

### Repository Pattern
Every model has a corresponding repository inheriting from `BaseRepository[Model]`:
```python
class UserRepository(BaseRepository[User]):
    async def get_by_email(self, email: str):
        return await select(User).filter(User.email == email).gino.first()
```

### Dependency Injection
Repositories and services are injected through the `Factory` class in `app/core/factory/factory.py`.

### Session Management
- **Automatic sessions**: Handled by middleware and `get_session` dependency
- **Transactions**: Use `@Transactional()` decorator for transactional operations
- **Isolated sessions**: Use `@standalone_session` decorator for separate sessions

### Row-Level Access Control
Inspired by fastapi-permissions:
```python
def get_user_principals(user: User = Depends(get_current_user)):
    return [UserPrincipal(user.id)]

Permission = AccessControl(get_user_principals)

@router.get("/users/{user_id}")
def get_user(assert_access = Permission("view")):
    assert_access(user)
```

### Caching
Use Redis caching with decorators:
```python
@Cache.cached(prefix="user", ttl=60)
def get_user(user_id: int):
    ...
```

## Configuration

### Environment Setup
Key configuration files:
- **`.env`**: Environment variables (copy from `.env.example`)
- **`pyproject.toml`**: Project dependencies and tool configuration
- **`uv.lock`**: uv lock file for dependency resolution
- **`docker-compose.yml`**: Database (PostgreSQL), Redis, and RabbitMQ services

### Code Quality Tools
- **Package Management**: uv for fast dependency installation and resolution
- **Formatting**: Black + iSort (120 character line length)
- **Linting**: Pylint + Ruff
- **Type checking**: Pyright (disabled in current config)
- **Python version**: 3.12+

## Request Processing Pipeline

1. **Correlation ID middleware** - Request tracking
2. **Response logging middleware** - Request/response logging
3. **Access middleware** - Access logging
4. **SQLAlchemy middleware** - Database session management
5. **Authentication middleware** - JWT validation
6. **Operation logging middleware** - Business operation tracking
7. **Route handler** - Business logic execution

## Database

### ORM
- **SQLAlchemy 2.0+** with async support
- **Alembic** for migrations
- **Connection pooling** configured

### Model Definition
Models inherit from `Base` in `app/db/session.py` and include:
- Table definitions with `__tablename__`
- Column definitions with proper types
- Relationships defined with SQLAlchemy relationships
- Access control lists via `__acl__()` method for row-level permissions

## Testing

- **Framework**: pytest with async support
- **Test database**: Separate PostgreSQL instance
- **Test locations**: `tests/` directory
- **Coverage**: All endpoints, core components, and complex inner components

## Development Notes

- **Async patterns**: Use `async/await` throughout the codebase
- **Error handling**: Proper HTTPException handling in API routes
- **Logging**: Structured logging with correlation IDs
- **API documentation**: Auto-generated from type hints and Pydantic models
- **Environment variables**: All sensitive configuration via environment variables
