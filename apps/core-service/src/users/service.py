from __future__ import annotations

"""Business logic for users."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundError
from .models import OrgRole
from .repository import UserRepository
from .schemas import UserCreate, UserOrganizationResponse, UserResponse, UserUpdate, UserWithRole


class UserService:
    """Service layer for user business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.repository = UserRepository(db)

    async def get_user(self, user_id: UUID) -> UserResponse:
        """Get user by ID."""
        user = await self.repository.get_by_id(user_id)
        return UserResponse.model_validate(user)

    async def get_user_by_firebase_uid(self, firebase_uid: str) -> UserResponse | None:
        """Get user by Firebase UID."""
        user = await self.repository.get_by_firebase_uid(firebase_uid)
        return UserResponse.model_validate(user) if user else None

    async def list_users(self, skip: int = 0, limit: int = 100) -> tuple[list[UserResponse], int]:
        """List users with pagination."""
        users, total = await self.repository.list(skip=skip, limit=limit)
        return [UserResponse.model_validate(u) for u in users], total

    async def create_user(self, data: UserCreate) -> UserResponse:
        """Create a new user or sync from Firebase."""
        user = await self.repository.create(data)
        return UserResponse.model_validate(user)

    async def update_user(self, user_id: UUID, data: UserUpdate) -> UserResponse:
        """Update a user."""
        user = await self.repository.update(user_id, data)
        return UserResponse.model_validate(user)

    async def delete_user(self, user_id: UUID) -> None:
        """Delete a user."""
        await self.repository.delete(user_id)

    async def sync_from_firebase(self, firebase_uid: str, email: str, name: str) -> UserResponse:
        """
        Sync user from Firebase Auth.
        Creates user if doesn't exist, returns existing user otherwise.
        """
        existing = await self.repository.get_by_firebase_uid(firebase_uid)
        if existing:
            return UserResponse.model_validate(existing)

        # Create new user
        user_data = UserCreate(firebase_uid=firebase_uid, email=email, name=name)
        return await self.create_user(user_data)

    async def add_to_organization(
        self, user_id: UUID, organization_id: UUID, role: OrgRole = OrgRole.COLLABORATOR
    ) -> None:
        """Add user to organization."""
        await self.repository.add_to_organization(user_id, organization_id, role)

    async def update_organization_role(
        self, user_id: UUID, organization_id: UUID, role: OrgRole
    ) -> None:
        """Update user's role in organization."""
        await self.repository.update_role(user_id, organization_id, role)

    async def remove_from_organization(self, user_id: UUID, organization_id: UUID) -> None:
        """Remove user from organization."""
        await self.repository.remove_from_organization(user_id, organization_id)

    async def get_user_primary_organization(self, firebase_uid: str) -> UserOrganizationResponse:
        """
        Get user's primary organization by Firebase UID.
        This is used by the API Gateway to establish tenant context.

        Returns the first organization the user belongs to.
        In the future, we could add a 'default_organization_id' field to the User model.
        """
        # First, get the user
        user = await self.repository.get_by_firebase_uid(firebase_uid)
        if not user:
            raise NotFoundError("User", firebase_uid)

        # Get user's organizations
        memberships = await self.repository.get_user_organizations(user.id)
        if not memberships:
            raise NotFoundError(
                "Organization membership",
                f"User {firebase_uid} is not a member of any organization",
            )

        # Return the first organization (primary)
        # In the future, we could sort by role (admin first) or add a default org field
        primary = memberships[0]
        return UserOrganizationResponse(
            organization_id=primary.organization_id,
            role=primary.role,
        )
