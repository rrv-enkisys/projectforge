from __future__ import annotations

"""Meeting Notes analysis using Gemini via Vertex AI."""
import json
import logging
import re
from typing import Any

from fastapi import Depends

from ...agents.base import BaseAgent
from ...embeddings.vertex_client import VertexAIClient, get_vertex_client
from .extractor import MeetingExtractor, PreExtractedData, get_meeting_extractor
from .prompts import build_meeting_analysis_prompt
from .schemas import (
    ActionItem,
    Decision,
    FollowUp,
    MeetingAnalysis,
    MeetingNotesParseResponse,
)

logger = logging.getLogger(__name__)

_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    m = _JSON_FENCE_RE.search(text)
    return m.group(1).strip() if m else text.strip()


class MeetingAnalyzer(BaseAgent):
    """Analyses a meeting transcript with Gemini and returns structured data."""

    name = "meeting_notes"
    description = "Extracts action items and decisions from meeting transcripts using Gemini."

    def __init__(
        self,
        vertex_client: VertexAIClient = Depends(get_vertex_client),
        extractor: MeetingExtractor = Depends(get_meeting_extractor),
    ) -> None:
        self.vertex_client = vertex_client
        self.extractor = extractor

    # BaseAgent interface
    async def run(self, **kwargs: Any) -> MeetingNotesParseResponse:
        """Entry point used by the agent framework.

        Kwargs:
            text: Raw meeting transcript string.
            source_type: ``"text"`` or ``"file"``.
        """
        text: str = kwargs["text"]
        source_type: str = kwargs.get("source_type", "text")
        return await self.analyze(text, source_type=source_type)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze(
        self,
        text: str,
        source_type: str = "text",
    ) -> MeetingNotesParseResponse:
        """Run pattern extraction then call Gemini for deep analysis."""
        pre = self.extractor.extract(text)
        prompt = build_meeting_analysis_prompt(text)

        try:
            raw = await self.vertex_client.generate_text(
                prompt=prompt,
                temperature=0.2,
                max_output_tokens=4096,
            )
            analysis = self._parse_response(raw, pre, text)
        except Exception as exc:
            logger.warning("Gemini unavailable for meeting analysis: %s", exc)
            analysis = self._fallback_analysis(pre, text)

        return MeetingNotesParseResponse(
            analysis=analysis,
            raw_text_length=len(text),
            source_type=source_type,  # type: ignore[arg-type]
        )

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_response(
        self,
        raw: str,
        pre: PreExtractedData,
        text: str,
    ) -> MeetingAnalysis:
        try:
            data: dict = json.loads(_strip_fences(raw))
        except json.JSONDecodeError as exc:
            logger.warning("LLM returned invalid JSON for meeting analysis: %s", exc)
            return self._fallback_analysis(pre, text)

        action_items = [
            ActionItem(
                description=a.get("description") or "",
                assignee_hint=a.get("assignee_hint"),
                due_date_hint=a.get("due_date_hint"),
                priority=a.get("priority") or "medium",
                context=a.get("context"),
            )
            for a in (data.get("action_items") or [])
            if a.get("description")
        ]

        decisions = [
            Decision(
                description=d.get("description") or "",
                made_by_hint=d.get("made_by_hint"),
                context=d.get("context"),
            )
            for d in (data.get("decisions") or [])
            if d.get("description")
        ]

        follow_ups = [
            FollowUp(
                description=f.get("description") or "",
                owner_hint=f.get("owner_hint"),
            )
            for f in (data.get("follow_ups") or [])
            if f.get("description")
        ]

        # Merge pattern-detected participants not caught by LLM
        llm_participants: list[str] = data.get("participants") or []
        llm_names_lower = {p.lower() for p in llm_participants}
        for p in pre.participants:
            if p.lower() not in llm_names_lower:
                llm_participants.append(p)

        return MeetingAnalysis(
            summary=data.get("summary") or "No summary available.",
            action_items=action_items,
            decisions=decisions,
            follow_ups=follow_ups,
            participants_detected=llm_participants,
            meeting_date_hint=data.get("meeting_date_hint"),
            confidence=float(data.get("confidence") or 0.7),
            warnings=list(data.get("warnings") or []),
        )

    def _fallback_analysis(self, pre: PreExtractedData, text: str) -> MeetingAnalysis:
        """Build a minimal analysis from pattern matches when AI is unavailable."""
        action_items: list[ActionItem] = []

        for item in pre.explicit_actions:
            action_items.append(ActionItem(description=item, priority="medium"))

        for person, action in pre.at_mention_actions:
            action_items.append(
                ActionItem(description=action, assignee_hint=person, priority="medium")
            )

        for person, action in pre.name_verb_actions:
            # Avoid duplicates already captured by at_mention
            existing = {a.description for a in action_items}
            if action not in existing:
                action_items.append(
                    ActionItem(description=action, assignee_hint=person, priority="medium")
                )

        decisions = [
            Decision(description=s)
            for s in pre.decision_sentences
        ]

        return MeetingAnalysis(
            summary=f"Pattern-based extraction found {len(action_items)} action items "
                    f"and {len(decisions)} decisions. AI analysis was unavailable.",
            action_items=action_items,
            decisions=decisions,
            follow_ups=[],
            participants_detected=pre.participants,
            confidence=0.0,
            warnings=["AI analysis unavailable. Results are pattern-based only."],
        )


def get_meeting_analyzer(
    vertex_client: VertexAIClient = Depends(get_vertex_client),
    extractor: MeetingExtractor = Depends(get_meeting_extractor),
) -> MeetingAnalyzer:
    """FastAPI dependency that returns a :class:`MeetingAnalyzer` instance."""
    return MeetingAnalyzer(vertex_client=vertex_client, extractor=extractor)
