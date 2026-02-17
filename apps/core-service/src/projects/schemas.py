from __future__ import annotations

"""Pydantic schemas for projects."""
from datetime import date, datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

from ..common.validators import BudgetValidator, DateValidator
from .models import ProjectStatus


class ProjectBase(BaseModel):
    """Base schema for project data."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    client_id: UUID | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = None
    settings: dict = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    @field_validator("budget")
    @classmethod
    def validate_budget_positive(cls, v: float | None) -> float | None:
        """Validate that budget is positive."""
        if v is not None:
            BudgetValidator.validate_positive_amount(v, "budget")
        return v

    @model_validator(mode="after")
    def validate_date_range(self) -> "ProjectCreate":
        """Validate that end_date is after start_date."""
        DateValidator.validate_date_range(self.start_date, self.end_date, "project dates")
        return self


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    client_id: UUID | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    budget: float | None = None
    settings: dict | None = None

    @field_validator("budget")
    @classmethod
    def validate_budget_positive(cls, v: float | None) -> float | None:
        """Validate that budget is positive."""
        if v is not None:
            BudgetValidator.validate_positive_amount(v, "budget")
        return v


class ProjectResponse(ProjectBase):
    """Schema for project response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectListResponse(BaseModel):
    """Schema for paginated project list."""

    data: list[ProjectResponse]
    total: int
    has_more: bool


class ProjectStatistics(BaseModel):
    """Schema for project statistics."""

    project_id: UUID
    project_name: str

    # Task statistics
    total_tasks: int
    tasks_by_status: dict[str, int]
    tasks_by_priority: dict[str, int]
    completed_tasks_count: int
    completion_percentage: float

    # Milestone statistics
    total_milestones: int
    completed_milestones: int
    milestones_completion_percentage: float

    # Time statistics
    overdue_tasks_count: int
    tasks_due_this_week: int
    tasks_due_this_month: int

    # Budget statistics (if applicable)
    total_estimated_hours: float
    total_actual_hours: float
    hours_completion_percentage: float
