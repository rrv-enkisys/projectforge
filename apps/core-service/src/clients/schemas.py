"""Pydantic schemas for clients."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ClientBase(BaseModel):
    """Base schema for client data."""

    name: str = Field(..., min_length=1, max_length=255, description="Client name")
    contact_info: dict = Field(
        default_factory=dict,
        description="Contact information (email, phone, address, etc.)",
    )
    settings: dict = Field(default_factory=dict, description="Client-specific settings")


class ClientCreate(ClientBase):
    """Schema for creating a client."""

    pass


class ClientUpdate(BaseModel):
    """Schema for updating a client."""

    name: str | None = Field(None, min_length=1, max_length=255)
    contact_info: dict | None = None
    settings: dict | None = None


class ClientResponse(ClientBase):
    """Schema for client response."""

    id: UUID
    organization_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ClientListResponse(BaseModel):
    """Schema for paginated client list."""

    data: list[ClientResponse]
    total: int
    has_more: bool
