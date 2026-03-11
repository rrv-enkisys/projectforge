from __future__ import annotations

"""Pydantic schemas for the SOW Parser agent."""
from typing import Literal

from pydantic import BaseModel, Field


class SOWSection(BaseModel):
    """A section extracted from the SOW document."""

    name: str
    content: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.8)


class TaskSuggestion(BaseModel):
    """A suggested task derived from the SOW."""

    title: str
    description: str
    estimated_hours: int | None = None
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    milestone_index: int | None = None  # index into the milestones list


class MilestoneSuggestion(BaseModel):
    """A suggested milestone derived from the SOW."""

    title: str
    description: str
    target_date_offset_days: int | None = None  # days from project start


class ProjectSuggestion(BaseModel):
    """High-level project metadata extracted from the SOW."""

    name: str
    description: str
    estimated_duration_days: int | None = None
    estimated_budget: float | None = None
    currency: str = "USD"


class SOWParseResponse(BaseModel):
    """Full structured output of the SOW Parser agent."""

    project: ProjectSuggestion
    milestones: list[MilestoneSuggestion]
    tasks: list[TaskSuggestion]
    raw_sections: list[SOWSection]
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    warnings: list[str] = []
