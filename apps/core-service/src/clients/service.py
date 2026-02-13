"""Business logic for clients."""
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .repository import ClientRepository
from .schemas import ClientCreate, ClientResponse, ClientUpdate


class ClientService:
    """Service layer for client business logic."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.repository = ClientRepository(db, organization_id)

    async def get_client(self, client_id: UUID) -> ClientResponse:
        """Get client by ID."""
        client = await self.repository.get_by_id(client_id)
        return ClientResponse.model_validate(client)

    async def list_clients(
        self, skip: int = 0, limit: int = 100
    ) -> tuple[list[ClientResponse], int]:
        """List clients with pagination."""
        clients, total = await self.repository.list(skip=skip, limit=limit)
        return [ClientResponse.model_validate(c) for c in clients], total

    async def create_client(self, data: ClientCreate) -> ClientResponse:
        """Create a new client."""
        client = await self.repository.create(data)
        return ClientResponse.model_validate(client)

    async def update_client(self, client_id: UUID, data: ClientUpdate) -> ClientResponse:
        """Update a client."""
        client = await self.repository.update(client_id, data)
        return ClientResponse.model_validate(client)

    async def delete_client(self, client_id: UUID) -> None:
        """Delete a client."""
        await self.repository.delete(client_id)
