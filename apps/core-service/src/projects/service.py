from __future__ import annotations

"""Business logic for projects."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .repository import ProjectRepository
from .schemas import ProjectCreate, ProjectResponse, ProjectUpdate


class ProjectService:
    """Service layer for project business logic."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.repository = ProjectRepository(db, organization_id)

    async def get_project(self, project_id: UUID) -> ProjectResponse:
        """Get project by ID."""
        project = await self.repository.get_by_id(project_id)
        return ProjectResponse.model_validate(project)

    async def list_projects(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[ProjectResponse], int]:
        """List projects with pagination."""
        projects, total = await self.repository.list(skip=skip, limit=limit)
        return [ProjectResponse.model_validate(p) for p in projects], total

    async def create_project(self, data: ProjectCreate) -> ProjectResponse:
        """Create a new project."""
        project = await self.repository.create(data)
        return ProjectResponse.model_validate(project)

    async def update_project(self, project_id: UUID, data: ProjectUpdate) -> ProjectResponse:
        """Update a project."""
        project = await self.repository.update(project_id, data)
        return ProjectResponse.model_validate(project)

    async def delete_project(self, project_id: UUID) -> None:
        """Delete a project."""
        await self.repository.delete(project_id)
