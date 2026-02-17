from __future__ import annotations

"""Business logic for projects."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import BusinessRuleError
from ..common.validators import DateValidator, StatusValidator
from .repository import ProjectRepository
from .schemas import ProjectCreate, ProjectResponse, ProjectStatistics, ProjectUpdate


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
        # Get current project for validation
        current_project = await self.repository.get_by_id(project_id)

        # Validate status transition if status is being updated
        if data.status is not None and data.status != current_project.status:
            StatusValidator.validate_status_transition(
                current_status=current_project.status.value,
                new_status=data.status.value,
                transitions=StatusValidator.PROJECT_TRANSITIONS,
                entity_type="project",
            )

        # Validate date range if dates are being updated
        start_date = data.start_date if data.start_date is not None else current_project.start_date
        end_date = data.end_date if data.end_date is not None else current_project.end_date

        if start_date or end_date:
            DateValidator.validate_date_range(start_date, end_date, "project dates")

        project = await self.repository.update(project_id, data)
        return ProjectResponse.model_validate(project)

    async def delete_project(self, project_id: UUID) -> None:
        """Delete a project."""
        await self.repository.delete(project_id)

    async def get_project_statistics(self, project_id: UUID) -> ProjectStatistics:
        """Get comprehensive statistics for a project."""
        return await self.repository.get_statistics(project_id)
