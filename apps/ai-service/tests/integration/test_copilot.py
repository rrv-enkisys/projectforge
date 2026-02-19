"""Integration tests for the AI Copilot service."""
from __future__ import annotations

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from src.copilot.analyzer import ProjectAnalyzer
from src.copilot.service import CopilotService
from tests.conftest import TEST_ORG_ID, TEST_PROJECT_ID


@pytest.fixture
def mock_db() -> MagicMock:
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def mock_project_data_repo() -> MagicMock:
    """Mock ProjectDataRepository."""
    mock = MagicMock()
    mock.get_project_data = AsyncMock()
    return mock


@pytest.fixture
def sample_project(sample_project_data: dict) -> dict:
    return sample_project_data


class TestCopilotServiceAnalyzeProject:
    """Tests for CopilotService.analyze_project"""

    @pytest.mark.asyncio
    async def test_analyze_project_returns_all_fields(
        self,
        mock_vertex_client: MagicMock,
        mock_db: MagicMock,
        sample_project: dict,
    ) -> None:
        service = CopilotService.__new__(CopilotService)
        service.db = mock_db
        service.vertex_client = mock_vertex_client
        service.analyzer = ProjectAnalyzer()
        service.project_data_repo = MagicMock()

        result = await service.analyze_project(sample_project)

        assert "health" in result
        assert "risks" in result
        assert "completion_prediction" in result
        assert "ai_insights" in result
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_timestamp_is_iso_format(
        self,
        mock_vertex_client: MagicMock,
        mock_db: MagicMock,
        sample_project: dict,
    ) -> None:
        service = CopilotService.__new__(CopilotService)
        service.db = mock_db
        service.vertex_client = mock_vertex_client
        service.analyzer = ProjectAnalyzer()
        service.project_data_repo = MagicMock()

        result = await service.analyze_project(sample_project)

        # Timestamp should be a valid ISO datetime string, not "utcnow"
        timestamp = result["timestamp"]
        assert timestamp != "utcnow"
        # Should be parseable as a datetime
        parsed = datetime.fromisoformat(timestamp)
        assert isinstance(parsed, datetime)

    @pytest.mark.asyncio
    async def test_health_score_is_numeric(
        self,
        mock_vertex_client: MagicMock,
        mock_db: MagicMock,
        sample_project: dict,
    ) -> None:
        service = CopilotService.__new__(CopilotService)
        service.db = mock_db
        service.vertex_client = mock_vertex_client
        service.analyzer = ProjectAnalyzer()
        service.project_data_repo = MagicMock()

        result = await service.analyze_project(sample_project)

        assert isinstance(result["health"]["score"], int)
        assert 0 <= result["health"]["score"] <= 100

    @pytest.mark.asyncio
    async def test_risks_is_list(
        self,
        mock_vertex_client: MagicMock,
        mock_db: MagicMock,
        sample_project: dict,
    ) -> None:
        service = CopilotService.__new__(CopilotService)
        service.db = mock_db
        service.vertex_client = mock_vertex_client
        service.analyzer = ProjectAnalyzer()
        service.project_data_repo = MagicMock()

        result = await service.analyze_project(sample_project)

        assert isinstance(result["risks"], list)

    @pytest.mark.asyncio
    async def test_ai_insights_called_with_prompt(
        self,
        mock_vertex_client: MagicMock,
        mock_db: MagicMock,
        sample_project: dict,
    ) -> None:
        service = CopilotService.__new__(CopilotService)
        service.db = mock_db
        service.vertex_client = mock_vertex_client
        service.analyzer = ProjectAnalyzer()
        service.project_data_repo = MagicMock()

        result = await service.analyze_project(sample_project)

        # Vertex client should have been called for AI insights
        mock_vertex_client.generate_text.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_by_id_with_no_project_returns_unknown(
        self,
        mock_vertex_client: MagicMock,
        mock_db: MagicMock,
        mock_project_data_repo: MagicMock,
    ) -> None:
        mock_project_data_repo.get_project_data = AsyncMock(return_value={})

        service = CopilotService.__new__(CopilotService)
        service.db = mock_db
        service.vertex_client = mock_vertex_client
        service.analyzer = ProjectAnalyzer()
        service.project_data_repo = mock_project_data_repo

        result = await service.analyze_project_by_id(uuid4(), TEST_ORG_ID)

        assert result["health"]["status"] == "unknown"


class TestCopilotServiceRiskAnalysis:
    @pytest.mark.asyncio
    async def test_risk_analysis_returns_breakdown(
        self,
        mock_vertex_client: MagicMock,
        mock_db: MagicMock,
        sample_project: dict,
    ) -> None:
        service = CopilotService.__new__(CopilotService)
        service.db = mock_db
        service.vertex_client = mock_vertex_client
        service.analyzer = ProjectAnalyzer()
        service.project_data_repo = MagicMock()

        result = await service.get_risk_analysis(sample_project)

        assert "detected_risks" in result
        assert "ai_analysis" in result
        assert "risk_count" in result
        assert "severity_breakdown" in result
        assert isinstance(result["severity_breakdown"], dict)

    @pytest.mark.asyncio
    async def test_severity_breakdown_has_all_levels(
        self,
        mock_vertex_client: MagicMock,
        mock_db: MagicMock,
        sample_project: dict,
    ) -> None:
        service = CopilotService.__new__(CopilotService)
        service.db = mock_db
        service.vertex_client = mock_vertex_client
        service.analyzer = ProjectAnalyzer()
        service.project_data_repo = MagicMock()

        result = await service.get_risk_analysis(sample_project)

        breakdown = result["severity_breakdown"]
        assert "high" in breakdown
        assert "medium" in breakdown
        assert "low" in breakdown


class TestCopilotServiceSuggestions:
    @pytest.mark.asyncio
    async def test_suggestions_returns_list(
        self,
        mock_vertex_client: MagicMock,
        mock_db: MagicMock,
        sample_project: dict,
    ) -> None:
        # Mock vertex to return structured suggestions
        mock_vertex_client.generate_text = AsyncMock(
            return_value="Category: Timeline, Action: Reduce scope, Impact: Faster delivery"
        )

        service = CopilotService.__new__(CopilotService)
        service.db = mock_db
        service.vertex_client = mock_vertex_client
        service.analyzer = ProjectAnalyzer()
        service.project_data_repo = MagicMock()

        result = await service.get_suggestions(sample_project)

        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_suggestions_have_required_fields(
        self,
        mock_vertex_client: MagicMock,
        mock_db: MagicMock,
        sample_project: dict,
    ) -> None:
        mock_vertex_client.generate_text = AsyncMock(
            return_value="Category1: Action text here\nCategory2: Another action here"
        )

        service = CopilotService.__new__(CopilotService)
        service.db = mock_db
        service.vertex_client = mock_vertex_client
        service.analyzer = ProjectAnalyzer()
        service.project_data_repo = MagicMock()

        result = await service.get_suggestions(sample_project)

        for suggestion in result:
            assert "category" in suggestion
            assert "action" in suggestion
            assert "priority" in suggestion
