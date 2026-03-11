"""Unit + integration tests for the Meeting Notes agent."""
from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.agents.meeting_notes.extractor import MeetingExtractor, PreExtractedData
from src.agents.meeting_notes.analyzer import MeetingAnalyzer
from src.agents.meeting_notes.schemas import MeetingNotesParseResponse


# ---------------------------------------------------------------------------
# Shared fixtures & sample data
# ---------------------------------------------------------------------------

SAMPLE_TRANSCRIPT = """
Meeting: Sprint Planning — March 11, 2026
Participants: Alice, Bob, Carol, Dave

Alice: Let's go through last week's action items.
Bob: I finished the API endpoints but still need to write the tests.
Carol: Agreed, the design tokens must be finalized by end of week.
Alice: Bob, can you finish the unit tests by Thursday?
Bob: Yes, I will have the unit tests done by Thursday.
Alice: Great. Carol will update the design system by Friday.
Carol: Got it. Also, we decided to drop the mobile-first approach for now.
Dave: TODO: Write E2E test suite for the checkout flow
Alice: Action Item: Update stakeholder presentation by next Monday
Bob: We approved the new architecture design.
Dave: I'll set up the test environment by end of day.
"""

SAMPLE_LLM_JSON = {
    "summary": (
        "Sprint planning covering last week's action items, design tokens, testing tasks, "
        "and architecture decisions. Key actions assigned to Bob, Carol, Dave, and Alice."
    ),
    "participants": ["Alice", "Bob", "Carol", "Dave"],
    "meeting_date_hint": "March 11, 2026",
    "action_items": [
        {
            "description": "Finish unit tests for API endpoints",
            "assignee_hint": "Bob",
            "due_date_hint": "by Thursday",
            "priority": "high",
            "context": "Bob, can you finish the unit tests by Thursday?",
        },
        {
            "description": "Update design system with new tokens",
            "assignee_hint": "Carol",
            "due_date_hint": "by Friday",
            "priority": "medium",
            "context": "Carol will update the design system by Friday.",
        },
        {
            "description": "Write E2E test suite for the checkout flow",
            "assignee_hint": "Dave",
            "due_date_hint": None,
            "priority": "medium",
            "context": "TODO: Write E2E test suite for the checkout flow",
        },
        {
            "description": "Update stakeholder presentation",
            "assignee_hint": "Alice",
            "due_date_hint": "by next Monday",
            "priority": "medium",
            "context": "Action Item: Update stakeholder presentation by next Monday",
        },
        {
            "description": "Set up the test environment",
            "assignee_hint": "Dave",
            "due_date_hint": "by end of day",
            "priority": "urgent",
            "context": "Dave: I'll set up the test environment by end of day.",
        },
    ],
    "decisions": [
        {
            "description": "Drop the mobile-first approach for now",
            "made_by_hint": "Carol",
            "context": "we decided to drop the mobile-first approach for now",
        },
        {
            "description": "New architecture design approved",
            "made_by_hint": "Bob",
            "context": "We approved the new architecture design.",
        },
    ],
    "follow_ups": [
        {
            "description": "Confirm design token finalization",
            "owner_hint": "Carol",
        }
    ],
    "confidence": 0.92,
    "warnings": [],
}


@pytest.fixture
def extractor() -> MeetingExtractor:
    return MeetingExtractor()


@pytest.fixture
def mock_vertex() -> MagicMock:
    client = MagicMock()
    client.generate_text = AsyncMock(return_value=json.dumps(SAMPLE_LLM_JSON))
    return client


@pytest.fixture
def analyzer(mock_vertex: MagicMock) -> MeetingAnalyzer:
    return MeetingAnalyzer(
        vertex_client=mock_vertex,
        extractor=MeetingExtractor(),
    )


# ===========================================================================
# TestMeetingExtractor — pattern-based extraction
# ===========================================================================

