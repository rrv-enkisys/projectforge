"""Dashboard service for aggregating statistics."""
from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..clients.models import Client
from ..database import set_organization_context
from ..projects.models import Project
from ..tasks.models import Task
from .schemas import DashboardStats, RecentProject, UpcomingTask


class DashboardService:
    """Service for dashboard statistics and aggregations."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.db = db
        self.organization_id = organization_id

    async def _set_context(self) -> None:
        """Set organization context for RLS."""
        await set_organization_context(self.db, self.organization_id)

    async def get_stats(self) -> DashboardStats:
        """Get aggregated dashboard statistics."""
        await self._set_context()

        # Count active projects
        active_projects_result = await self.db.execute(
            select(func.count(Project.id)).where(
                and_(
                    Project.organization_id == self.organization_id,
                    Project.status == "active",
                )
            )
        )
        active_projects = active_projects_result.scalar_one()

        # Count total clients
        total_clients_result = await self.db.execute(
            select(func.count(Client.id)).where(Client.organization_id == self.organization_id)
        )
        total_clients = total_clients_result.scalar_one()

        # Count completed tasks this week
        week_ago = datetime.utcnow() - timedelta(days=7)
        completed_tasks_result = await self.db.execute(
            select(func.count(Task.id)).where(
                and_(
                    Task.organization_id == self.organization_id,
                    Task.status == "done",
                    Task.updated_at >= week_ago,
                )
            )
        )
        completed_tasks_this_week = completed_tasks_result.scalar_one()

        # Get recent projects (last 5 updated)
        recent_projects_result = await self.db.execute(
            select(Project)
            .where(Project.organization_id == self.organization_id)
            .order_by(Project.updated_at.desc())
            .limit(5)
        )
        recent_projects_data = list(recent_projects_result.scalars().all())
        recent_projects = [
            RecentProject(
                id=p.id,
                name=p.name,
                status=p.status,
                updated_at=p.updated_at,
            )
            for p in recent_projects_data
        ]

        # Get upcoming tasks (due in next 7 days)
        now = datetime.utcnow()
        next_week = now + timedelta(days=7)
        upcoming_tasks_result = await self.db.execute(
            select(Task)
            .where(
                and_(
                    Task.organization_id == self.organization_id,
                    Task.due_date.isnot(None),
                    Task.due_date >= now,
                    Task.due_date <= next_week,
                    Task.status != "done",
                )
            )
            .order_by(Task.due_date.asc())
            .limit(5)
        )
        upcoming_tasks_data = list(upcoming_tasks_result.scalars().all())
        upcoming_tasks = [
            UpcomingTask(
                id=t.id,
                title=t.title,
                due_date=t.due_date,
                priority=t.priority,
                status=t.status,
                project_id=t.project_id,
            )
            for t in upcoming_tasks_data
        ]

        return DashboardStats(
            active_projects=active_projects,
            total_clients=total_clients,
            documents=0,  # TODO: Call AI service for document count
            completed_tasks_this_week=completed_tasks_this_week,
            recent_projects=recent_projects,
            upcoming_tasks=upcoming_tasks,
        )
