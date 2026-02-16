"""Database connection and session management"""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from .config import settings

# SQLAlchemy base for models
Base = declarative_base()

# Global engine instance
engine: AsyncEngine | None = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create database engine"""
    global engine
    if engine is None:
        engine = create_async_engine(
            settings.database_url,
            echo=settings.environment == "development",
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=10,
        )
    return engine


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create session maker"""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return SessionLocal


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session"""
    async_session = get_session_maker()
    async with async_session() as session:
        yield session


@asynccontextmanager
async def get_db_context(organization_id: str | None = None) -> AsyncGenerator[AsyncSession, None]:
    """Context manager for database session with optional RLS context"""
    async_session = get_session_maker()
    async with async_session() as session:
        # Set organization context for Row Level Security if provided
        if organization_id:
            await session.execute(
                f"SET LOCAL app.current_organization_id = '{organization_id}'"
            )
        yield session


async def init_db() -> None:
    """Initialize database connection"""
    get_engine()
    get_session_maker()


async def close_db() -> None:
    """Close database connections"""
    global engine
    if engine:
        await engine.dispose()
        engine = None
