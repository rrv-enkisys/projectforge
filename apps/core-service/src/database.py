"""
Database connection and session management.
Provides async SQLAlchemy engine and session factory.
"""
import logging
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
from uuid import UUID

from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from .config import settings

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


# Create async engine with optimized pool settings
engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.debug,  # Log SQL in debug mode
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Base connection pool size
    max_overflow=20,  # Additional connections allowed during peak
    pool_recycle=3600,  # Recycle connections after 1 hour
    pool_timeout=30,  # Wait up to 30s for a connection
    connect_args={
        "server_settings": {
            "application_name": "projectforge-core-service",
        },
    },
)


# Query performance monitoring
@event.listens_for(Engine, "before_cursor_execute", named=True)
def receive_before_cursor_execute(**kw: Any) -> None:
    """Store query start time for performance monitoring."""
    kw["conn"].info.setdefault("query_start_time", []).append(time.time())


@event.listens_for(Engine, "after_cursor_execute", named=True)
def receive_after_cursor_execute(**kw: Any) -> None:
    """Log slow queries for performance monitoring."""
    query_start_times = kw["conn"].info.get("query_start_time", [])
    if query_start_times:
        total_time = time.time() - query_start_times.pop(-1)

        # Log slow queries (> 1 second)
        if total_time > 1.0:
            logger.warning(
                f"Slow query detected ({total_time:.2f}s)",
                extra={
                    "duration_seconds": total_time,
                    "statement": kw["statement"],
                    "parameters": kw["parameters"],
                },
            )

        # Log very slow queries as error (> 5 seconds)
        if total_time > 5.0:
            logger.error(
                f"Very slow query detected ({total_time:.2f}s)",
                extra={
                    "duration_seconds": total_time,
                    "statement": kw["statement"],
                    "parameters": kw["parameters"],
                },
            )

# Create session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.

    Usage:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager for database session.

    Usage:
        async with get_db_context() as db:
            result = await db.execute(...)
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def set_organization_context(
    session: AsyncSession,
    organization_id: UUID,
) -> None:
    """
    Set the organization_id session variable for Row Level Security.

    This must be called before any queries on multi-tenant tables.
    RLS policies use: current_setting('app.current_organization_id')::uuid

    Args:
        session: The async database session
        organization_id: UUID of the organization to set as context

    Example:
        async with get_db_context() as db:
            await set_organization_context(db, org_id)
            projects = await db.execute(select(Project))
    """
    # Use string formatting for SET LOCAL since it doesn't accept bind parameters
    await session.execute(
        text(f"SET LOCAL app.current_organization_id = '{organization_id}'"),
    )


async def init_db() -> None:
    """
    Initialize database tables.

    Note: In production, use Alembic migrations instead.
    This is mainly for development/testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
