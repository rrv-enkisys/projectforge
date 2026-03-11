"""Unit tests for the SOW Parser agent."""
from __future__ import annotations

import json
from io import BytesIO
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.agents.sow_parser.extractor import ExtractedDocument, SOWExtractor
from src.agents.sow_parser.analyzer import SOWAnalyzer
from src.agents.sow_parser.schemas import SOWParseResponse


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SAMPLE_SOW_TEXT = """
Statement of Work — ProjectForge Website Redesign

Scope of Work
This project covers the complete redesign of the company website including UX research,
visual design, front-end development, and QA testing.

Deliverables
- Wireframes and prototypes
- Final design assets
- Responsive front-end codebase
- QA test report

Timeline
Phase 1: Discovery & UX Research — 2 weeks
Phase 2: Design — 3 weeks
Phase 3: Development — 6 weeks
Phase 4: QA & Launch — 1 week
Total estimated duration: 12 weeks

Budget
Total project cost: $45,000 USD
Payment schedule: 50% upfront, 50% on delivery

Terms and Conditions
All intellectual property created under this agreement is owned by the client.
Confidentiality is required for 24 months post-project.
"""

SAMPLE_LLM_JSON = {
    "project": {
        "name": "ProjectForge Website Redesign",
        "description": "Complete redesign of the company website including UX, design, development, and QA.",
        "estimated_duration_days": 84,
        "estimated_budget": 45000.0,
        "currency": "USD",
    },
    "milestones": [
        {"title": "Discovery & UX Research", "description": "User research and wireframes", "target_date_offset_days": 14},
        {"title": "Design", "description": "Visual design and prototypes", "target_date_offset_days": 35},
        {"title": "Development", "description": "Front-end implementation", "target_date_offset_days": 77},
        {"title": "QA & Launch", "description": "Testing and go-live", "target_date_offset_days": 84},
    ],
    "tasks": [
        {"title": "UX research interviews", "description": "Conduct 10 user interviews", "estimated_hours": 20, "priority": "high", "milestone_index": 0},
        {"title": "Wireframes", "description": "Create wireframes for all pages", "estimated_hours": 30, "priority": "high", "milestone_index": 0},
        {"title": "Visual design system", "description": "Build design system in Figma", "estimated_hours": 40, "priority": "high", "milestone_index": 1},
        {"title": "Front-end development", "description": "Implement React components", "estimated_hours": 160, "priority": "high", "milestone_index": 2},
        {"title": "QA testing", "description": "Execute test cases across browsers", "estimated_hours": 24, "priority": "medium", "milestone_index": 3},
    ],
    "sections": {
        "scope": "Complete redesign of the company website.",
        "deliverables": "Wireframes, design assets, codebase, QA report.",
        "timeline": "12 weeks total across 4 phases.",
        "budget": "$45,000 USD. 50% upfront, 50% on delivery.",
        "terms": "IP owned by client. Confidentiality for 24 months.",
    },
    "confidence": 0.92,
    "warnings": [],
}


@pytest.fixture
def extractor() -> SOWExtractor:
    return SOWExtractor()


@pytest.fixture
def mock_vertex_client() -> MagicMock:
    client = MagicMock()
    client.generate_text = AsyncMock(return_value=json.dumps(SAMPLE_LLM_JSON))
    return client


@pytest.fixture
def analyzer(mock_vertex_client: MagicMock) -> SOWAnalyzer:
    return SOWAnalyzer(vertex_client=mock_vertex_client)


# ---------------------------------------------------------------------------
# SOWExtractor tests
# ---------------------------------------------------------------------------

