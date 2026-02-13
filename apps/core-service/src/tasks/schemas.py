"""Pydantic schemas for tasks."""
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field

from .models import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    """Base schema for task data."""

    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    project_id: UUID
    milestone_id: UUID | None = None
    parent_task_id: UUID | None = None
    status: TaskStatus = TaskStatus.TODO
    priority: TaskPriority = TaskPriority.MEDIUM
    start_date: date | None = None
    due_date: date | None = None
    estimated_hours: Decimal | None = None
    actual_hours: Decimal | None = None
    position: int = 0


class TaskCreate(TaskBase):
    """Schema for creating a task."""

    pass


class TaskUpdate(BaseModel):
    """Schema for updating a task."""

    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    milestone_id: UUID | None = None
    parent_task_id: UUID | None = None
    status: TaskStatus | None = None
    priority: TaskPriority | None = None
    start_date: date | None = None
    due_date: date | None = None
    estimated_hours: Decimal | None = None
    actual_hours: Decimal | None = None
    position: int | None = None


class TaskStatusUpdate(BaseModel):
    """Schema for updating task status (Kanban)."""

    status: TaskStatus
    position: int | None = None


class TaskResponse(TaskBase):
    """Schema for task response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TaskListResponse(BaseModel):
    """Schema for paginated task list."""

    data: list[TaskResponse]
    total: int
    has_more: bool