class TestMeetingExtractor:

    def test_detects_todo_prefix(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("TODO: Write the deployment script")
        assert len(pre.explicit_actions) >= 1
        assert any("deployment script" in a.lower() for a in pre.explicit_actions)

    def test_detects_action_item_prefix(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("Action Item: Schedule review with client by Friday")
        assert len(pre.explicit_actions) >= 1

    def test_detects_at_mention_action(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("@alice will review the pull request")
        assert len(pre.at_mention_actions) >= 1
        person, action = pre.at_mention_actions[0]
        assert person.lower() == "alice"
        assert "pull request" in action.lower()

    def test_detects_name_verb_action(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("Bob will finish the backend migration by Thursday.")
        assert len(pre.name_verb_actions) >= 1
        person, action = pre.name_verb_actions[0]
        assert "bob" in person.lower()

    def test_detects_decision_agreed(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("We agreed to postpone the release to next quarter.")
        assert len(pre.decision_sentences) >= 1
        assert any("agreed" in s.lower() for s in pre.decision_sentences)

    def test_detects_decision_decided(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("The team decided to migrate to PostgreSQL.")
        assert len(pre.decision_sentences) >= 1

    def test_detects_date_hint_by_friday(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("Please finish the report by Friday.")
        assert len(pre.date_hints) >= 1
        assert any("friday" in h.lower() for h in pre.date_hints)

    def test_detects_date_hint_eod(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("Send the summary EOD.")
        assert len(pre.date_hints) >= 1

    def test_detects_participants_at_mention(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("@alice and @bob please review this.")
        assert "alice" in [p.lower() for p in pre.participants]
        assert "bob" in [p.lower() for p in pre.participants]

    def test_detects_participants_name_colon(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("Alice: Let's start.\nBob: Agreed.")
        names_lower = [p.lower() for p in pre.participants]
        assert "alice" in names_lower
        assert "bob" in names_lower

    def test_empty_text_returns_empty(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("")
        assert isinstance(pre, PreExtractedData)
        assert not pre.has_content

    def test_whitespace_only_returns_empty(self, extractor: MeetingExtractor) -> None:
        pre = extractor.extract("   \n\t  ")
        assert not pre.has_content

    def test_full_transcript_extracts_multiple_items(
        self, extractor: MeetingExtractor
    ) -> None:
        pre = extractor.extract(SAMPLE_TRANSCRIPT)
        assert len(pre.explicit_actions) >= 2      # TODO + Action Item
        assert len(pre.name_verb_actions) >= 1    # "Bob will…", "Carol will…"
        assert len(pre.decision_sentences) >= 1   # "agreed", "decided", "approved"
        assert len(pre.date_hints) >= 1
        assert len(pre.participants) >= 2


# ===========================================================================
# TestMeetingAnalyzer — LLM response parsing
# ===========================================================================

class TestMeetingAnalyzer:

    @pytest.mark.asyncio
    async def test_returns_meeting_notes_parse_response(
        self, analyzer: MeetingAnalyzer
    ) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        assert isinstance(result, MeetingNotesParseResponse)

    @pytest.mark.asyncio
    async def test_action_items_extracted(self, analyzer: MeetingAnalyzer) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        assert len(result.analysis.action_items) == 5

    @pytest.mark.asyncio
    async def test_action_items_have_required_fields(
        self, analyzer: MeetingAnalyzer
    ) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        for item in result.analysis.action_items:
            assert item.description
            assert item.priority in ("low", "medium", "high", "urgent")

    @pytest.mark.asyncio
    async def test_decisions_extracted(self, analyzer: MeetingAnalyzer) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        assert len(result.analysis.decisions) == 2

    @pytest.mark.asyncio
    async def test_participants_detected(self, analyzer: MeetingAnalyzer) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        names = result.analysis.participants_detected
        assert len(names) >= 4

    @pytest.mark.asyncio
    async def test_summary_not_empty(self, analyzer: MeetingAnalyzer) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        assert len(result.analysis.summary) > 10

    @pytest.mark.asyncio
    async def test_confidence_in_range(self, analyzer: MeetingAnalyzer) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        assert 0.0 <= result.analysis.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_source_type_default_is_text(
        self, analyzer: MeetingAnalyzer
    ) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        assert result.source_type == "text"

    @pytest.mark.asyncio
    async def test_source_type_file_preserved(
        self, analyzer: MeetingAnalyzer
    ) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT, source_type="file")
        assert result.source_type == "file"

    @pytest.mark.asyncio
    async def test_raw_text_length_matches(self, analyzer: MeetingAnalyzer) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        assert result.raw_text_length == len(SAMPLE_TRANSCRIPT)

    @pytest.mark.asyncio
    async def test_fallback_on_invalid_json(
        self, mock_vertex: MagicMock
    ) -> None:
        mock_vertex.generate_text = AsyncMock(return_value="not {{ valid json")
        az = MeetingAnalyzer(vertex_client=mock_vertex, extractor=MeetingExtractor())
        result = await az.analyze(SAMPLE_TRANSCRIPT)
        assert result.analysis.confidence == 0.0
        assert any("unavailable" in w.lower() for w in result.analysis.warnings)

    @pytest.mark.asyncio
    async def test_fallback_on_vertex_error(self, mock_vertex: MagicMock) -> None:
        mock_vertex.generate_text = AsyncMock(
            side_effect=RuntimeError("Vertex API unreachable")
        )
        az = MeetingAnalyzer(vertex_client=mock_vertex, extractor=MeetingExtractor())
        result = await az.analyze(SAMPLE_TRANSCRIPT)
        assert result.analysis.confidence == 0.0
        # Fallback uses pattern extraction — should still find some items
        assert isinstance(result.analysis.action_items, list)

    @pytest.mark.asyncio
    async def test_run_delegates_to_analyze(
        self, analyzer: MeetingAnalyzer
    ) -> None:
        result = await analyzer.run(text=SAMPLE_TRANSCRIPT, source_type="text")
        assert isinstance(result, MeetingNotesParseResponse)

    @pytest.mark.asyncio
    async def test_assignee_hints_present(self, analyzer: MeetingAnalyzer) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        hints = [a.assignee_hint for a in result.analysis.action_items if a.assignee_hint]
        assert len(hints) >= 3   # Bob, Carol, Dave, Alice at minimum

    @pytest.mark.asyncio
    async def test_urgent_priority_set_for_eod_task(
        self, analyzer: MeetingAnalyzer
    ) -> None:
        result = await analyzer.analyze(SAMPLE_TRANSCRIPT)
        urgent = [a for a in result.analysis.action_items if a.priority == "urgent"]
        assert len(urgent) >= 1


# ===========================================================================
# TestMeetingRouter — integration tests
# ===========================================================================

class TestMeetingRouter:

    @pytest.fixture
    def client(self, mock_vertex: MagicMock):
        from fastapi.testclient import TestClient
        from src.main import app
        from src.agents.meeting_notes.analyzer import get_meeting_analyzer
        from src.agents.meeting_notes.extractor import get_meeting_extractor

        test_extractor = MeetingExtractor()
        test_analyzer = MeetingAnalyzer(
            vertex_client=mock_vertex, extractor=test_extractor
        )

        app.dependency_overrides[get_meeting_extractor] = lambda: test_extractor
        app.dependency_overrides[get_meeting_analyzer] = lambda: test_analyzer

        with TestClient(app) as c:
            yield c

        app.dependency_overrides.clear()

    def test_file_upload_returns_200(self, client) -> None:
        response = client.post(
            "/api/v1/agents/meeting/analyze",
            headers={"X-Organization-ID": str(uuid4())},
            files={"file": ("meeting.txt", SAMPLE_TRANSCRIPT.encode(), "text/plain")},
        )
        assert response.status_code == 200

    def test_text_form_field_returns_200(self, client) -> None:
        response = client.post(
            "/api/v1/agents/meeting/analyze",
            headers={"X-Organization-ID": str(uuid4())},
            data={"text": SAMPLE_TRANSCRIPT},
        )
        assert response.status_code == 200

    def test_response_has_analysis_field(self, client) -> None:
        response = client.post(
            "/api/v1/agents/meeting/analyze",
            headers={"X-Organization-ID": str(uuid4())},
            data={"text": SAMPLE_TRANSCRIPT},
        )
        body = response.json()
        assert "analysis" in body
        assert "action_items" in body["analysis"]
        assert "decisions" in body["analysis"]
        assert "summary" in body["analysis"]

    def test_empty_input_returns_400(self, client) -> None:
        response = client.post(
            "/api/v1/agents/meeting/analyze",
            headers={"X-Organization-ID": str(uuid4())},
            data={"text": "   "},
        )
        assert response.status_code == 400

    def test_no_input_returns_400(self, client) -> None:
        response = client.post(
            "/api/v1/agents/meeting/analyze",
            headers={"X-Organization-ID": str(uuid4())},
        )
        assert response.status_code == 400

    def test_missing_org_header_returns_422(self, client) -> None:
        response = client.post(
            "/api/v1/agents/meeting/analyze",
            data={"text": SAMPLE_TRANSCRIPT},
        )
        assert response.status_code == 422

    def test_unsupported_file_type_returns_415(self, client) -> None:
        response = client.post(
            "/api/v1/agents/meeting/analyze",
            headers={"X-Organization-ID": str(uuid4())},
            files={"file": ("notes.pdf", b"%PDF-1.4", "application/pdf")},
        )
        assert response.status_code == 415

    def test_source_type_file_when_file_uploaded(self, client) -> None:
        response = client.post(
            "/api/v1/agents/meeting/analyze",
            headers={"X-Organization-ID": str(uuid4())},
            files={"file": ("meeting.txt", SAMPLE_TRANSCRIPT.encode(), "text/plain")},
        )
        assert response.json()["source_type"] == "file"

    def test_source_type_text_when_text_posted(self, client) -> None:
        response = client.post(
            "/api/v1/agents/meeting/analyze",
            headers={"X-Organization-ID": str(uuid4())},
            data={"text": SAMPLE_TRANSCRIPT},
        )
        assert response.json()["source_type"] == "text"
