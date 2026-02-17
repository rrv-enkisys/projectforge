from __future__ import annotations

"""Business logic for tasks."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import BusinessRuleError, NotFoundError
from ..common.validators import DateValidator, DependencyValidator, OrganizationValidator, StatusValidator
from ..milestones.repository import MilestoneRepository
from ..projects.repository import ProjectRepository
from .repository import TaskRepository
from .schemas import (
    TaskBulkCreate,
    TaskBulkDelete,
    TaskBulkUpdate,
    TaskCreate,
    TaskFilter,
    TaskResponse,
    TaskSort,
    TaskStatusUpdate,
    TaskUpdate,
)


class TaskService:
    """Service layer for task business logic."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.repository = TaskRepository(db, organization_id)
        self.project_repository = ProjectRepository(db, organization_id)
        self.milestone_repository = MilestoneRepository(db, organization_id)
        self.db = db
        self.organization_id = organization_id

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
        # Validate project exists
        try:
            project = await self.project_repository.get_by_id(data.project_id)
        except NotFoundError:
            raise NotFoundError("Project", str(data.project_id))

        # Validate milestone belongs to same project if specified
        if data.milestone_id:
            try:
                milestone = await self.milestone_repository.get_by_id(data.milestone_id)
                if milestone.project_id != data.project_id:
                    raise BusinessRuleError(
                        "Milestone must belong to the same project as the task",
                        rule="milestone_project_match",
                    )
            except NotFoundError:
                raise NotFoundError("Milestone", str(data.milestone_id))

        # Validate parent task belongs to same project if specified
        if data.parent_task_id:
            try:
                parent_task = await self.repository.get_by_id(data.parent_task_id)
                if parent_task.project_id != data.project_id:
                    raise BusinessRuleError(
                        "Parent task must belong to the same project",
                        rule="parent_task_project_match",
                    )
            except NotFoundError:
                raise NotFoundError("Parent task", str(data.parent_task_id))

        # Validate task dates are within project dates
        if data.start_date and project.start_date:
            DateValidator.validate_date_within_range(
                data.start_date,
                project.start_date,
                project.end_date,
                "task start_date",
                "project",
            )

        if data.due_date:
            DateValidator.validate_date_within_range(
                data.due_date,
                project.start_date,
                project.end_date,
                "task due_date",
                "project",
            )

        task = await self.repository.create(data)
        return TaskResponse.model_validate(task)

    async def update_task(self, task_id: UUID, data: TaskUpdate) -> TaskResponse:
        """Update a task."""
        # Get current task
        current_task = await self.repository.get_by_id(task_id)

        # Validate status transition if status is being updated
        if data.status is not None and data.status != current_task.status:
            StatusValidator.validate_status_transition(
                current_status=current_task.status.value,
                new_status=data.status.value,
                transitions=StatusValidator.TASK_TRANSITIONS,
                entity_type="task",
            )

        # Validate milestone if being updated
        if data.milestone_id is not None:
            try:
                milestone = await self.milestone_repository.get_by_id(data.milestone_id)
                if milestone.project_id != current_task.project_id:
                    raise BusinessRuleError(
                        "Milestone must belong to the same project as the task",
                        rule="milestone_project_match",
                    )
            except NotFoundError:
                raise NotFoundError("Milestone", str(data.milestone_id))

        # Validate parent task and circular dependencies
        if data.parent_task_id is not None:
            # Cannot set self as parent
            if data.parent_task_id == task_id:
                raise BusinessRuleError(
                    "A task cannot be its own parent",
                    rule="circular_dependency",
                )

            # Check for circular dependency
            try:
                parent_task = await self.repository.get_by_id(data.parent_task_id)
                if parent_task.project_id != current_task.project_id:
                    raise BusinessRuleError(
                        "Parent task must belong to the same project",
                        rule="parent_task_project_match",
                    )

                # Check ancestors to detect circular dependency
                async def get_ancestors_fn(parent_id: UUID) -> list[UUID]:
                    return await self.repository.get_ancestors(parent_id)

                DependencyValidator.detect_circular_dependency(
                    item_id=task_id,
                    parent_id=data.parent_task_id,
                    get_ancestors_fn=get_ancestors_fn,
                )
            except NotFoundError:
                raise NotFoundError("Parent task", str(data.parent_task_id))

        # Validate dates against project if being updated
        if data.start_date is not None or data.due_date is not None:
            project = await self.project_repository.get_by_id(current_task.project_id)

            start_date = data.start_date if data.start_date is not None else current_task.start_date
            due_date = data.due_date if data.due_date is not None else current_task.due_date

            if start_date and project.start_date:
                DateValidator.validate_date_within_range(
                    start_date,
                    project.start_date,
                    project.end_date,
                    "task start_date",
                    "project",
                )

            if due_date:
                DateValidator.validate_date_within_range(
                    due_date,
                    project.start_date,
                    project.end_date,
                    "task due_date",
                    "project",
                )

        task = await self.repository.update(task_id, data)
        return TaskResponse.model_validate(task)

    async def update_status(self, task_id: UUID, data: TaskStatusUpdate) -> TaskResponse:
        """Update task status (for Kanban board)."""
        update_data = TaskUpdate(status=data.status, position=data.position)
        return await self.update_task(task_id, update_data)

    async def delete_task(self, task_id: UUID) -> None:
        """Delete a task."""
        await self.repository.delete(task_id)

    async def bulk_create_tasks(self, data: TaskBulkCreate) -> list[TaskResponse]:
        """Create multiple tasks."""
        # Validate each task (basic validation)
        for task_data in data.tasks:
            # Validate project exists
            try:
                project = await self.project_repository.get_by_id(task_data.project_id)
            except NotFoundError:
                raise NotFoundError("Project", str(task_data.project_id))

        # Create all tasks
        tasks = await self.repository.bulk_create(data.tasks)
        return [TaskResponse.model_validate(t) for t in tasks]

    async def bulk_update_tasks(self, data: TaskBulkUpdate) -> dict[str, int]:
        """Update multiple tasks."""
        updated_count = await self.repository.bulk_update(data.task_ids, data.update)
        return {"updated": updated_count}

    async def bulk_delete_tasks(self, data: TaskBulkDelete) -> dict[str, int]:
        """Delete multiple tasks."""
        deleted_count = await self.repository.bulk_delete(data.task_ids)
        return {"deleted": deleted_count}

    async def list_tasks_filtered(
        self,
        filters: TaskFilter,
        sort: TaskSort | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[TaskResponse], int]:
        """List tasks with advanced filtering and sorting."""
        tasks, total = await self.repository.list_filtered(filters, sort, skip, limit)
        return [TaskResponse.model_validate(t) for t in tasks], total
