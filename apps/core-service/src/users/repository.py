"""Repository for user data access."""
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..common.exceptions import ConflictError, NotFoundError
from .models import OrgRole, OrganizationMember, User
from .schemas import OrganizationMemberCreate, UserCreate, UserUpdate


class UserRepository:
    """Repository for user CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: UUID) -> User:
        """Get user by ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundError("User", str(user_id))
        return user

    async def get_by_firebase_uid(self, firebase_uid: str) -> User | None:
        """Get user by Firebase UID."""
        result = await self.db.execute(select(User).where(User.firebase_uid == firebase_uid))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Get user by email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 100) -> tuple[list[User], int]:
        """List users with pagination."""
        count_result = await self.db.execute(select(func.count(User.id)))
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        users = list(result.scalars().all())

        return users, total

    async def create(self, data: UserCreate) -> User:
        """Create a new user."""
        # Check if firebase_uid or email already exists
        existing_uid = await self.get_by_firebase_uid(data.firebase_uid)
        if existing_uid:
            raise ConflictError(f"User with Firebase UID '{data.firebase_uid}' already exists")

        existing_email = await self.get_by_email(data.email)
        if existing_email:
            raise ConflictError(f"User with email '{data.email}' already exists")

        user = User(**data.model_dump())
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user_id: UUID, data: UserUpdate) -> User:
        """Update a user."""
        user = await self.get_by_id(user_id)
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(user, field, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def delete(self, user_id: UUID) -> None:
        """Delete a user."""
        user = await self.get_by_id(user_id)
        await self.db.delete(user)
        await self.db.flush()

    async def get_user_organizations(self, user_id: UUID) -> list[OrganizationMember]:
        """Get all organizations a user belongs to."""
        result = await self.db.execute(
            select(OrganizationMember).where(OrganizationMember.user_id == user_id)
        )
        return list(result.scalars().all())

    async def add_to_organization(
        self, user_id: UUID, organization_id: UUID, role: OrgRole = OrgRole.COLLABORATOR
    ) -> OrganizationMember:
        """Add a user to an organization."""
        # Check if membership already exists
        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ConflictError("User is already a member of this organization")

        member = OrganizationMember(
            user_id=user_id,
            organization_id=organization_id,
            role=role,
            joined_at=datetime.utcnow(),
        )
        self.db.add(member)
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def update_role(
        self, user_id: UUID, organization_id: UUID, role: OrgRole
    ) -> OrganizationMember:
        """Update user's role in an organization."""
        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError("Organization membership")

        member.role = role
        await self.db.flush()
        await self.db.refresh(member)
        return member

    async def remove_from_organization(self, user_id: UUID, organization_id: UUID) -> None:
        """Remove a user from an organization."""
        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.user_id == user_id,
                OrganizationMember.organization_id == organization_id,
            )
        )
        member = result.scalar_one_or_none()
        if not member:
            raise NotFoundError("Organization membership")

        await self.db.delete(member)
        await self.db.flush()
