"""Dashboard schemas for statistics and aggregations."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class RecentProject(BaseModel):
    """Recent project summary."""

    id: UUID
    name: str
    status: str
    updated_at: datetime

    class Config:
        from_attributes = True


class UpcomingTask(BaseModel):
    """Upcoming task summary."""

    id: UUID
    title: str
    due_date: datetime | None
    priority: str
    status: str
    project_id: UUID

    class Config:
        from_attributes = True


class DashboardStats(BaseModel):
    """Dashboard statistics response."""

    active_projects: int
    total_clients: int
    documents: int
    completed_tasks_this_week: int
    recent_projects: list[RecentProject]
    upcoming_tasks: list[UpcomingTask]


class DashboardStatsResponse(BaseModel):
    """Dashboard stats API response."""

    data: DashboardStats
