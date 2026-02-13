"""
Custom exceptions and exception handlers for FastAPI.
"""
from typing import Any

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse


class ProjectForgeException(Exception):
    """Base exception for ProjectForge application."""

    def __init__(self, message: str, code: str = "ERROR") -> None:
        self.message = message
        self.code = code
        super().__init__(message)


class NotFoundError(ProjectForgeException):
    """Raised when a resource is not found."""

    def __init__(self, resource: str, identifier: str | None = None) -> None:
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(message, code="NOT_FOUND")


class ValidationError(ProjectForgeException):
    """Raised when validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        self.field = field
        super().__init__(message, code="VALIDATION_ERROR")


class PermissionDeniedError(ProjectForgeException):
    """Raised when user doesn't have permission for an action."""

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message, code="PERMISSION_DENIED")


class UnauthorizedError(ProjectForgeException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Unauthorized") -> None:
        super().__init__(message, code="UNAUTHORIZED")


class ConflictError(ProjectForgeException):
    """Raised when there's a conflict (e.g., duplicate resource)."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="CONFLICT")


# Exception handlers for FastAPI


async def not_found_error_handler(
    request: Request,
    exc: NotFoundError,
) -> JSONResponse:
    """Handle NotFoundError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


async def validation_error_handler(
    request: Request,
    exc: ValidationError,
) -> JSONResponse:
    """Handle ValidationError exceptions."""
    content: dict[str, Any] = {
        "error": {
            "code": exc.code,
            "message": exc.message,
        }
    }
    if exc.field:
        content["error"]["field"] = exc.field

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=content,
    )


async def permission_denied_error_handler(
    request: Request,
    exc: PermissionDeniedError,
) -> JSONResponse:
    """Handle PermissionDeniedError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


async def unauthorized_error_handler(
    request: Request,
    exc: UnauthorizedError,
) -> JSONResponse:
    """Handle UnauthorizedError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
        headers={"WWW-Authenticate": "Bearer"},
    )


async def conflict_error_handler(
    request: Request,
    exc: ConflictError,
) -> JSONResponse:
    """Handle ConflictError exceptions."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
            }
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle any unhandled exceptions."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            }
        },
    )
