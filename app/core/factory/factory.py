from functools import partial

from fastapi import Depends

from app.db import get_session
from app.models import Task, User
from app.repositories import TaskRepository, UserRepository
from app.services import AuthService, TaskService, UserService


class Factory:
    """Service and repository factory for dependency injection."""

    # Repositories
    task_repository = partial(TaskRepository, Task)
    user_repository = partial(UserRepository, User)

    def get_user_service(self, db_session=None):
        if db_session is None:
            db_session = Depends(get_session)
        return UserService(user_repository=self.user_repository(db_session=db_session))

    def get_task_service(self, db_session=None):
        if db_session is None:
            db_session = Depends(get_session)
        return TaskService(task_repository=self.task_repository(db_session=db_session))

    def get_auth_service(self, db_session=None):
        if db_session is None:
            db_session = Depends(get_session)
        return AuthService(
            user_repository=self.user_repository(db_session=db_session),
        )
