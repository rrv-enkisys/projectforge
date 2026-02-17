from __future__ import annotations

"""Pydantic schemas for users."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from .models import OrgRole


class UserBase(BaseModel):
    """Base schema for user data."""

    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    avatar_url: str | None = None
    contact_info: dict = Field(default_factory=dict)


class UserCreate(UserBase):
    """Schema for creating a user."""

    firebase_uid: str = Field(..., description="Firebase Auth UID")


class UserUpdate(BaseModel):
    """Schema for updating a user."""

    name: str | None = Field(None, min_length=1, max_length=255)
    avatar_url: str | None = None
    contact_info: dict | None = None


class UserResponse(UserBase):
    """Schema for user response."""

    id: UUID
    firebase_uid: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserWithRole(UserResponse):
    """User response with organization role."""

    role: OrgRole
    organization_id: UUID


class UserListResponse(BaseModel):
    """Schema for paginated user list."""

    data: list[UserResponse]
    total: int
    has_more: bool


class OrganizationMemberCreate(BaseModel):
    """Schema for adding a user to an organization."""

    user_id: UUID
    role: OrgRole = OrgRole.COLLABORATOR


class OrganizationMemberUpdate(BaseModel):
    """Schema for updating organization membership."""

    role: OrgRole


class OrganizationMemberResponse(BaseModel):
    """Schema for organization member response."""

    id: UUID
    organization_id: UUID
    user_id: UUID
    role: OrgRole
    invited_at: datetime | None
    joined_at: datetime | None
    created_at: datetime
    updated_at: datetime

    # Include user information
    user: UserResponse | None = None

    model_config = {"from_attributes": True}
