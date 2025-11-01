from app.models import Task
from app.repositories import TaskRepository
from core.controller import BaseController
from core.database.transactional import Propagation, Transactional
from core.exceptions import (
    DataValidationException,
    ResourceNotFoundException,
    InvalidOperationException,
)


class TaskController(BaseController[Task]):
    """Task controller."""

    def __init__(self, task_repository: TaskRepository):
        super().__init__(model=Task, repository=task_repository)
        self.task_repository = task_repository

    async def get_by_author_id(self, author_id: int) -> list[Task]:
        """
        Returns a list of tasks based on author_id.

        :param author_id: The author id.
        :return: A list of tasks.
        """
        if not author_id or author_id <= 0:
            raise DataValidationException("Invalid author ID")

        return await self.task_repository.get_by_author_id(author_id)

    @Transactional(propagation=Propagation.REQUIRED)
    async def add(self, title: str, description: str, author_id: int) -> Task:
        """
        Adds a task.

        :param title: The task title.
        :param description: The task description.
        :param author_id: The author id.
        :return: The task.
        """
        # 参数验证
        if not title or len(title.strip()) == 0:
            raise DataValidationException("Task title cannot be empty")

        if len(title) > 200:
            raise DataValidationException("Task title must be less than 200 characters")

        if description and len(description) > 1000:
            raise DataValidationException("Task description must be less than 1000 characters")

        if not author_id or author_id <= 0:
            raise DataValidationException("Invalid author ID")

        # 验证作者是否存在（这里假设有用户控制器或用户服务）
        # 在实际应用中，应该注入用户服务来验证作者存在性
        # 这里暂时跳过这个验证，保持与现有代码的兼容性

        return await self.task_repository.create(
            {
                "title": title.strip(),
                "description": description.strip() if description else None,
                "task_author_id": author_id,
            }
        )

    @Transactional(propagation=Propagation.REQUIRED)
    async def complete(self, task_id: int) -> Task:
        """
        Completes a task.

        :param task_id: The task id.
        :return: The task.
        """
        if not task_id or task_id <= 0:
            raise DataValidationException("Invalid task ID")

        # 检查任务是否存在
        task = await self.task_repository.get_by_id(task_id)
        if not task:
            raise ResourceNotFoundException(f"Task with ID {task_id} not found")

        # 检查任务是否已经完成
        if task.is_completed:
            raise InvalidOperationException("Task is already completed")

        return await self.task_repository.set_completed(task_id, True)

    async def get_task_by_id(self, task_id: int) -> Task:
        """
        Get task by ID with validation.

        :param task_id: The task id.
        :return: The task.
        """
        if not task_id or task_id <= 0:
            raise DataValidationException("Invalid task ID")

        task = await self.task_repository.get_by_id(task_id)
        if not task:
            raise ResourceNotFoundException(f"Task with ID {task_id} not found")

        return task

    async def delete_task(self, task_id: int) -> bool:
        """
        Delete task with validation.

        :param task_id: The task id.
        :return: True if deleted successfully.
        """
        if not task_id or task_id <= 0:
            raise DataValidationException("Invalid task ID")

        # 检查任务是否存在
        task = await self.task_repository.get_by_id(task_id)
        if not task:
            raise ResourceNotFoundException(f"Task with ID {task_id} not found")

        # 检查任务是否已经完成（可以根据业务规则决定是否允许删除已完成的任务）
        if task.is_completed:
            raise InvalidOperationException("Cannot delete completed task")

        return await self.task_repository.delete(task_id)

    async def update_task(self, task_id: int, update_data: dict) -> Task:
        """
        Update task with validation.

        :param task_id: The task id.
        :param update_data: The data to update.
        :return: The updated task.
        """
        if not task_id or task_id <= 0:
            raise DataValidationException("Invalid task ID")

        if not update_data:
            raise DataValidationException("Update data cannot be empty")

        # 检查任务是否存在
        existing_task = await self.task_repository.get_by_id(task_id)
        if not existing_task:
            raise ResourceNotFoundException(f"Task with ID {task_id} not found")

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

        # 验证作者ID（如果提供）
        if "task_author_id" in update_data:
            author_id = update_data["task_author_id"]
            if not author_id or author_id <= 0:
                raise DataValidationException("Invalid author ID")

        # 检查是否尝试更新完成状态
        if "is_completed" in update_data:
            new_status = update_data["is_completed"]
            if existing_task.is_completed and not new_status:
                raise InvalidOperationException("Cannot mark completed task as incomplete")

        return await self.task_repository.update(task_id, update_data)
