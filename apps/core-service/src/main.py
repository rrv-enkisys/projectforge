"""
ProjectForge Core Service - Main FastAPI Application

This is the main entry point for the Core Service, which handles:
- Organizations, clients, users
- Projects, tasks, milestones
- Multi-tenant data isolation with RLS
"""
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .common.exceptions import (
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    UnauthorizedError,
    ValidationError,
    business_rule_error_handler,
    conflict_error_handler,
    generic_exception_handler,
    not_found_error_handler,
    permission_denied_error_handler,
    unauthorized_error_handler,
    validation_error_handler,
)
from .common.health import HealthCheck
from .common.logging import logging_middleware, setup_logging
from .config import settings
from .database import close_db, init_db
from .clients.router import router as clients_router
from .dashboard.router import router as dashboard_router
from .milestones.router import router as milestones_router
from .organizations.router import router as organizations_router
from .projects.router import router as projects_router
from .tasks.router import router as tasks_router
from .tasks.dependencies_router import router as task_dependencies_router
from .tasks.assignments_router import router as task_assignments_router
from .tasks.comments_router import router as task_comments_router
from .users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    # Setup structured logging
    log_level = "DEBUG" if settings.debug else "INFO"
    setup_logging(log_level)

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

# CORS middleware - DISABLED
# CORS is handled by the API Gateway, not by individual services
# Uncomment only if running Core Service standalone (without API Gateway)
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=settings.cors_origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
#     expose_headers=["*"],
# )

# Exception handlers
app.add_exception_handler(NotFoundError, not_found_error_handler)  # type: ignore
app.add_exception_handler(ValidationError, validation_error_handler)  # type: ignore
app.add_exception_handler(BusinessRuleError, business_rule_error_handler)  # type: ignore
app.add_exception_handler(PermissionDeniedError, permission_denied_error_handler)  # type: ignore
app.add_exception_handler(UnauthorizedError, unauthorized_error_handler)  # type: ignore
app.add_exception_handler(ConflictError, conflict_error_handler)  # type: ignore
app.add_exception_handler(Exception, generic_exception_handler)  # type: ignore


# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check() -> dict[str, Any]:
    """
    Basic health check endpoint.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "core-service",
        "version": settings.app_version,
        "uptime_seconds": HealthCheck.get_uptime_seconds(),
    }


@app.get("/health/detailed", tags=["health"])
async def health_check_detailed() -> dict[str, Any]:
    """
    Detailed health check with dependency checks.

    Returns:
        dict: Detailed health status
    """
    health_status = await HealthCheck.get_health_status(detailed=True)
    health_status["service"] = "core-service"
    health_status["version"] = settings.app_version
    return health_status


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
app.include_router(task_dependencies_router, prefix=settings.api_prefix)
app.include_router(task_assignments_router, prefix=settings.api_prefix)
app.include_router(task_comments_router, prefix=settings.api_prefix)
app.include_router(dashboard_router, prefix=settings.api_prefix)


# Structured logging middleware
@app.middleware("http")
async def structured_logging_middleware(request: Request, call_next):  # type: ignore
    """Add structured logging to all requests."""
    return await logging_middleware(request, call_next)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="debug" if settings.debug else "info",
    )
