"""
FastAPI dependencies for authentication, authorization, and database access.
"""
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from firebase_admin import auth, credentials, initialize_app
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from .exceptions import UnauthorizedError

# Initialize Firebase Admin SDK
try:
    if settings.firebase_credentials_path:
        cred = credentials.Certificate(settings.firebase_credentials_path)
    else:
        # Use default credentials in GCP
        cred = credentials.ApplicationDefault()

    initialize_app(cred, {"projectId": settings.firebase_project_id})
except Exception:
    # Firebase already initialized or no credentials available
    pass


class CurrentUser:
    """
    Represents the currently authenticated user.
    """

    def __init__(
        self,
        uid: str,
        email: str,
        name: str | None = None,
        organization_id: UUID | None = None,
    ) -> None:
        self.uid = uid
        self.email = email
        self.name = name
        self.organization_id = organization_id


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
) -> CurrentUser:
    """
    Dependency to get the current authenticated user from Firebase JWT.

    Args:
        authorization: The Authorization header with Bearer token

    Returns:
        CurrentUser: The authenticated user information

    Raises:
        UnauthorizedError: If token is invalid or missing

    Usage:
        @app.get("/me")
        async def get_me(user: CurrentUser = Depends(get_current_user)):
            return {"uid": user.uid, "email": user.email}
    """
    if not authorization:
        raise UnauthorizedError("Missing authorization header")

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise UnauthorizedError("Invalid authorization header format")

    token = parts[1]

    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(token)

        # Extract user information
        uid = decoded_token["uid"]
        email = decoded_token.get("email", "")
        name = decoded_token.get("name")

        # Extract organization_id from custom claims
        organization_id = None
        custom_claims = decoded_token.get("organizations", {})
        default_org = decoded_token.get("default_organization")

        if default_org:
            try:
                organization_id = UUID(default_org)
            except ValueError:
                pass

        return CurrentUser(
            uid=uid,
            email=email,
            name=name,
            organization_id=organization_id,
        )

    except auth.InvalidIdTokenError:
        raise UnauthorizedError("Invalid authentication token")
    except auth.ExpiredIdTokenError:
        raise UnauthorizedError("Authentication token has expired")
    except Exception as e:
        raise UnauthorizedError(f"Authentication failed: {str(e)}")


async def get_organization_id(
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> UUID:
    """
    Dependency to get the organization_id from the current user.

    Args:
        user: The current authenticated user

    Returns:
        UUID: The organization ID

    Raises:
        UnauthorizedError: If user doesn't have an organization

    Usage:
        @app.get("/projects")
        async def get_projects(org_id: UUID = Depends(get_organization_id)):
            ...
    """
    if not user.organization_id:
        raise UnauthorizedError("User does not have an organization assigned")

    return user.organization_id


# Type aliases for cleaner dependency injection
DatabaseSession = Annotated[AsyncSession, Depends(get_db)]
AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
OrganizationId = Annotated[UUID, Depends(get_organization_id)]
