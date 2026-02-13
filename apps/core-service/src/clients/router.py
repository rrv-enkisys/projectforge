"""FastAPI router for client endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ..common.dependencies import DatabaseSession, OrganizationId
from .schemas import ClientCreate, ClientListResponse, ClientResponse, ClientUpdate
from .service import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


def get_service(db: DatabaseSession, org_id: OrganizationId) -> ClientService:
    """Dependency to get client service."""
    return ClientService(db, org_id)


@router.get("", response_model=ClientListResponse, summary="List clients")
async def list_clients(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: ClientService = Depends(get_service),
) -> ClientListResponse:
    """List all clients for the organization."""
    clients, total = await service.list_clients(skip=skip, limit=limit)
    return ClientListResponse(
        data=clients,
        total=total,
        has_more=(skip + len(clients)) < total,
    )


@router.get("/{client_id}", response_model=ClientResponse, summary="Get client")
async def get_client(
    client_id: UUID,
    service: ClientService = Depends(get_service),
) -> ClientResponse:
    """Get a specific client by ID."""
    return await service.get_client(client_id)


@router.post("", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    data: ClientCreate,
    service: ClientService = Depends(get_service),
) -> ClientResponse:
    """Create a new client."""
    return await service.create_client(data)


@router.patch("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: UUID,
    data: ClientUpdate,
    service: ClientService = Depends(get_service),
) -> ClientResponse:
    """Update an existing client."""
    return await service.update_client(client_id, data)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: UUID,
    service: ClientService = Depends(get_service),
) -> None:
    """Delete a client."""
    await service.delete_client(client_id)
