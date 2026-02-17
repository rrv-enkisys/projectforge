from __future__ import annotations

"""Pydantic schemas for tasks."""
from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from ..common.validators import DateValidator
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

    @field_validator("estimated_hours", "actual_hours")
    @classmethod
    def validate_hours_positive(cls, v: Decimal | None) -> Decimal | None:
        """Validate that hours are positive."""
        if v is not None and v < 0:
            from ..common.exceptions import ValidationError

            raise ValidationError("Hours must be positive", field="hours")
        return v

    @model_validator(mode="after")
    def validate_dates(self) -> "TaskCreate":
        """Validate task date logic."""
        # Validate start_date < due_date
        DateValidator.validate_date_range(self.start_date, self.due_date, "task dates")

        # Don't allow setting self as parent
        if self.parent_task_id and hasattr(self, "id"):
            if self.parent_task_id == getattr(self, "id", None):
                from ..common.exceptions import BusinessRuleError

                raise BusinessRuleError("A task cannot be its own parent", rule="circular_dependency")

        return self


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

    @field_validator("estimated_hours", "actual_hours")
    @classmethod
    def validate_hours_positive(cls, v: Decimal | None) -> Decimal | None:
        """Validate that hours are positive."""
        if v is not None and v < 0:
            from ..common.exceptions import ValidationError

            raise ValidationError("Hours must be positive", field="hours")
        return v


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


class TaskBulkCreate(BaseModel):
    """Schema for creating multiple tasks."""

    tasks: list[TaskCreate] = Field(..., min_length=1, max_length=100)


class TaskBulkUpdate(BaseModel):
    """Schema for updating multiple tasks."""

    task_ids: list[UUID] = Field(..., min_length=1, max_length=100)
    update: TaskUpdate


class TaskBulkDelete(BaseModel):
    """Schema for deleting multiple tasks."""

    task_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class TaskFilter(BaseModel):
    """Schema for filtering tasks."""

    project_id: UUID | None = None
    milestone_id: UUID | None = None
    status: list[TaskStatus] | None = None
    priority: list[TaskPriority] | None = None
    start_date_from: date | None = None
    start_date_to: date | None = None
    due_date_from: date | None = None
    due_date_to: date | None = None
    search: str | None = Field(None, max_length=255)  # Search in title/description
    assigned_user_id: UUID | None = None  # Future: when we add assignments


class TaskSort(BaseModel):
    """Schema for sorting tasks."""

    field: str = Field(..., pattern="^(created_at|updated_at|due_date|priority|status|position)$")
    direction: str = Field("asc", pattern="^(asc|desc)$")
