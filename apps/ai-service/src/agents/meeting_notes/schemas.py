from __future__ import annotations

"""Pydantic schemas for the Meeting Notes agent."""
from typing import Literal

from pydantic import BaseModel, Field


class ActionItem(BaseModel):
    """A task extracted from the meeting transcript."""

    description: str
    assignee_hint: str | None = None  # name or @mention found in text
    due_date_hint: str | None = None  # e.g. "by Friday", "next week", "EOD"
    priority: Literal["low", "medium", "high", "urgent"] = "medium"
    context: str | None = None  # surrounding sentence for reference


class Decision(BaseModel):
    """A decision reached during the meeting."""

    description: str
    made_by_hint: str | None = None  # person or group who made the decision
    context: str | None = None


class FollowUp(BaseModel):
    """Something to check back on after the meeting."""

    description: str
    owner_hint: str | None = None


class MeetingAnalysis(BaseModel):
    """Full structured analysis of a meeting transcript."""

    summary: str
    action_items: list[ActionItem]
    decisions: list[Decision]
    follow_ups: list[FollowUp]
    participants_detected: list[str]
    meeting_date_hint: str | None = None
    confidence: float = Field(ge=0.0, le=1.0, default=0.7)
    warnings: list[str] = []


class MeetingNotesParseResponse(BaseModel):
    """Response envelope for the meeting analysis endpoint."""

    analysis: MeetingAnalysis
    raw_text_length: int
    source_type: Literal["text", "file"] = "text"
