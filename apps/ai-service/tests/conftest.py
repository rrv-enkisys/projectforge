"""Pytest configuration and shared fixtures for AI Service tests."""
from __future__ import annotations

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.main import app
from src.database import Base, get_db

# Fixed test IDs for consistency
TEST_ORG_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_ID = "test-user-firebase-uid"
TEST_PROJECT_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_SESSION_ID = UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_vertex_client() -> MagicMock:
    """Mock VertexAI client to avoid real API calls."""
    mock = MagicMock()
    mock.generate_text = AsyncMock(return_value="Mocked AI response for testing.")
    mock.generate_embeddings = AsyncMock(return_value=[[0.1] * 768])
    mock.generate_text_stream = AsyncMock(return_value=iter(["Mocked ", "stream ", "response."]))
    return mock


@pytest.fixture
def mock_embedding_service(mock_vertex_client: MagicMock) -> MagicMock:
    """Mock embedding service."""
    mock = MagicMock()
    mock.embed_query = AsyncMock(return_value=[0.1] * 768)
    mock.embed_texts = AsyncMock(return_value=[[0.1] * 768])
    return mock


@pytest.fixture
def test_org_id() -> UUID:
    return TEST_ORG_ID


@pytest.fixture
def test_user_id() -> str:
    return TEST_USER_ID


@pytest.fixture
def test_project_id() -> UUID:
    return TEST_PROJECT_ID


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """HTTP headers that simulate authenticated requests."""
    return {
        "X-Organization-ID": str(TEST_ORG_ID),
        "X-User-ID": TEST_USER_ID,
    }


@pytest.fixture
def sample_project_data() -> dict:
    """Sample project data for copilot testing."""
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    return {
        "id": str(TEST_PROJECT_ID),
        "name": "Test Project Alpha",
        "description": "A test project for copilot analysis",
        "status": "active",
        "start_date": (now - timedelta(days=30)).isoformat(),
        "end_date": (now + timedelta(days=60)).isoformat(),
        "budget": 50000.0,
        "organization_id": str(TEST_ORG_ID),
        "tasks": [
            {
                "id": str(uuid4()),
                "title": "Design system architecture",
                "status": "done",
                "priority": "high",
                "due_date": (now - timedelta(days=5)).isoformat(),
                "updated_at": (now - timedelta(days=5)).isoformat(),
                "assignee_id": str(uuid4()),
            },
            {
                "id": str(uuid4()),
                "title": "Implement API endpoints",
                "status": "in_progress",
                "priority": "high",
                "due_date": (now + timedelta(days=7)).isoformat(),
                "updated_at": (now - timedelta(days=1)).isoformat(),
                "assignee_id": str(uuid4()),
            },
            {
                "id": str(uuid4()),
                "title": "Write unit tests",
                "status": "todo",
                "priority": "medium",
                "due_date": (now - timedelta(days=2)).isoformat(),  # overdue
                "updated_at": (now - timedelta(days=10)).isoformat(),
                "assignee_id": None,
            },
            {
                "id": str(uuid4()),
                "title": "Deploy to staging",
                "status": "todo",
                "priority": "low",
                "due_date": (now + timedelta(days=14)).isoformat(),
                "updated_at": (now - timedelta(days=3)).isoformat(),
                "assignee_id": None,
            },
        ],
        "milestones": [
            {
                "id": str(uuid4()),
                "title": "MVP Release",
                "status": "pending",
                "target_date": (now + timedelta(days=30)).isoformat(),
                "is_completed": False,
            },
            {
                "id": str(uuid4()),
                "title": "Beta Launch",
                "status": "completed",
                "target_date": (now - timedelta(days=10)).isoformat(),
                "is_completed": True,
            },
        ],
    }
