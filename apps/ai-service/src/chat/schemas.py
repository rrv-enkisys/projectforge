from __future__ import annotations

"""Chat schemas"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CreateSession(BaseModel):
    """Schema for creating a chat session"""

    project_id: UUID
    title: str | None = None


class MessageCreate(BaseModel):
    """Schema for creating a message"""

    session_id: UUID
    content: str = Field(..., min_length=1, max_length=5000)


class MessageResponse(BaseModel):
    """Schema for message response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    session_id: UUID
    role: str
    content: str
    created_at: datetime


class SessionResponse(BaseModel):
    """Schema for session response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    organization_id: UUID
    user_id: str
    title: str | None
    created_at: datetime
    updated_at: datetime


class SessionWithMessages(SessionResponse):
    """Session response with messages"""

    messages: list[MessageResponse]
