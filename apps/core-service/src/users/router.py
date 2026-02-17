"""FastAPI router for user endpoints."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from ..common.dependencies import AuthenticatedUser, DatabaseSession
from .models import OrgRole
from .schemas import (
    OrganizationMemberCreate,
    OrganizationMemberUpdate,
    UserCreate,
    UserListResponse,
    UserOrganizationResponse,
    UserResponse,
    UserUpdate,
    UserWithRole,
)
from .service import UserService

router = APIRouter(prefix="/users", tags=["users"])


def get_service(db: DatabaseSession) -> UserService:
    """Dependency to get user service."""
    return UserService(db)


@router.get("/me", response_model=UserResponse, summary="Get current user")
async def get_current_user_profile(
    current_user: AuthenticatedUser,
    service: UserService = Depends(get_service),
) -> UserResponse:
    """Get the current authenticated user's profile."""
    # Try to get user from database
    user = await service.get_user_by_firebase_uid(current_user.uid)

    if not user:
        # User doesn't exist in database, sync from Firebase
        user = await service.sync_from_firebase(
            firebase_uid=current_user.uid,
            email=current_user.email,
            name=current_user.name or current_user.email.split("@")[0],
        )

    return user


@router.get("", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    service: UserService = Depends(get_service),
) -> UserListResponse:
    """List all users."""
    users, total = await service.list_users(skip=skip, limit=limit)
    return UserListResponse(
        data=users,
        total=total,
        has_more=(skip + len(users)) < total,
    )


@router.get("/firebase/{firebase_uid}/organization", response_model=UserOrganizationResponse)
async def get_user_organization_by_firebase_uid(
    firebase_uid: str,
    service: UserService = Depends(get_service),
) -> UserOrganizationResponse:
    """
    Get user's primary organization by Firebase UID.

    This endpoint is used by the API Gateway to establish tenant context.
    Returns the organization_id and role of the user's primary organization.
    """
    return await service.get_user_primary_organization(firebase_uid)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    service: UserService = Depends(get_service),
) -> UserResponse:
    """Get a specific user by ID."""
    return await service.get_user(user_id)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_service),
) -> UserResponse:
    """Create a new user (typically called during Firebase Auth sync)."""
    return await service.create_user(data)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    data: UserUpdate,
    service: UserService = Depends(get_service),
) -> UserResponse:
    """Update an existing user."""
    return await service.update_user(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    service: UserService = Depends(get_service),
) -> None:
    """Delete a user."""
    await service.delete_user(user_id)


# Organization membership endpoints
@router.post("/{user_id}/organizations/{organization_id}", status_code=status.HTTP_201_CREATED)
async def add_user_to_organization(
    user_id: UUID,
    organization_id: UUID,
    data: OrganizationMemberCreate | None = None,
    service: UserService = Depends(get_service),
) -> dict[str, str]:
    """Add a user to an organization with a specific role."""
    role = data.role if data else OrgRole.COLLABORATOR
    await service.add_to_organization(user_id, organization_id, role)
    return {"message": "User added to organization successfully"}


@router.patch("/{user_id}/organizations/{organization_id}")
async def update_user_organization_role(
    user_id: UUID,
    organization_id: UUID,
    data: OrganizationMemberUpdate,
    service: UserService = Depends(get_service),
) -> dict[str, str]:
    """Update a user's role in an organization."""
    await service.update_organization_role(user_id, organization_id, data.role)
    return {"message": "User role updated successfully"}


@router.delete("/{user_id}/organizations/{organization_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_organization(
    user_id: UUID,
    organization_id: UUID,
    service: UserService = Depends(get_service),
) -> None:
    """Remove a user from an organization."""
    await service.remove_from_organization(user_id, organization_id)
