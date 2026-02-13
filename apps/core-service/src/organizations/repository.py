"""
Repository pattern for organization data access.
"""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import ConflictError, NotFoundError
from .models import Organization
from .schemas import OrganizationCreate, OrganizationUpdate


class OrganizationRepository:
    """Repository for organization CRUD operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, organization_id: UUID) -> Organization:
        """
        Get organization by ID.

        Args:
            organization_id: UUID of the organization

        Returns:
            Organization: The organization object

        Raises:
            NotFoundError: If organization not found
        """
        result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        organization = result.scalar_one_or_none()

        if not organization:
            raise NotFoundError("Organization", str(organization_id))

        return organization

    async def get_by_slug(self, slug: str) -> Organization | None:
        """
        Get organization by slug.

        Args:
            slug: URL slug of the organization

        Returns:
            Organization or None if not found
        """
        result = await self.db.execute(select(Organization).where(Organization.slug == slug))
        return result.scalar_one_or_none()

    async def list(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[Organization], int]:
        """
        List organizations with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (organizations list, total count)
        """
        # Get total count
        count_result = await self.db.execute(select(func.count(Organization.id)))
        total = count_result.scalar_one()

        # Get paginated results
        result = await self.db.execute(
            select(Organization).offset(skip).limit(limit).order_by(Organization.created_at.desc())
        )
        organizations = list(result.scalars().all())

        return organizations, total

    async def create(self, data: OrganizationCreate) -> Organization:
        """
        Create a new organization.

        Args:
            data: Organization creation data

        Returns:
            Organization: The created organization

        Raises:
            ConflictError: If slug already exists
        """
        # Check if slug already exists
        existing = await self.get_by_slug(data.slug)
        if existing:
            raise ConflictError(f"Organization with slug '{data.slug}' already exists")

        organization = Organization(**data.model_dump())
        self.db.add(organization)
        await self.db.flush()
        await self.db.refresh(organization)

        return organization

    async def update(
        self,
        organization_id: UUID,
        data: OrganizationUpdate,
    ) -> Organization:
        """
        Update an organization.

        Args:
            organization_id: UUID of the organization to update
            data: Update data

        Returns:
            Organization: The updated organization

        Raises:
            NotFoundError: If organization not found
            ConflictError: If new slug already exists
        """
        organization = await self.get_by_id(organization_id)

        # Check if slug is being changed and if it conflicts
        if data.slug and data.slug != organization.slug:
            existing = await self.get_by_slug(data.slug)
            if existing:
                raise ConflictError(f"Organization with slug '{data.slug}' already exists")

        # Update fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(organization, field, value)

        await self.db.flush()
        await self.db.refresh(organization)

        return organization

    async def delete(self, organization_id: UUID) -> None:
        """
        Delete an organization.

        Args:
            organization_id: UUID of the organization to delete

        Raises:
            NotFoundError: If organization not found
        """
        organization = await self.get_by_id(organization_id)
        await self.db.delete(organization)
        await self.db.flush()
