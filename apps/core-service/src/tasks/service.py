from __future__ import annotations

"""Business logic for tasks."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .repository import TaskRepository
from .schemas import TaskCreate, TaskResponse, TaskStatusUpdate, TaskUpdate


class TaskService:
    """Service layer for task business logic."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.repository = TaskRepository(db, organization_id)

    async def get_task(self, task_id: UUID) -> TaskResponse:
        """Get task by ID."""
        task = await self.repository.get_by_id(task_id)
        return TaskResponse.model_validate(task)

    async def list_tasks(
        self, project_id: UUID | None, skip: int = 0, limit: int = 100
    ) -> tuple[list[TaskResponse], int]:
        """List tasks for a project, or all tasks if project_id is None."""
        if project_id:
            tasks, total = await self.repository.list_by_project(project_id, skip, limit)
        else:
            # List all tasks for the organization
            tasks, total = await self.repository.list_all(skip, limit)
        return [TaskResponse.model_validate(t) for t in tasks], total

    async def create_task(self, data: TaskCreate) -> TaskResponse:
        """Create a new task."""
        task = await self.repository.create(data)
        return TaskResponse.model_validate(task)

    async def update_task(self, task_id: UUID, data: TaskUpdate) -> TaskResponse:
        """Update a task."""
        task = await self.repository.update(task_id, data)
        return TaskResponse.model_validate(task)

    async def update_status(self, task_id: UUID, data: TaskStatusUpdate) -> TaskResponse:
        """Update task status (for Kanban board)."""
        update_data = TaskUpdate(status=data.status, position=data.position)
        return await self.update_task(task_id, update_data)

    async def delete_task(self, task_id: UUID) -> None:
        """Delete a task."""
        await self.repository.delete(task_id)
