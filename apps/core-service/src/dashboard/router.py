"""FastAPI router for dashboard endpoints."""
from fastapi import APIRouter, Depends

from ..common.dependencies import DatabaseSession, OrganizationId
from .schemas import DashboardStatsResponse
from .service import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


def get_service(db: DatabaseSession, org_id: OrganizationId) -> DashboardService:
    """Dependency to get dashboard service."""
    return DashboardService(db, org_id)


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    service: DashboardService = Depends(get_service),
) -> DashboardStatsResponse:
    """Get organization dashboard statistics."""
    stats = await service.get_stats()
    return DashboardStatsResponse(data=stats)
