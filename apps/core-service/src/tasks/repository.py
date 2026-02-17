from __future__ import annotations

"""Repository for task data access."""
from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundError
from ..database import set_organization_context
from .models import Task, TaskPriority, TaskStatus
from .schemas import TaskCreate, TaskFilter, TaskSort, TaskUpdate


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

    async def get_ancestors(self, task_id: UUID) -> list[UUID]:
        """Get all ancestor task IDs (parent, parent's parent, etc.)."""
        await self._set_context()
        ancestors = []
        current_id = task_id

        max_depth = 100  # Prevent infinite loops
        depth = 0

        while current_id and depth < max_depth:
            result = await self.db.execute(
                select(Task.parent_task_id).where(
                    Task.id == current_id,
                    Task.organization_id == self.organization_id,
                )
            )
            parent_id = result.scalar_one_or_none()

            if parent_id:
                if parent_id in ancestors:
                    # Circular dependency detected
                    break
                ancestors.append(parent_id)
                current_id = parent_id
            else:
                break

            depth += 1

        return ancestors

    async def bulk_create(self, tasks_data: list[TaskCreate]) -> list[Task]:
        """Create multiple tasks."""
        try:
            await self._set_context()
            tasks = [Task(**data.model_dump(), organization_id=self.organization_id) for data in tasks_data]
            self.db.add_all(tasks)
            await self.db.flush()
            await self.db.commit()
            for task in tasks:
                await self.db.refresh(task)
            return tasks
        except Exception:
            await self.db.rollback()
            raise

    async def bulk_update(self, task_ids: list[UUID], data: TaskUpdate) -> int:
        """Update multiple tasks. Returns number of updated tasks."""
        try:
            await self._set_context()
            update_data = data.model_dump(exclude_unset=True)

            stmt = (
                update(Task)
                .where(
                    Task.id.in_(task_ids),
                    Task.organization_id == self.organization_id,
                )
                .values(**update_data)
            )

            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.rowcount  # type: ignore
        except Exception:
            await self.db.rollback()
            raise

    async def bulk_delete(self, task_ids: list[UUID]) -> int:
        """Delete multiple tasks. Returns number of deleted tasks."""
        try:
            await self._set_context()

            stmt = delete(Task).where(
                Task.id.in_(task_ids),
                Task.organization_id == self.organization_id,
            )

            result = await self.db.execute(stmt)
            await self.db.commit()
            return result.rowcount  # type: ignore
        except Exception:
            await self.db.rollback()
            raise

    async def list_filtered(
        self,
        filters: TaskFilter,
        sort: TaskSort | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Task], int]:
        """List tasks with advanced filtering and sorting."""
        await self._set_context()

        # Build base query
        query = select(Task).where(Task.organization_id == self.organization_id)

        # Apply filters
        if filters.project_id:
            query = query.where(Task.project_id == filters.project_id)

        if filters.milestone_id:
            query = query.where(Task.milestone_id == filters.milestone_id)

        if filters.status:
            query = query.where(Task.status.in_(filters.status))

        if filters.priority:
            query = query.where(Task.priority.in_(filters.priority))

        if filters.start_date_from:
            query = query.where(Task.start_date >= filters.start_date_from)

        if filters.start_date_to:
            query = query.where(Task.start_date <= filters.start_date_to)

        if filters.due_date_from:
            query = query.where(Task.due_date >= filters.due_date_from)

        if filters.due_date_to:
            query = query.where(Task.due_date <= filters.due_date_to)

        if filters.search:
            search_term = f"%{filters.search}%"
            query = query.where(
                or_(
                    Task.title.ilike(search_term),
                    Task.description.ilike(search_term),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        # Apply sorting
        if sort:
            sort_column = getattr(Task, sort.field)
            if sort.direction == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # Default sort
            query = query.order_by(Task.position.asc(), Task.created_at.desc())

        # Apply pagination
        query = query.offset(skip).limit(limit)

        # Execute
        result = await self.db.execute(query)
        tasks = list(result.scalars().all())

        return tasks, total
