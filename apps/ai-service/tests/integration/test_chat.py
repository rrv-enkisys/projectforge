"""Integration tests for the Chat service."""
from __future__ import annotations

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.chat.models import ChatMessage
from src.chat.service import ChatService
from tests.conftest import TEST_ORG_ID, TEST_PROJECT_ID, TEST_USER_ID


def make_chat_service(mock_db: MagicMock, mock_vertex_client: MagicMock) -> ChatService:
    """Create a ChatService instance with mocked dependencies."""
    service = ChatService.__new__(ChatService)
    service.db = mock_db
    service.vertex_client = mock_vertex_client
    service.embedding_service = MagicMock()
    service.embedding_service.embed_query = AsyncMock(return_value=[0.1] * 768)
    return service


@pytest.fixture
def mock_db() -> MagicMock:
    """Mock database session."""
    mock = MagicMock(spec=AsyncSession)
    mock.add = MagicMock()
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.delete = AsyncMock()
    mock.execute = AsyncMock()
    return mock


@pytest.fixture
def sample_session() -> MagicMock:
    """A sample chat session mock."""
    session = MagicMock()
    session.id = uuid4()
    session.project_id = TEST_PROJECT_ID
    session.organization_id = TEST_ORG_ID
    session.user_id = TEST_USER_ID
    session.title = None
    session.created_at = datetime.utcnow()
    session.updated_at = datetime.utcnow()
    session.messages = []
    return session


@pytest.fixture
def sample_messages() -> list[ChatMessage]:
    """Sample chat messages for history."""
    session_id = uuid4()
    messages = []
    for i, (role, content) in enumerate([
        ("user", "What is the status of the project?"),
        ("assistant", "The project is currently in progress with 5 active tasks."),
        ("user", "Which tasks are overdue?"),
    ]):
        msg = ChatMessage.__new__(ChatMessage)
        msg.id = uuid4()
        msg.session_id = session_id
        msg.role = role
        msg.content = content
        msg.created_at = datetime.utcnow()
        messages.append(msg)
    return messages


class TestChatServiceGetRagContext:
    @pytest.mark.asyncio
    async def test_rag_context_returns_empty_on_no_docs(
        self,
        mock_db: MagicMock,
        mock_vertex_client: MagicMock,
    ) -> None:
        service = make_chat_service(mock_db, mock_vertex_client)

        # Mock doc repo to return no results
        with patch("src.chat.service.DocumentRepository") as MockDocRepo:
            mock_repo_instance = MagicMock()
            mock_repo_instance.vector_search = AsyncMock(return_value=[])
            MockDocRepo.return_value = mock_repo_instance

            context = await service.get_rag_context(
                "What is the budget?", TEST_PROJECT_ID, TEST_ORG_ID
            )

        assert context == ""

    @pytest.mark.asyncio
    async def test_rag_context_returns_empty_on_low_relevance(
        self,
        mock_db: MagicMock,
        mock_vertex_client: MagicMock,
    ) -> None:
        service = make_chat_service(mock_db, mock_vertex_client)

        # Mock doc repo to return low-relevance results
        mock_chunk = MagicMock()
        mock_chunk.content = "Some document content"
        low_relevance_score = 0.3  # Below threshold of 0.5

        with patch("src.chat.service.DocumentRepository") as MockDocRepo:
            mock_repo_instance = MagicMock()
            mock_repo_instance.vector_search = AsyncMock(
                return_value=[(mock_chunk, low_relevance_score)]
            )
            MockDocRepo.return_value = mock_repo_instance

            context = await service.get_rag_context(
                "question", TEST_PROJECT_ID, TEST_ORG_ID
            )

        assert context == ""

    @pytest.mark.asyncio
    async def test_rag_context_returns_content_on_high_relevance(
        self,
        mock_db: MagicMock,
        mock_vertex_client: MagicMock,
    ) -> None:
        service = make_chat_service(mock_db, mock_vertex_client)

        mock_chunk = MagicMock()
        mock_chunk.content = "The project budget is $50,000"
        high_relevance_score = 0.85

        with patch("src.chat.service.DocumentRepository") as MockDocRepo:
            mock_repo_instance = MagicMock()
            mock_repo_instance.vector_search = AsyncMock(
                return_value=[(mock_chunk, high_relevance_score)]
            )
            MockDocRepo.return_value = mock_repo_instance

            context = await service.get_rag_context(
                "What is the budget?", TEST_PROJECT_ID, TEST_ORG_ID
            )

        assert "budget" in context.lower() or "$50,000" in context

    @pytest.mark.asyncio
    async def test_rag_context_failure_returns_empty(
        self,
        mock_db: MagicMock,
        mock_vertex_client: MagicMock,
    ) -> None:
        """RAG failure should not crash chat - returns empty context."""
        service = make_chat_service(mock_db, mock_vertex_client)
        service.embedding_service.embed_query = AsyncMock(side_effect=Exception("Vertex AI unavailable"))

        context = await service.get_rag_context(
            "question", TEST_PROJECT_ID, TEST_ORG_ID
        )
        assert context == ""


