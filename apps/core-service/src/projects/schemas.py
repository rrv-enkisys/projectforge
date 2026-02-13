"""Pydantic schemas for projects."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .models import ProjectStatus


class ProjectBase(BaseModel):
    """Base schema for project data."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    client_id: UUID | None = None
    status: ProjectStatus = ProjectStatus.PLANNING
    start_date: date | None = None
    end_date: date | None = None
    settings: dict = Field(default_factory=dict)


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    client_id: UUID | None = None
    status: ProjectStatus | None = None
    start_date: date | None = None
    end_date: date | None = None
    settings: dict | None = None


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
