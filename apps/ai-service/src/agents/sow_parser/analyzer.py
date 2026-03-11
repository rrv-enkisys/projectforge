from __future__ import annotations

"""SOW analysis using Gemini via Vertex AI."""
import json
import logging
import re
from typing import Any

from fastapi import Depends

from ...agents.base import BaseAgent
from ...embeddings.vertex_client import VertexAIClient, get_vertex_client
from .extractor import ExtractedDocument
from .prompts import build_sow_analysis_prompt
from .schemas import (
    MilestoneSuggestion,
    ProjectSuggestion,
    SOWParseResponse,
    SOWSection,
    TaskSuggestion,
)

logger = logging.getLogger(__name__)

# Strip markdown code fences that some LLM outputs include
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _strip_fences(text: str) -> str:
    m = _JSON_FENCE_RE.search(text)
    return m.group(1).strip() if m else text.strip()


class SOWAnalyzer(BaseAgent):
    """Analyses a SOW document with Gemini and returns a structured project plan."""

    name = "sow_parser"
    description = "Parses Statements of Work into structured project plans using Gemini."

    def __init__(
        self,
        vertex_client: VertexAIClient = Depends(get_vertex_client),
    ) -> None:
        self.vertex_client = vertex_client

    # BaseAgent interface
    async def run(self, **kwargs: Any) -> SOWParseResponse:
        """Entry point used by the agent framework.

        Pass ``doc`` as a keyword argument containing an :class:`ExtractedDocument`.
        """
        doc: ExtractedDocument = kwargs["doc"]
        return await self.analyze(doc)

    # Public API
    async def analyze(self, doc: ExtractedDocument) -> SOWParseResponse:
        """Call Gemini with the SOW text and parse the structured JSON response."""
        prompt = build_sow_analysis_prompt(doc.full_text)
        try:
            raw = await self.vertex_client.generate_text(
                prompt=prompt,
                temperature=0.2,
                max_output_tokens=4096,
            )
            return self._parse_response(raw, doc)
        except Exception as exc:
            logger.warning("Gemini unavailable for SOW analysis: %s", exc)
            return self._fallback_response(doc)

    # ------------------------------------------------------------------
    # Parsing helpers
    # ------------------------------------------------------------------

    def _parse_response(self, raw: str, doc: ExtractedDocument) -> SOWParseResponse:
        try:
            data: dict = json.loads(_strip_fences(raw))
        except json.JSONDecodeError as exc:
            logger.warning("LLM returned invalid JSON for SOW analysis: %s", exc)
            return self._fallback_response(doc)

        project_data = data.get("project") or {}
        project = ProjectSuggestion(
            name=project_data.get("name") or "Unnamed Project",
            description=project_data.get("description") or "",
            estimated_duration_days=project_data.get("estimated_duration_days"),
            estimated_budget=project_data.get("estimated_budget"),
            currency=project_data.get("currency") or "USD",
        )

        milestones = [
            MilestoneSuggestion(
                title=m.get("title") or "",
                description=m.get("description") or "",
                target_date_offset_days=m.get("target_date_offset_days"),
            )
            for m in (data.get("milestones") or [])
            if m.get("title")
        ]

        tasks = [
            TaskSuggestion(
                title=t.get("title") or "",
                description=t.get("description") or "",
                estimated_hours=t.get("estimated_hours"),
                priority=t.get("priority") or "medium",
                milestone_index=t.get("milestone_index"),
            )
            for t in (data.get("tasks") or [])
            if t.get("title")
        ]

        # Sections reported by the LLM
        sections_data: dict[str, str | None] = data.get("sections") or {}
        raw_sections: list[SOWSection] = [
            SOWSection(name=k, content=v, confidence=0.85)
            for k, v in sections_data.items()
            if v
        ]

        # Supplement with extractor-detected sections not covered by LLM
        llm_section_names = {s.name for s in raw_sections}
        for section_name, content in doc.sections.items():
            if section_name not in llm_section_names and content:
                raw_sections.append(
                    SOWSection(name=section_name, content=content, confidence=0.6)
                )

        return SOWParseResponse(
            project=project,
            milestones=milestones,
            tasks=tasks,
            raw_sections=raw_sections,
            confidence=float(data.get("confidence") or 0.7),
            warnings=list(data.get("warnings") or []),
        )

    @staticmethod
    def _fallback_response(doc: ExtractedDocument) -> SOWParseResponse:
        """Minimal response when AI is unavailable."""
        sections = [
            SOWSection(name=k, content=v, confidence=0.5)
            for k, v in doc.sections.items()
            if v
        ]
        return SOWParseResponse(
            project=ProjectSuggestion(
                name="Project (review required)",
                description=doc.full_text[:500] if doc.full_text else "",
            ),
            milestones=[],
            tasks=[],
            raw_sections=sections,
            confidence=0.0,
            warnings=["AI analysis unavailable. Review the extracted sections manually."],
        )


def get_sow_analyzer(
    vertex_client: VertexAIClient = Depends(get_vertex_client),
) -> SOWAnalyzer:
    """FastAPI dependency that returns a :class:`SOWAnalyzer` instance."""
    return SOWAnalyzer(vertex_client=vertex_client)
