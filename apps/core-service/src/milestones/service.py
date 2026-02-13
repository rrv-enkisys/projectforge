"""Business logic for milestones."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .models import MilestoneStatus
from .repository import MilestoneRepository
from .schemas import MilestoneCreate, MilestoneResponse, MilestoneUpdate


class MilestoneService:
    """Service layer for milestone business logic."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.repository = MilestoneRepository(db, organization_id)

    async def get_milestone(self, milestone_id: UUID) -> MilestoneResponse:
        """Get milestone by ID."""
        milestone = await self.repository.get_by_id(milestone_id)
        return MilestoneResponse.model_validate(milestone)

    async def list_milestones(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[list[MilestoneResponse], int]:
        """List milestones for a project."""
        milestones, total = await self.repository.list_by_project(project_id, skip, limit)
        return [MilestoneResponse.model_validate(m) for m in milestones], total

    async def create_milestone(self, data: MilestoneCreate) -> MilestoneResponse:
        """Create a new milestone."""
        milestone = await self.repository.create(data)
        return MilestoneResponse.model_validate(milestone)

    async def update_milestone(
        self, milestone_id: UUID, data: MilestoneUpdate
    ) -> MilestoneResponse:
        """Update a milestone."""
        milestone = await self.repository.update(milestone_id, data)
        return MilestoneResponse.model_validate(milestone)

    async def mark_completed(self, milestone_id: UUID) -> MilestoneResponse:
        """Mark a milestone as completed."""
        update_data = MilestoneUpdate(status=MilestoneStatus.COMPLETED)
        return await self.update_milestone(milestone_id, update_data)

    async def delete_milestone(self, milestone_id: UUID) -> None:
        """Delete a milestone."""
        await self.repository.delete(milestone_id)
