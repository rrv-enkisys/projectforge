"""FastAPI router for project endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ..common.dependencies import DatabaseSession, OrganizationId
from .schemas import ProjectCreate, ProjectListResponse, ProjectResponse, ProjectStatistics, ProjectUpdate
from .service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_service(db: DatabaseSession, org_id: OrganizationId) -> ProjectService:
    """Dependency to get project service."""
    return ProjectService(db, org_id)


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ProjectService = Depends(get_service),
) -> ProjectListResponse:
    """List all projects for the organization."""
    projects, total = await service.list_projects(skip=skip, limit=limit)
    return ProjectListResponse(
        data=projects,
        total=total,
        has_more=(skip + len(projects)) < total,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: UUID,
    service: ProjectService = Depends(get_service),
) -> ProjectResponse:
    """Get a specific project by ID."""
    return await service.get_project(project_id)


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends(get_service),
) -> ProjectResponse:
    """Create a new project."""
    return await service.create_project(data)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: UUID,
    data: ProjectUpdate,
    service: ProjectService = Depends(get_service),
) -> ProjectResponse:
    """Update an existing project."""
    return await service.update_project(project_id, data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: UUID,
    service: ProjectService = Depends(get_service),
) -> None:
    """Delete a project."""
    await service.delete_project(project_id)


@router.get("/{project_id}/statistics", response_model=ProjectStatistics)
async def get_project_statistics(
    project_id: UUID,
    service: ProjectService = Depends(get_service),
) -> ProjectStatistics:
    """Get comprehensive statistics for a project."""
    return await service.get_project_statistics(project_id)
