from __future__ import annotations

"""Repository for task data access."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundError
from ..database import set_organization_context
from .models import Task
from .schemas import TaskCreate, TaskUpdate


class TaskRepository:
    """Repository for task CRUD operations."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.db = db
        self.organization_id = organization_id

    async def _set_context(self) -> None:
        """Set organization context for RLS."""
        await set_organization_context(self.db, self.organization_id)

    async def get_by_id(self, task_id: UUID) -> Task:
        """Get task by ID."""
        await self._set_context()
        result = await self.db.execute(
            select(Task).where(
                Task.id == task_id,
                Task.organization_id == self.organization_id,
            )
        )
        task = result.scalar_one_or_none()
        if not task:
            raise NotFoundError("Task", str(task_id))
        return task

    async def list_all(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[Task], int]:
        """List all tasks for the organization."""
        await self._set_context()

        count_result = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.organization_id == self.organization_id,
            )
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Task)
            .where(
                Task.organization_id == self.organization_id,
            )
            .offset(skip)
            .limit(limit)
            .order_by(Task.created_at.desc())
        )
        tasks = list(result.scalars().all())

        return tasks, total

    async def list_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[list[Task], int]:
        """List tasks for a project."""
        await self._set_context()

        count_result = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.organization_id == self.organization_id,
            )
        )
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Task)
            .where(
                Task.project_id == project_id,
                Task.organization_id == self.organization_id,
            )
            .offset(skip)
            .limit(limit)
            .order_by(Task.position.asc(), Task.created_at.desc())
        )
        tasks = list(result.scalars().all())

        return tasks, total

    async def create(self, data: TaskCreate) -> Task:
        """Create a new task."""
        try:
            await self._set_context()
            task = Task(**data.model_dump(), organization_id=self.organization_id)
            self.db.add(task)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(task)
            return task
        except Exception:
            await self.db.rollback()
            raise

    async def update(self, task_id: UUID, data: TaskUpdate) -> Task:
        """Update a task."""
        try:
            task = await self.get_by_id(task_id)
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(task, field, value)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(task)
            return task
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, task_id: UUID) -> None:
        """Delete a task."""
        try:
            task = await self.get_by_id(task_id)
            await self.db.delete(task)
            await self.db.flush()
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
