from __future__ import annotations

"""Repository for project data access."""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundError
from ..database import set_organization_context
from .models import Project
from .schemas import ProjectCreate, ProjectStatistics, ProjectUpdate

if TYPE_CHECKING:
    from ..milestones.models import Milestone, MilestoneStatus
    from ..tasks.models import Task, TaskPriority, TaskStatus


class ProjectRepository:
    """Repository for project CRUD operations."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.db = db
        self.organization_id = organization_id

    async def _set_context(self) -> None:
        """Set organization context for RLS."""
        await set_organization_context(self.db, self.organization_id)

    async def get_by_id(self, project_id: UUID) -> Project:
        """Get project by ID."""
        await self._set_context()
        result = await self.db.execute(
            select(Project).where(
                Project.id == project_id,
                Project.organization_id == self.organization_id,
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundError("Project", str(project_id))
        return project

    async def list(self, skip: int = 0, limit: int = 100) -> tuple[list[Project], int]:
        """List projects with pagination."""
        await self._set_context()

        # Get total count
        count_result = await self.db.execute(
            select(func.count(Project.id)).where(Project.organization_id == self.organization_id)
        )
        total = count_result.scalar_one()

        # Get paginated results
        result = await self.db.execute(
            select(Project)
            .where(Project.organization_id == self.organization_id)
            .offset(skip)
            .limit(limit)
            .order_by(Project.created_at.desc())
        )
        projects = list(result.scalars().all())

        return projects, total

    async def create(self, data: ProjectCreate) -> Project:
        """Create a new project."""
        try:
            await self._set_context()
            project = Project(**data.model_dump(), organization_id=self.organization_id)
            self.db.add(project)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(project)
            return project
        except Exception:
            await self.db.rollback()
            raise

    async def update(self, project_id: UUID, data: ProjectUpdate) -> Project:
        """Update a project."""
        try:
            project = await self.get_by_id(project_id)
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(project, field, value)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(project)
            return project
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, project_id: UUID) -> None:
        """Delete a project."""
        try:
            project = await self.get_by_id(project_id)
            await self.db.delete(project)
            await self.db.flush()
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise

    async def get_statistics(self, project_id: UUID) -> ProjectStatistics:
        """Get comprehensive statistics for a project."""
        from ..milestones.models import Milestone, MilestoneStatus
        from ..tasks.models import Task, TaskPriority, TaskStatus

        await self._set_context()

        # Get project
        project = await self.get_by_id(project_id)

        # Get task statistics
        task_count_result = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.organization_id == self.organization_id,
            )
        )
        total_tasks = task_count_result.scalar_one()

        # Tasks by status
        tasks_by_status = {}
        for status_value in TaskStatus:
            status_count_result = await self.db.execute(
                select(func.count(Task.id)).where(
                    Task.project_id == project_id,
                    Task.organization_id == self.organization_id,
                    Task.status == status_value,
                )
            )
            tasks_by_status[status_value.value] = status_count_result.scalar_one()

        # Tasks by priority
        tasks_by_priority = {}
        for priority_value in TaskPriority:
            priority_count_result = await self.db.execute(
                select(func.count(Task.id)).where(
                    Task.project_id == project_id,
                    Task.organization_id == self.organization_id,
                    Task.priority == priority_value,
                )
            )
            tasks_by_priority[priority_value.value] = priority_count_result.scalar_one()

        completed_tasks_count = tasks_by_status.get("done", 0)
        completion_percentage = (completed_tasks_count / total_tasks * 100) if total_tasks > 0 else 0.0

        # Milestone statistics
        milestone_count_result = await self.db.execute(
            select(func.count(Milestone.id)).where(
                Milestone.project_id == project_id,
                Milestone.organization_id == self.organization_id,
            )
        )
        total_milestones = milestone_count_result.scalar_one()

        completed_milestones_result = await self.db.execute(
            select(func.count(Milestone.id)).where(
                Milestone.project_id == project_id,
                Milestone.organization_id == self.organization_id,
                Milestone.status == MilestoneStatus.COMPLETED,
            )
        )
        completed_milestones = completed_milestones_result.scalar_one()

        milestones_completion_percentage = (
            (completed_milestones / total_milestones * 100) if total_milestones > 0 else 0.0
        )

        # Time statistics
        today = date.today()
        week_from_now = today + timedelta(days=7)
        month_from_now = today + timedelta(days=30)

        overdue_tasks_result = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.organization_id == self.organization_id,
                Task.due_date < today,
                Task.status != TaskStatus.DONE,
            )
        )
        overdue_tasks_count = overdue_tasks_result.scalar_one()

        tasks_due_this_week_result = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.organization_id == self.organization_id,
                Task.due_date >= today,
                Task.due_date <= week_from_now,
            )
        )
        tasks_due_this_week = tasks_due_this_week_result.scalar_one()

        tasks_due_this_month_result = await self.db.execute(
            select(func.count(Task.id)).where(
                Task.project_id == project_id,
                Task.organization_id == self.organization_id,
                Task.due_date >= today,
                Task.due_date <= month_from_now,
            )
        )
        tasks_due_this_month = tasks_due_this_month_result.scalar_one()

        # Hours statistics
        estimated_hours_result = await self.db.execute(
            select(func.coalesce(func.sum(Task.estimated_hours), 0)).where(
                Task.project_id == project_id,
                Task.organization_id == self.organization_id,
            )
        )
        total_estimated_hours = float(estimated_hours_result.scalar_one() or 0)

        actual_hours_result = await self.db.execute(
            select(func.coalesce(func.sum(Task.actual_hours), 0)).where(
                Task.project_id == project_id,
                Task.organization_id == self.organization_id,
            )
        )
        total_actual_hours = float(actual_hours_result.scalar_one() or 0)

        hours_completion_percentage = (
            (total_actual_hours / total_estimated_hours * 100) if total_estimated_hours > 0 else 0.0
        )

        return ProjectStatistics(
            project_id=project.id,
            project_name=project.name,
            total_tasks=total_tasks,
            tasks_by_status=tasks_by_status,
            tasks_by_priority=tasks_by_priority,
            completed_tasks_count=completed_tasks_count,
            completion_percentage=round(completion_percentage, 2),
            total_milestones=total_milestones,
            completed_milestones=completed_milestones,
            milestones_completion_percentage=round(milestones_completion_percentage, 2),
            overdue_tasks_count=overdue_tasks_count,
            tasks_due_this_week=tasks_due_this_week,
            tasks_due_this_month=tasks_due_this_month,
            total_estimated_hours=total_estimated_hours,
            total_actual_hours=total_actual_hours,
            hours_completion_percentage=round(hours_completion_percentage, 2),
        )
