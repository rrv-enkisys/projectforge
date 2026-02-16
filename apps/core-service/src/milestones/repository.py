from __future__ import annotations

"""Repository for milestone data access."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundError
from ..database import set_organization_context
from .models import Milestone
from .schemas import MilestoneCreate, MilestoneUpdate


class MilestoneRepository:
    """Repository for milestone CRUD operations."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.db = db
        self.organization_id = organization_id

    async def _set_context(self) -> None:
        """Set organization context for RLS."""
        await set_organization_context(self.db, self.organization_id)

    async def get_by_id(self, milestone_id: UUID) -> Milestone:
        """Get milestone by ID."""
        await self._set_context()
        result = await self.db.execute(
            select(Milestone).where(
                Milestone.id == milestone_id,
                Milestone.organization_id == self.organization_id,
            )
        )
        milestone = result.scalar_one_or_none()
        if not milestone:
            raise NotFoundError("Milestone", str(milestone_id))
        return milestone

    async def list_by_project(
        self, project_id: UUID, skip: int = 0, limit: int = 100
    ) -> tuple[list[Milestone], int]:
        """List milestones for a project."""
        await self._set_context()

        # Get total count
        count_result = await self.db.execute(
            select(func.count(Milestone.id)).where(
                Milestone.project_id == project_id,
                Milestone.organization_id == self.organization_id,
            )
        )
        total = count_result.scalar_one()

        # Get paginated results ordered by target_date
        result = await self.db.execute(
            select(Milestone)
            .where(
                Milestone.project_id == project_id,
                Milestone.organization_id == self.organization_id,
            )
            .offset(skip)
            .limit(limit)
            .order_by(Milestone.target_date.asc().nulls_last(), Milestone.created_at.asc())
        )
        milestones = list(result.scalars().all())

        return milestones, total

    async def list_all(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[Milestone], int]:
        """List all milestones for the organization."""
        await self._set_context()

        # Get total count
        count_result = await self.db.execute(
            select(func.count(Milestone.id)).where(
                Milestone.organization_id == self.organization_id,
            )
        )
        total = count_result.scalar_one()

        # Get paginated results ordered by target_date
        result = await self.db.execute(
            select(Milestone)
            .where(
                Milestone.organization_id == self.organization_id,
            )
            .offset(skip)
            .limit(limit)
            .order_by(Milestone.target_date.asc().nulls_last(), Milestone.created_at.asc())
        )
        milestones = list(result.scalars().all())

        return milestones, total

    async def create(self, data: MilestoneCreate) -> Milestone:
        """Create a new milestone."""
        try:
            await self._set_context()
            milestone = Milestone(**data.model_dump(), organization_id=self.organization_id)
            self.db.add(milestone)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(milestone)
            return milestone
        except Exception:
            await self.db.rollback()
            raise

    async def update(self, milestone_id: UUID, data: MilestoneUpdate) -> Milestone:
        """Update a milestone."""
        try:
            milestone = await self.get_by_id(milestone_id)
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(milestone, field, value)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(milestone)
            return milestone
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, milestone_id: UUID) -> None:
        """Delete a milestone."""
        try:
            milestone = await self.get_by_id(milestone_id)
            await self.db.delete(milestone)
            await self.db.flush()
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
