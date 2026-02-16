"""AI Copilot API endpoints"""
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Header

from .schemas import (
    ProjectAnalysis,
    ProjectAnalysisRequest,
    RiskAnalysisResponse,
    Suggestion,
    TimelinePrediction,
)
from .service import CopilotService

router = APIRouter(prefix="/copilot", tags=["copilot"])


@router.post("/analyze", response_model=ProjectAnalysis)
async def analyze_project(
    data: ProjectAnalysisRequest,
    service: CopilotService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> ProjectAnalysis:
    """
    Perform comprehensive AI-powered project analysis.
    Returns health metrics, risks, timeline prediction, and AI insights.
    """
    # In a real implementation, fetch project data from database
    # For now, using mock data structure
    project_data = {
        "id": str(data.project_id),
        "organization_id": str(x_organization_id),
        "tasks": [],  # Would fetch from DB
        "milestones": [],  # Would fetch from DB
    }

    result = await service.analyze_project(project_data)
    return ProjectAnalysis(**result)


@router.post("/risks", response_model=RiskAnalysisResponse)
async def get_risk_analysis(
    project_id: UUID,
    service: CopilotService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> RiskAnalysisResponse:
    """
    Get detailed risk analysis with AI-generated mitigation strategies.
    """
    project_data = {
        "id": str(project_id),
        "organization_id": str(x_organization_id),
        "tasks": [],
        "milestones": [],
    }

    result = await service.get_risk_analysis(project_data)
    return RiskAnalysisResponse(**result)


@router.post("/suggestions", response_model=list[Suggestion])
async def get_suggestions(
    project_id: UUID,
    service: CopilotService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> list[Suggestion]:
    """
    Get AI-generated suggestions for project improvement.
    """
    project_data = {
        "id": str(project_id),
        "organization_id": str(x_organization_id),
        "tasks": [],
        "milestones": [],
    }

    suggestions = await service.get_suggestions(project_data)
    return suggestions


@router.post("/timeline", response_model=TimelinePrediction)
async def predict_timeline(
    project_id: UUID,
    include_historical: bool = False,
    service: CopilotService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> TimelinePrediction:
    """
    Predict project completion timeline with AI analysis.
    Optionally includes analysis based on historical project data.
    """
    project_data = {
        "id": str(project_id),
        "organization_id": str(x_organization_id),
        "tasks": [],
        "milestones": [],
    }

    historical_data = {} if include_historical else None

    result = await service.predict_timeline(project_data, historical_data)
    return TimelinePrediction(**result)
