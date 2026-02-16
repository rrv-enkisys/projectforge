from __future__ import annotations

"""Repository for project data access."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundError
from ..database import set_organization_context
from .models import Project
from .schemas import ProjectCreate, ProjectUpdate


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
