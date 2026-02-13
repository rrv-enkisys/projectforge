"""FastAPI router for milestone endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ..common.dependencies import DatabaseSession, OrganizationId
from .schemas import (
    MilestoneComplete,
    MilestoneCreate,
    MilestoneListResponse,
    MilestoneResponse,
    MilestoneUpdate,
)
from .service import MilestoneService

router = APIRouter(prefix="/milestones", tags=["milestones"])


def get_service(db: DatabaseSession, org_id: OrganizationId) -> MilestoneService:
    """Dependency to get milestone service."""
    return MilestoneService(db, org_id)


@router.get("", response_model=MilestoneListResponse)
async def list_milestones(
    project_id: UUID = Query(..., description="Project ID to filter milestones"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: MilestoneService = Depends(get_service),
) -> MilestoneListResponse:
    """List all milestones for a project, ordered by target date."""
    milestones, total = await service.list_milestones(project_id, skip, limit)
    return MilestoneListResponse(
        data=milestones,
        total=total,
        has_more=(skip + len(milestones)) < total,
    )


@router.get("/{milestone_id}", response_model=MilestoneResponse)
async def get_milestone(
    milestone_id: UUID,
    service: MilestoneService = Depends(get_service),
) -> MilestoneResponse:
    """Get a specific milestone by ID."""
    return await service.get_milestone(milestone_id)


@router.post("", response_model=MilestoneResponse, status_code=status.HTTP_201_CREATED)
async def create_milestone(
    data: MilestoneCreate,
    service: MilestoneService = Depends(get_service),
) -> MilestoneResponse:
    """Create a new milestone."""
    return await service.create_milestone(data)


@router.patch("/{milestone_id}", response_model=MilestoneResponse)
async def update_milestone(
    milestone_id: UUID,
    data: MilestoneUpdate,
    service: MilestoneService = Depends(get_service),
) -> MilestoneResponse:
    """Update an existing milestone."""
    return await service.update_milestone(milestone_id, data)


@router.post("/{milestone_id}/complete", response_model=MilestoneResponse)
async def mark_milestone_completed(
    milestone_id: UUID,
    data: MilestoneComplete,
    service: MilestoneService = Depends(get_service),
) -> MilestoneResponse:
    """Mark a milestone as completed."""
    return await service.mark_completed(milestone_id)


@router.delete("/{milestone_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_milestone(
    milestone_id: UUID,
    service: MilestoneService = Depends(get_service),
) -> None:
    """Delete a milestone."""
    await service.delete_milestone(milestone_id)
