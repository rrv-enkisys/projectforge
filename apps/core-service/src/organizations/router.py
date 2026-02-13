"""
FastAPI router for organization endpoints.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ..common.dependencies import DatabaseSession
from .schemas import (
    OrganizationCreate,
    OrganizationListResponse,
    OrganizationResponse,
    OrganizationUpdate,
)
from .service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["organizations"])


def get_service(db: DatabaseSession) -> OrganizationService:
    """Dependency to get organization service."""
    return OrganizationService(db)


@router.get(
    "",
    response_model=OrganizationListResponse,
    summary="List organizations",
    description="Get a paginated list of all organizations",
)
async def list_organizations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    service: OrganizationService = Depends(get_service),
) -> OrganizationListResponse:
    """
    List all organizations with pagination.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum records to return (default: 100, max: 1000)
    """
    organizations, total = await service.list_organizations(skip=skip, limit=limit)

    return OrganizationListResponse(
        data=organizations,
        total=total,
        has_more=(skip + len(organizations)) < total,
    )


@router.get(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Get organization",
    description="Get a specific organization by ID",
)
async def get_organization(
    organization_id: UUID,
    service: OrganizationService = Depends(get_service),
) -> OrganizationResponse:
    """
    Get an organization by ID.

    - **organization_id**: UUID of the organization
    """
    return await service.get_organization(organization_id)


@router.post(
    "",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create organization",
    description="Create a new organization",
)
async def create_organization(
    data: OrganizationCreate,
    service: OrganizationService = Depends(get_service),
) -> OrganizationResponse:
    """
    Create a new organization.

    - **name**: Organization name
    - **slug**: URL-friendly slug (lowercase, numbers, hyphens only)
    - **settings**: Optional settings object
    - **branding**: Optional branding configuration
    """
    return await service.create_organization(data)


@router.patch(
    "/{organization_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
    description="Update an existing organization",
)
async def update_organization(
    organization_id: UUID,
    data: OrganizationUpdate,
    service: OrganizationService = Depends(get_service),
) -> OrganizationResponse:
    """
    Update an organization.

    - **organization_id**: UUID of the organization
    - Only provided fields will be updated
    """
    return await service.update_organization(organization_id, data)


@router.delete(
    "/{organization_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete organization",
    description="Delete an organization and all related data",
)
async def delete_organization(
    organization_id: UUID,
    service: OrganizationService = Depends(get_service),
) -> None:
    """
    Delete an organization.

    - **organization_id**: UUID of the organization
    - ⚠️  This will cascade delete all related data
    """
    await service.delete_organization(organization_id)