class TestSOWExtractor:
    @pytest.mark.asyncio
    async def test_extract_plain_text(self, extractor: SOWExtractor) -> None:
        doc = await extractor.extract(SAMPLE_SOW_TEXT.encode(), "text/plain")
        assert SAMPLE_SOW_TEXT.strip() in doc.full_text

    @pytest.mark.asyncio
    async def test_extract_markdown(self, extractor: SOWExtractor) -> None:
        md = "# Project\n## Scope\nDo the work.\n"
        doc = await extractor.extract(md.encode(), "text/markdown")
        assert "Project" in doc.full_text

    @pytest.mark.asyncio
    async def test_detects_scope_section(self, extractor: SOWExtractor) -> None:
        doc = await extractor.extract(SAMPLE_SOW_TEXT.encode(), "text/plain")
        assert "scope" in doc.sections
        assert len(doc.sections["scope"]) > 0

    @pytest.mark.asyncio
    async def test_detects_deliverables_section(self, extractor: SOWExtractor) -> None:
        doc = await extractor.extract(SAMPLE_SOW_TEXT.encode(), "text/plain")
        assert "deliverables" in doc.sections

    @pytest.mark.asyncio
    async def test_detects_timeline_section(self, extractor: SOWExtractor) -> None:
        doc = await extractor.extract(SAMPLE_SOW_TEXT.encode(), "text/plain")
        assert "timeline" in doc.sections

    @pytest.mark.asyncio
    async def test_detects_budget_section(self, extractor: SOWExtractor) -> None:
        doc = await extractor.extract(SAMPLE_SOW_TEXT.encode(), "text/plain")
        assert "budget" in doc.sections

    @pytest.mark.asyncio
    async def test_detects_terms_section(self, extractor: SOWExtractor) -> None:
        doc = await extractor.extract(SAMPLE_SOW_TEXT.encode(), "text/plain")
        assert "terms" in doc.sections

    @pytest.mark.asyncio
    async def test_empty_content_returns_empty_document(self, extractor: SOWExtractor) -> None:
        doc = await extractor.extract(b"", "text/plain")
        assert doc.full_text == ""
        assert doc.sections == {}

    def test_section_detection_no_headings(self, extractor: SOWExtractor) -> None:
        sections = extractor._detect_sections("Just some text without headings.")
        assert sections == {}

    def test_section_detection_multiple_sections(self, extractor: SOWExtractor) -> None:
        text = "Scope\nDo A.\nDeliverables\nDeliver B.\n"
        sections = extractor._detect_sections(text)
        assert "scope" in sections
        assert "deliverables" in sections


# ---------------------------------------------------------------------------
# SOWAnalyzer tests
# ---------------------------------------------------------------------------

class TestSOWAnalyzer:
    @pytest.mark.asyncio
    async def test_analyze_returns_sow_parse_response(self, analyzer: SOWAnalyzer) -> None:
        doc = ExtractedDocument(full_text=SAMPLE_SOW_TEXT, sections={"scope": "Full scope text."})
        result = await analyzer.analyze(doc)
        assert isinstance(result, SOWParseResponse)

    @pytest.mark.asyncio
    async def test_project_name_extracted(self, analyzer: SOWAnalyzer) -> None:
        doc = ExtractedDocument(full_text=SAMPLE_SOW_TEXT, sections={})
        result = await analyzer.analyze(doc)
        assert result.project.name == "ProjectForge Website Redesign"

    @pytest.mark.asyncio
    async def test_milestones_extracted(self, analyzer: SOWAnalyzer) -> None:
        doc = ExtractedDocument(full_text=SAMPLE_SOW_TEXT, sections={})
        result = await analyzer.analyze(doc)
        assert len(result.milestones) == 4
        assert result.milestones[0].title == "Discovery & UX Research"

    @pytest.mark.asyncio
    async def test_tasks_extracted(self, analyzer: SOWAnalyzer) -> None:
        doc = ExtractedDocument(full_text=SAMPLE_SOW_TEXT, sections={})
        result = await analyzer.analyze(doc)
        assert len(result.tasks) == 5

    @pytest.mark.asyncio
    async def test_confidence_set(self, analyzer: SOWAnalyzer) -> None:
        doc = ExtractedDocument(full_text=SAMPLE_SOW_TEXT, sections={})
        result = await analyzer.analyze(doc)
        assert result.confidence == pytest.approx(0.92)

    @pytest.mark.asyncio
    async def test_sections_included(self, analyzer: SOWAnalyzer) -> None:
        doc = ExtractedDocument(full_text=SAMPLE_SOW_TEXT, sections={})
        result = await analyzer.analyze(doc)
        section_names = {s.name for s in result.raw_sections}
        assert "scope" in section_names
        assert "deliverables" in section_names

    @pytest.mark.asyncio
    async def test_extractor_sections_merged_when_missing_from_llm(
        self, analyzer: SOWAnalyzer
    ) -> None:
        # Extractor found a section the LLM didn't report
        doc = ExtractedDocument(
            full_text=SAMPLE_SOW_TEXT,
            sections={"scope": "Scope from extractor", "extra_section": "Extra content"},
        )
        result = await analyzer.analyze(doc)
        section_names = {s.name for s in result.raw_sections}
        assert "extra_section" in section_names

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_json(self, mock_vertex_client: MagicMock) -> None:
        mock_vertex_client.generate_text = AsyncMock(return_value="not valid json{{")
        analyzer = SOWAnalyzer(vertex_client=mock_vertex_client)
        doc = ExtractedDocument(full_text="Some SOW text", sections={"scope": "Scope text"})
        result = await analyzer.analyze(doc)
        assert result.confidence == 0.0
        assert len(result.warnings) > 0
        assert result.project.name == "Project (review required)"

    @pytest.mark.asyncio
    async def test_fallback_on_vertex_error(self, mock_vertex_client: MagicMock) -> None:
        mock_vertex_client.generate_text = AsyncMock(side_effect=RuntimeError("API unavailable"))
        analyzer = SOWAnalyzer(vertex_client=mock_vertex_client)
        doc = ExtractedDocument(full_text="SOW content", sections={})
        result = await analyzer.analyze(doc)
        assert result.confidence == 0.0
        assert any("unavailable" in w.lower() for w in result.warnings)

    @pytest.mark.asyncio
    async def test_run_delegates_to_analyze(self, analyzer: SOWAnalyzer) -> None:
        doc = ExtractedDocument(full_text=SAMPLE_SOW_TEXT, sections={})
        result = await analyzer.run(doc=doc)
        assert isinstance(result, SOWParseResponse)

    @pytest.mark.asyncio
    async def test_task_priority_values_are_valid(self, analyzer: SOWAnalyzer) -> None:
        doc = ExtractedDocument(full_text=SAMPLE_SOW_TEXT, sections={})
        result = await analyzer.analyze(doc)
        valid_priorities = {"low", "medium", "high", "urgent"}
        for task in result.tasks:
            assert task.priority in valid_priorities

    @pytest.mark.asyncio
    async def test_milestone_index_within_bounds(self, analyzer: SOWAnalyzer) -> None:
        doc = ExtractedDocument(full_text=SAMPLE_SOW_TEXT, sections={})
        result = await analyzer.analyze(doc)
        n_milestones = len(result.milestones)
        for task in result.tasks:
            if task.milestone_index is not None:
                assert 0 <= task.milestone_index < n_milestones


