"""
ProjectForge Core Service - Main FastAPI Application

This is the main entry point for the Core Service, which handles:
- Organizations, clients, users
- Projects, tasks, milestones
- Multi-tenant data isolation with RLS
"""
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .common.exceptions import (
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    UnauthorizedError,
    ValidationError,
    conflict_error_handler,
    generic_exception_handler,
    not_found_error_handler,
    permission_denied_error_handler,
    unauthorized_error_handler,
    validation_error_handler,
)
from .config import settings
from .database import close_db, init_db
from .clients.router import router as clients_router
from .milestones.router import router as milestones_router
from .organizations.router import router as organizations_router
from .projects.router import router as projects_router
from .tasks.router import router as tasks_router
from .users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    if settings.debug:
        # Only init DB in development mode
        # In production, use Alembic migrations
        await init_db()

    yield

    # Shutdown
    await close_db()


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Core service for ProjectForge project management platform",
    docs_url=f"{settings.api_prefix}/docs" if settings.debug else None,
    redoc_url=f"{settings.api_prefix}/redoc" if settings.debug else None,
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Exception handlers
app.add_exception_handler(NotFoundError, not_found_error_handler)  # type: ignore
app.add_exception_handler(ValidationError, validation_error_handler)  # type: ignore
app.add_exception_handler(PermissionDeniedError, permission_denied_error_handler)  # type: ignore
app.add_exception_handler(UnauthorizedError, unauthorized_error_handler)  # type: ignore
app.add_exception_handler(ConflictError, conflict_error_handler)  # type: ignore
app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "core-service",
        "version": settings.app_version,
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """
    Root endpoint.

    Returns:
        dict: Service information
    """
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }


# Include routers with API prefix
app.include_router(organizations_router, prefix=settings.api_prefix)
app.include_router(clients_router, prefix=settings.api_prefix)
app.include_router(users_router, prefix=settings.api_prefix)
app.include_router(projects_router, prefix=settings.api_prefix)
app.include_router(milestones_router, prefix=settings.api_prefix)
app.include_router(tasks_router, prefix=settings.api_prefix)


# Request logging middleware (optional, for debugging)
if settings.debug:

    @app.middleware("http")
    async def log_requests(request: Request, call_next):  # type: ignore
        """Log all HTTP requests in debug mode."""
        print(f"{request.method} {request.url.path}")
        response = await call_next(request)
        print(f"  -> {response.status_code}")
        return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
