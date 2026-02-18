from __future__ import annotations

"""AI Copilot API endpoints"""
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query

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
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
) -> ProjectAnalysis:
    """
    Perform comprehensive AI-powered project analysis.
    Fetches real project data and returns health metrics, risks,
    timeline prediction, and AI insights.
    """
    result = await service.analyze_project_by_id(data.project_id, x_organization_id)
    return ProjectAnalysis(**result)


@router.post("/risks", response_model=RiskAnalysisResponse)
async def get_risk_analysis(
    project_id: UUID,
    service: CopilotService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
) -> RiskAnalysisResponse:
    """
    Get detailed risk analysis with AI-generated mitigation strategies.
    Fetches real project data for analysis.
    """
    project_data = await service.project_data_repo.get_project_data(project_id, x_organization_id)
    result = await service.get_risk_analysis(project_data)
    return RiskAnalysisResponse(**result)


@router.post("/suggestions", response_model=list[Suggestion])
async def get_suggestions(
    project_id: UUID,
    service: CopilotService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
) -> list[Suggestion]:
    """
    Get AI-generated suggestions for project improvement.
    Fetches real project data for context.
    """
    project_data = await service.project_data_repo.get_project_data(project_id, x_organization_id)
    suggestions = await service.get_suggestions(project_data)
    return suggestions


@router.post("/timeline", response_model=TimelinePrediction)
async def predict_timeline(
    project_id: UUID,
    include_historical: bool = Query(False),
    service: CopilotService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
) -> TimelinePrediction:
    """
    Predict project completion timeline with AI analysis.
    Uses real task and milestone data for prediction.
    """
    project_data = await service.project_data_repo.get_project_data(project_id, x_organization_id)
    historical_data: dict | None = {} if include_historical else None
    result = await service.predict_timeline(project_data, historical_data)
    return TimelinePrediction(**result)
