from __future__ import annotations

"""Repository for client data access."""
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..common.exceptions import NotFoundError
from ..database import set_organization_context
from .models import Client
from .schemas import ClientCreate, ClientUpdate


class ClientRepository:
    """Repository for client CRUD operations."""

    def __init__(self, db: AsyncSession, organization_id: UUID) -> None:
        self.db = db
        self.organization_id = organization_id

    async def _set_context(self) -> None:
        """Set organization context for RLS."""
        await set_organization_context(self.db, self.organization_id)

    async def get_by_id(self, client_id: UUID) -> Client:
        """Get client by ID."""
        await self._set_context()
        result = await self.db.execute(
            select(Client).where(
                Client.id == client_id,
                Client.organization_id == self.organization_id,
            )
        )
        client = result.scalar_one_or_none()
        if not client:
            raise NotFoundError("Client", str(client_id))
        return client

    async def list(self, skip: int = 0, limit: int = 100) -> tuple[list[Client], int]:
        """List clients with pagination."""
        await self._set_context()

        # Get total count
        count_result = await self.db.execute(
            select(func.count(Client.id)).where(Client.organization_id == self.organization_id)
        )
        total = count_result.scalar_one()

        # Get paginated results
        result = await self.db.execute(
            select(Client)
            .where(Client.organization_id == self.organization_id)
            .offset(skip)
            .limit(limit)
            .order_by(Client.name.asc())
        )
        clients = list(result.scalars().all())

        return clients, total

    async def create(self, data: ClientCreate) -> Client:
        """Create a new client."""
        try:
            await self._set_context()
            client = Client(**data.model_dump(), organization_id=self.organization_id)
            self.db.add(client)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(client)
            return client
        except Exception:
            await self.db.rollback()
            raise

    async def update(self, client_id: UUID, data: ClientUpdate) -> Client:
        """Update a client."""
        try:
            client = await self.get_by_id(client_id)
            update_data = data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(client, field, value)
            await self.db.flush()
            await self.db.commit()
            await self.db.refresh(client)
            return client
        except Exception:
            await self.db.rollback()
            raise

    async def delete(self, client_id: UUID) -> None:
        """Delete a client."""
        try:
            client = await self.get_by_id(client_id)
            await self.db.delete(client)
            await self.db.flush()
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            raise
