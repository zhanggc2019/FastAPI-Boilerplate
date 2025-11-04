from app.models import Task, User
from app.repositories import TaskRepository, UserRepository
from app.services import AuthService, TaskService, UserService


class ServiceOverrides:
    """测试环境下用于覆盖服务实例的帮助类。"""

    def __init__(self, db_session):
        self.db_session = db_session

    def user_service(self) -> UserService:
        """构建用户服务，用于测试覆盖。"""
        return UserService(UserRepository(model=User, session=self.db_session))

    def task_service(self) -> TaskService:
        """构建任务服务，用于测试覆盖。"""
        return TaskService(TaskRepository(model=Task, session=self.db_session))

    def auth_service(self) -> AuthService:
        """构建认证服务，用于测试覆盖。"""
        return AuthService(UserRepository(model=User, session=self.db_session))

