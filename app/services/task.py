from uuid import UUID
from app.models import Task
from app.repositories import TaskRepository
from app.services.base import BaseService
from app.db.transactional import Propagation, Transactional
from app.core.exceptions import (
    DataValidationException,
    ResourceNotFoundException,
    InvalidOperationException,
)


class TaskService(BaseService[Task]):
    """任务领域的业务服务。"""

    def __init__(self, task_repository: TaskRepository):
        super().__init__(model=Task, repository=task_repository)
        self.task_repository = task_repository

    async def get_by_author_uuid(self, author_uuid: UUID) -> list[Task]:
        """
        Returns a list of tasks based on author_uuid.

        :param author_uuid: The author uuid.
        :return: A list of tasks.
        """
        if not author_uuid:
            raise DataValidationException("Invalid author UUID")

        return await self.task_repository.get_by_author_uuid(author_uuid)

    @Transactional(propagation=Propagation.REQUIRED)
    async def add(self, title: str, description: str, author_uuid: UUID) -> Task:
        """
        Adds a task.

        :param title: The task title.
        :param description: The task description.
        :param author_uuid: The author uuid.
        :return: The task.
        """
        # 参数验证
        if not title or len(title.strip()) == 0:
            raise DataValidationException("Task title cannot be empty")

        if len(title) > 200:
            raise DataValidationException("Task title must be less than 200 characters")

        if description and len(description) > 1000:
            raise DataValidationException("Task description must be less than 1000 characters")

        if not author_uuid:
            raise DataValidationException("Invalid author UUID")

        # 验证作者是否存在（这里假设有用户控制器或用户服务）
        # 在实际应用中，应该注入用户服务来验证作者存在性
        # 这里暂时跳过这个验证，保持与现有代码的兼容性

        return await self.task_repository.create(
            {
                "title": title.strip(),
                "description": description.strip() if description else None,
                "task_author_uuid": author_uuid,
            }
        )

    @Transactional(propagation=Propagation.REQUIRED)
    async def complete(self, task_uuid: UUID) -> Task:
        """
        Completes a task.

        :param task_uuid: The task uuid.
        :return: The task.
        """
        if not task_uuid:
            raise DataValidationException("Invalid task UUID")

        # 检查任务是否存在
        task = await self.task_repository.get_by("uuid", task_uuid, unique=True)
        if not task:
            raise ResourceNotFoundException(f"Task with UUID {task_uuid} not found")

        # 检查任务是否已经完成
        if task.is_completed:
            raise InvalidOperationException("Task is already completed")

        return await self.task_repository.set_completed(task_uuid, True)

    async def get_task_by_uuid(self, task_uuid: UUID) -> Task:
        """
        Get task by UUID with validation.

        :param task_uuid: The task uuid.
        :return: The task.
        """
        if not task_uuid:
            raise DataValidationException("Invalid task UUID")

        task = await self.task_repository.get_by("uuid", task_uuid, unique=True)
        if not task:
            raise ResourceNotFoundException(f"Task with UUID {task_uuid} not found")

        return task

    async def delete_task(self, task_uuid: UUID) -> bool:
        """
        Delete task with validation.

        :param task_uuid: The task uuid.
        :return: True if deleted successfully.
        """
        if not task_uuid:
            raise DataValidationException("Invalid task UUID")

        # 检查任务是否存在
        task = await self.task_repository.get_by("uuid", task_uuid, unique=True)
        if not task:
            raise ResourceNotFoundException(f"Task with UUID {task_uuid} not found")

        # 检查任务是否已经完成（可以根据业务规则决定是否允许删除已完成的任务）
        if task.is_completed:
            raise InvalidOperationException("Cannot delete completed task")

        await self.task_repository.delete(task)
        return True

    async def update_task(self, task_uuid: UUID, update_data: dict) -> Task:
        """
        Update task with validation.

        :param task_uuid: The task uuid.
        :param update_data: The data to update.
        :return: The updated task.
        """
        if not task_uuid:
            raise DataValidationException("Invalid task UUID")

        if not update_data:
            raise DataValidationException("Update data cannot be empty")

        # 检查任务是否存在
        existing_task = await self.task_repository.get_by("uuid", task_uuid, unique=True)
        if not existing_task:
            raise ResourceNotFoundException(f"Task with UUID {task_uuid} not found")

        # 验证标题（如果提供）
        if "title" in update_data:
            title = update_data["title"]
            if not title or len(title.strip()) == 0:
                raise DataValidationException("Task title cannot be empty")

            if len(title) > 200:
                raise DataValidationException("Task title must be less than 200 characters")

            update_data["title"] = title.strip()

        # 验证描述（如果提供）
        if "description" in update_data and update_data["description"] is not None:
            description = update_data["description"]
            if len(description) > 1000:
                raise DataValidationException("Task description must be less than 1000 characters")

            update_data["description"] = description.strip()

        # 验证作者UUID（如果提供）
        if "task_author_uuid" in update_data:
            author_uuid = update_data["task_author_uuid"]
            if not author_uuid:
                raise DataValidationException("Invalid author UUID")

        # 检查是否尝试更新完成状态
        if "is_completed" in update_data:
            new_status = update_data["is_completed"]
            if existing_task.is_completed and not new_status:
                raise InvalidOperationException("Cannot mark completed task as incomplete")

        return await self.task_repository.update(existing_task, update_data)
