"""Copilot schemas"""
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ProjectAnalysisRequest(BaseModel):
    """Request for project analysis"""

    project_id: UUID
    include_tasks: bool = True
    include_milestones: bool = True


class HealthAnalysis(BaseModel):
    """Project health analysis"""

    score: int
    status: str
    issues: list[str]
    task_completion_rate: float
    overdue_tasks_count: int
    overdue_milestones_count: int


class Risk(BaseModel):
    """Detected risk"""

    type: str
    severity: str
    description: str
    impact: str
    mitigation: str


class CompletionPrediction(BaseModel):
    """Timeline prediction"""

    predicted_date: str | None
    confidence: str
    estimated_days_remaining: int | None = None
    completion_rate: float | None = None
    reasoning: str


class ProjectAnalysis(BaseModel):
    """Complete project analysis"""

    health: HealthAnalysis
    risks: list[Risk]
    completion_prediction: CompletionPrediction
    ai_insights: str
    timestamp: str


class RiskAnalysisResponse(BaseModel):
    """Risk analysis response"""

    detected_risks: list[Risk]
    ai_analysis: str
    risk_count: int
    severity_breakdown: dict[str, int]


class Suggestion(BaseModel):
    """AI suggestion"""

    category: str
    action: str
    priority: str


class TimelinePrediction(BaseModel):
    """Timeline prediction with AI analysis"""

    predicted_date: str | None
    confidence: str
    estimated_days_remaining: int | None = None
    completion_rate: float | None = None
    reasoning: str
    ai_analysis: str | None = None
    factors: list[str]
