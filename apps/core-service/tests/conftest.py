"""Pytest configuration and shared fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base, get_db
from src.main import app

# Test database URL (use a separate test database)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/projectforge_test"

# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

# Create test session factory
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database() -> AsyncGenerator[None, None]:
    """Create test database tables before tests and drop after."""
    # Create all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Drop all tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a database session for a test."""
    async with TestSessionLocal() as session:
        # Start a nested transaction
        await session.begin()

        yield session

        # Rollback the transaction
        await session.rollback()


@pytest.fixture
def test_org_id() -> UUID:
    """Fixed organization ID for tests."""
    return UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def test_user_id() -> str:
    """Fixed user ID for tests."""
    return "test-user-uid-123"


@pytest.fixture
async def db_with_org_context(
    db_session: AsyncSession, test_org_id: UUID
) -> AsyncGenerator[AsyncSession, None]:
    """Database session with organization context set."""
    # Set organization context for RLS
    await db_session.execute(text(f"SET LOCAL app.current_organization_id = '{test_org_id}'"))
    yield db_session


@pytest.fixture
def override_get_db(db_session: AsyncSession) -> Any:
    """Override the get_db dependency."""

    async def _override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    return _override_get_db


@pytest.fixture
def client(override_get_db: Any) -> TestClient:
    """Create a test client with database override."""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(test_org_id: UUID, test_user_id: str) -> dict[str, str]:
    """Headers with authentication and organization context."""
    return {
        "X-Organization-ID": str(test_org_id),
        "X-User-ID": test_user_id,
        "X-User-Email": "test@example.com",
        "X-User-Role": "admin",
    }