class TestChatServiceGenerateResponse:
    @pytest.mark.asyncio
    async def test_generate_response_calls_vertex(
        self,
        mock_db: MagicMock,
        mock_vertex_client: MagicMock,
    ) -> None:
        service = make_chat_service(mock_db, mock_vertex_client)

        # Mock get_conversation_history to return empty
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        with patch.object(service, "get_rag_context", AsyncMock(return_value="")):
            with patch.object(service, "add_message", AsyncMock()) as mock_add:
                with patch.object(service, "_auto_title_session", AsyncMock()):
                    response = await service.generate_response(
                        session_id=uuid4(),
                        user_message="Hello, what can you do?",
                    )

        mock_vertex_client.generate_text.assert_called_once()
        assert response == "Mocked AI response for testing."

    @pytest.mark.asyncio
    async def test_generate_response_saves_messages(
        self,
        mock_db: MagicMock,
        mock_vertex_client: MagicMock,
    ) -> None:
        service = make_chat_service(mock_db, mock_vertex_client)
        session_id = uuid4()

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        saved_messages: list[tuple[str, str, str]] = []

        async def mock_add_message(s_id: UUID, role: str, content: str) -> MagicMock:
            saved_messages.append((str(s_id), role, content))
            return MagicMock()

        with patch.object(service, "get_rag_context", AsyncMock(return_value="")):
            with patch.object(service, "add_message", side_effect=mock_add_message):
                with patch.object(service, "_auto_title_session", AsyncMock()):
                    await service.generate_response(
                        session_id=session_id,
                        user_message="Test message",
                    )

        # Should have saved user message and assistant response
        assert len(saved_messages) == 2
        roles = [msg[1] for msg in saved_messages]
        assert "user" in roles
        assert "assistant" in roles

    @pytest.mark.asyncio
    async def test_generate_response_includes_rag_context_in_prompt(
        self,
        mock_db: MagicMock,
        mock_vertex_client: MagicMock,
    ) -> None:
        service = make_chat_service(mock_db, mock_vertex_client)

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        rag_context = "Project budget is $100,000"

        with patch.object(service, "get_rag_context", AsyncMock(return_value=rag_context)):
            with patch.object(service, "add_message", AsyncMock()):
                with patch.object(service, "_auto_title_session", AsyncMock()):
                    await service.generate_response(
                        session_id=uuid4(),
                        user_message="What is the budget?",
                        project_id=TEST_PROJECT_ID,
                        organization_id=TEST_ORG_ID,
                    )

        # Prompt should contain the RAG context
        call_args = mock_vertex_client.generate_text.call_args
        prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
        assert rag_context in prompt


class TestChatServiceAutoTitle:
    @pytest.mark.asyncio
    async def test_auto_title_sets_short_title(
        self,
        mock_db: MagicMock,
        mock_vertex_client: MagicMock,
        sample_session: MagicMock,
    ) -> None:
        service = make_chat_service(mock_db, mock_vertex_client)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_session
        mock_db.execute = AsyncMock(return_value=mock_result)

        short_message = "What are the project risks?"
        await service._auto_title_session(sample_session.id, short_message)

        assert sample_session.title == short_message

    @pytest.mark.asyncio
    async def test_auto_title_truncates_long_message(
        self,
        mock_db: MagicMock,
        mock_vertex_client: MagicMock,
        sample_session: MagicMock,
    ) -> None:
        service = make_chat_service(mock_db, mock_vertex_client)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_session
        mock_db.execute = AsyncMock(return_value=mock_result)

        long_message = "A" * 100
        await service._auto_title_session(sample_session.id, long_message)

        assert sample_session.title is not None
        assert len(sample_session.title) <= 63  # 60 chars + "..."

    @pytest.mark.asyncio
    async def test_auto_title_does_not_overwrite_existing(
        self,
        mock_db: MagicMock,
        mock_vertex_client: MagicMock,
        sample_session: MagicMock,
    ) -> None:
        service = make_chat_service(mock_db, mock_vertex_client)
        sample_session.title = "Existing title"

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_session
        mock_db.execute = AsyncMock(return_value=mock_result)

        await service._auto_title_session(sample_session.id, "New message that should not become title")

        assert sample_session.title == "Existing title"
