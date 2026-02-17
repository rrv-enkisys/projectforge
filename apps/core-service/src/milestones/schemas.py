from __future__ import annotations

"""Pydantic schemas for milestones."""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .models import MilestoneStatus


class MilestoneBase(BaseModel):
    """Base schema for milestone data."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    project_id: UUID
    target_date: date | None = None
    status: MilestoneStatus = MilestoneStatus.PLANNING


class MilestoneCreate(MilestoneBase):
    """Schema for creating a milestone."""

    pass


class MilestoneUpdate(BaseModel):
    """Schema for updating a milestone."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    target_date: date | None = None
    status: MilestoneStatus | None = None


class MilestoneComplete(BaseModel):
    """Schema for marking milestone as completed."""

    completed: bool = True


class MilestoneResponse(MilestoneBase):
    """Schema for milestone response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MilestoneListResponse(BaseModel):
    """Schema for paginated milestone list."""

    data: list[MilestoneResponse]
    total: int
    has_more: bool
