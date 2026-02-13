"""
Pydantic schemas for organizations.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class OrganizationBase(BaseModel):
    """Base schema for organization data."""

    name: str = Field(..., min_length=1, max_length=255, description="Organization name")
    slug: str = Field(
        ...,
        min_length=1,
        max_length=255,
        pattern=r"^[a-z0-9-]+$",
        description="URL-friendly slug (lowercase, numbers, hyphens)",
    )
    settings: dict = Field(default_factory=dict, description="Organization settings")
    branding: dict = Field(default_factory=dict, description="Branding configuration")

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        """Ensure slug is lowercase and valid."""
        return v.lower().strip()


class OrganizationCreate(OrganizationBase):
    """Schema for creating a new organization."""

    pass


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization."""

    name: str | None = Field(None, min_length=1, max_length=255)
    slug: str | None = Field(None, min_length=1, max_length=255, pattern=r"^[a-z0-9-]+$")
    settings: dict | None = None
    branding: dict | None = None

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, v: str | None) -> str | None:
        """Ensure slug is lowercase and valid."""
        return v.lower().strip() if v else None


class OrganizationResponse(OrganizationBase):
    """Schema for organization response."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class OrganizationListResponse(BaseModel):
    """Schema for paginated organization list."""

    data: list[OrganizationResponse]
    total: int
    has_more: bool
