from datetime import datetime
from typing import Any, Protocol

from starlette_context.ctx import _Context, context
from starlette_context.errors import ContextDoesNotExistError


class TypedContextProtocol(Protocol):
    perf_time: float
    start_time: datetime

    ip: str
    country: str | None
    region: str | None
    city: str | None

    user_agent: str
    os: str | None
    browser: str | None
    device: str | None

    permission: str | None


class TypedContext(TypedContextProtocol, _Context):
    def __getattr__(self, name: str) -> Any:
        try:
            return context.get(name)
        except ContextDoesNotExistError:
            # Context not available (outside request cycle)
            return None

    def __setattr__(self, name: str, value: Any) -> None:
        try:
            context[name] = value
        except ContextDoesNotExistError:
            # Context not available (outside request cycle), ignore silently
            pass


ctx = TypedContext()
