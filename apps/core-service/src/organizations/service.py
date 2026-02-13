"""
Business logic for organizations.
"""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .repository import OrganizationRepository
from .schemas import OrganizationCreate, OrganizationResponse, OrganizationUpdate


class OrganizationService:
    """Service layer for organization business logic."""

    def __init__(self, db: AsyncSession) -> None:
        self.repository = OrganizationRepository(db)

    async def get_organization(self, organization_id: UUID) -> OrganizationResponse:
        """
        Get organization by ID.

        Args:
            organization_id: UUID of the organization

        Returns:
            OrganizationResponse: Organization data
        """
        organization = await self.repository.get_by_id(organization_id)
        return OrganizationResponse.model_validate(organization)

    async def list_organizations(
        self,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[list[OrganizationResponse], int]:
        """
        List organizations with pagination.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (organizations list, total count)
        """
        organizations, total = await self.repository.list(skip=skip, limit=limit)
        return (
            [OrganizationResponse.model_validate(org) for org in organizations],
            total,
        )

    async def create_organization(self, data: OrganizationCreate) -> OrganizationResponse:
        """
        Create a new organization.

        Args:
            data: Organization creation data

        Returns:
            OrganizationResponse: The created organization
        """
        organization = await self.repository.create(data)
        return OrganizationResponse.model_validate(organization)

    async def update_organization(
        self,
        organization_id: UUID,
        data: OrganizationUpdate,
    ) -> OrganizationResponse:
        """
        Update an organization.

        Args:
            organization_id: UUID of the organization
            data: Update data

        Returns:
            OrganizationResponse: The updated organization
        """
        organization = await self.repository.update(organization_id, data)
        return OrganizationResponse.model_validate(organization)

    async def delete_organization(self, organization_id: UUID) -> None:
        """
        Delete an organization.

        Args:
            organization_id: UUID of the organization
        """
        await self.repository.delete(organization_id)
