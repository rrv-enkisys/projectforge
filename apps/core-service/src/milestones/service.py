from __future__ import annotations

"""Business logic for milestones."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundError
from ..common.validators import DateValidator, StatusValidator
from ..projects.repository import ProjectRepository
from .models import MilestoneStatus
from .repository import MilestoneRepository
from .schemas import MilestoneCreate, MilestoneResponse, MilestoneUpdate


class MilestoneService:
    """Service layer for milestone business logic."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.repository = MilestoneRepository(db, organization_id)
        self.project_repository = ProjectRepository(db, organization_id)
        self.db = db
        self.organization_id = organization_id

    async def get_milestone(self, milestone_id: UUID) -> MilestoneResponse:
        """Get milestone by ID."""
        milestone = await self.repository.get_by_id(milestone_id)
        return MilestoneResponse.model_validate(milestone)

    async def list_milestones(
        self, project_id: UUID | None = None, skip: int = 0, limit: int = 100
    ) -> tuple[list[MilestoneResponse], int]:
        """List milestones for a project (or all if no project_id)."""
        if project_id:
            milestones, total = await self.repository.list_by_project(project_id, skip, limit)
        else:
            milestones, total = await self.repository.list_all(skip, limit)
        return [MilestoneResponse.model_validate(m) for m in milestones], total

    async def create_milestone(self, data: MilestoneCreate) -> MilestoneResponse:
        """Create a new milestone."""
        # Validate project exists
        try:
            project = await self.project_repository.get_by_id(data.project_id)
        except NotFoundError:
            raise NotFoundError("Project", str(data.project_id))

        # Validate target date is within project dates
        if data.target_date:
            DateValidator.validate_date_within_range(
                data.target_date,
                project.start_date,
                project.end_date,
                "milestone target_date",
                "project",
            )

        milestone = await self.repository.create(data)
        return MilestoneResponse.model_validate(milestone)

    async def update_milestone(
        self, milestone_id: UUID, data: MilestoneUpdate
    ) -> MilestoneResponse:
        """Update a milestone."""
        # Get current milestone
        current_milestone = await self.repository.get_by_id(milestone_id)

        # Validate status transition if status is being updated
        if data.status is not None and data.status != current_milestone.status:
            StatusValidator.validate_status_transition(
                current_status=current_milestone.status.value,
                new_status=data.status.value,
                transitions=StatusValidator.MILESTONE_TRANSITIONS,
                entity_type="milestone",
            )

        # Validate target date against project if being updated
        if data.target_date is not None:
            project = await self.project_repository.get_by_id(current_milestone.project_id)
            DateValidator.validate_date_within_range(
                data.target_date,
                project.start_date,
                project.end_date,
                "milestone target_date",
                "project",
            )

        milestone = await self.repository.update(milestone_id, data)
        return MilestoneResponse.model_validate(milestone)

    async def mark_completed(self, milestone_id: UUID) -> MilestoneResponse:
        """Mark a milestone as completed."""
        update_data = MilestoneUpdate(status=MilestoneStatus.COMPLETED)
        return await self.update_milestone(milestone_id, update_data)

    async def delete_milestone(self, milestone_id: UUID) -> None:
        """Delete a milestone."""
        await self.repository.delete(milestone_id)