# ---------------------------------------------------------------------------
# Router integration tests
# ---------------------------------------------------------------------------

class TestSOWParserRouter:
    @pytest.fixture
    def client(self, mock_vertex_client: MagicMock):
        from fastapi.testclient import TestClient
        from unittest.mock import patch
        from src.main import app
        from src.agents.sow_parser.extractor import get_sow_extractor
        from src.agents.sow_parser.analyzer import get_sow_analyzer

        test_extractor = SOWExtractor()
        test_analyzer = SOWAnalyzer(vertex_client=mock_vertex_client)

        app.dependency_overrides[get_sow_extractor] = lambda: test_extractor
        app.dependency_overrides[get_sow_analyzer] = lambda: test_analyzer

        with TestClient(app) as c:
            yield c

        app.dependency_overrides.clear()

    def test_parse_text_file_returns_200(self, client) -> None:
        response = client.post(
            "/api/v1/agents/sow/parse",
            headers={"X-Organization-ID": str(uuid4())},
            files={"file": ("sow.txt", SAMPLE_SOW_TEXT.encode(), "text/plain")},
        )
        assert response.status_code == 200

    def test_parse_response_has_project(self, client) -> None:
        response = client.post(
            "/api/v1/agents/sow/parse",
            headers={"X-Organization-ID": str(uuid4())},
            files={"file": ("sow.txt", SAMPLE_SOW_TEXT.encode(), "text/plain")},
        )
        data = response.json()
        assert "project" in data
        assert "name" in data["project"]

    def test_parse_response_has_milestones_and_tasks(self, client) -> None:
        response = client.post(
            "/api/v1/agents/sow/parse",
            headers={"X-Organization-ID": str(uuid4())},
            files={"file": ("sow.txt", SAMPLE_SOW_TEXT.encode(), "text/plain")},
        )
        data = response.json()
        assert "milestones" in data
        assert "tasks" in data
        assert isinstance(data["milestones"], list)
        assert isinstance(data["tasks"], list)

    def test_empty_file_returns_400(self, client) -> None:
        response = client.post(
            "/api/v1/agents/sow/parse",
            headers={"X-Organization-ID": str(uuid4())},
            files={"file": ("empty.txt", b"", "text/plain")},
        )
        assert response.status_code == 400

    def test_unsupported_type_returns_415(self, client) -> None:
        response = client.post(
            "/api/v1/agents/sow/parse",
            headers={"X-Organization-ID": str(uuid4())},
            files={"file": ("image.png", b"\x89PNG\r\n", "image/png")},
        )
        assert response.status_code == 415

    def test_missing_org_header_returns_422(self, client) -> None:
        response = client.post(
            "/api/v1/agents/sow/parse",
            files={"file": ("sow.txt", SAMPLE_SOW_TEXT.encode(), "text/plain")},
        )
        assert response.status_code == 422

    def test_markdown_file_accepted(self, client) -> None:
        md_content = b"# SOW\n## Scope\nDo work.\n## Timeline\n4 weeks\n"
        response = client.post(
            "/api/v1/agents/sow/parse",
            headers={"X-Organization-ID": str(uuid4())},
            files={"file": ("sow.md", md_content, "text/markdown")},
        )
        assert response.status_code == 200
