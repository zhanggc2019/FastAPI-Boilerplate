from uuid import UUID
from sqlalchemy import Select
from sqlalchemy.orm import joinedload

from app.models import Task
from app.repositories import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """
    Task repository provides all the database operations for the Task model.
    """

    async def get_by_author_uuid(self, author_uuid: UUID, join_: set[str] | None = None) -> list[Task]:
        """
        Get all tasks by author uuid.

        :param author_uuid: The author uuid to match.
        :param join_: The joins to make.
        :return: A list of tasks.
        """
        query = self._query(join_)
        query = await self._get_by(query, "task_author_uuid", author_uuid)

        if join_ is not None:
            return await self._all_unique(query)

        return await self._all(query)

    def _join_author(self, query: Select) -> Select:
        """
        Join the author relationship.

        :param query: The query to join.
        :return: The joined query.
        """
        return query.options(joinedload(Task.author))

    async def set_completed(self, task_uuid: UUID, completed: bool = True) -> Task:
        """
        Set the completed status of a task.

        :param task_uuid: The task uuid to update.
        :param completed: The completion status.
        :return: The updated task.
        """
        task = await self.get_by("uuid", task_uuid)
        task.is_completed = completed
        return task
