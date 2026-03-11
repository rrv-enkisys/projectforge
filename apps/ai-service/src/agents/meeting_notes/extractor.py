from __future__ import annotations

"""Pattern-based pre-extraction for meeting transcripts.

This module does a fast heuristic scan of the raw text to detect
action items, decisions, date hints, and participants *before* the LLM
call.  The results are passed as supplementary context to the Gemini
prompt so the model has a head-start on structured extraction.
"""
import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Compiled patterns
# ---------------------------------------------------------------------------

# Explicit prefixes: "TODO:", "Action:", "AI:", "Action Item:"
# Also matches when preceded by a speaker prefix like "Dave: TODO: ..."
_EXPLICIT_ACTION_RE = re.compile(
    r"(?:^|(?:[A-Za-z][A-Za-z\s]*:\s+))(?:TODO|Action\s*Item?|AI|AP)\s*[:–\-]\s*(.+)",
    re.IGNORECASE | re.MULTILINE,
)

# "@mention will/needs to/should …"
_AT_MENTION_RE = re.compile(
    r"@(\w+)\s+(?:will|to|should|needs?\s+to|must|is\s+going\s+to)\s+(.+?)(?:\.|$)",
    re.IGNORECASE | re.MULTILINE,
)

# "Name will / needs to / is going to …"
_NAME_VERB_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:will|needs?\s+to|is\s+going\s+to|should|must)\s+(.+?)(?:\.|$)",
    re.MULTILINE,
)

# "agreed/decided/approved/resolved/confirmed …"
_DECISION_RE = re.compile(
    r"\b(?:agreed|decided|approved|resolved|confirmed|chosen)\b.{0,100}",
    re.IGNORECASE | re.MULTILINE,
)

# Date hints: "by Friday", "by next week", "EOD", "by March 15"
_DATE_HINT_RE = re.compile(
    r"\bby\s+((?:next\s+)?(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday"
    r"|week|month|end\s+of\s+(?:day|week)|tomorrow|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?))"
    r"|\b(EOD|end\s+of\s+day|end\s+of\s+week|tomorrow)\b",
    re.IGNORECASE,
)

# Participants: "@mention" or "Name:" at start of line
_PARTICIPANT_RE = re.compile(
    r"@(\w+)|^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s*:",
    re.MULTILINE,
)


@dataclass
class PreExtractedData:
    """Heuristic extraction results used to prime the LLM prompt."""

    explicit_actions: list[str] = field(default_factory=list)
    at_mention_actions: list[tuple[str, str]] = field(default_factory=list)  # (person, action)
    name_verb_actions: list[tuple[str, str]] = field(default_factory=list)  # (person, action)
    decision_sentences: list[str] = field(default_factory=list)
    date_hints: list[str] = field(default_factory=list)
    participants: list[str] = field(default_factory=list)

    @property
    def has_content(self) -> bool:
        return bool(
            self.explicit_actions
            or self.at_mention_actions
            or self.name_verb_actions
            or self.decision_sentences
        )


class MeetingExtractor:
    """Fast pattern-based scanner for meeting transcripts."""

    def extract(self, text: str) -> PreExtractedData:
        """Scan *text* and return heuristic extraction results."""
        if not text or not text.strip():
            return PreExtractedData()

        data = PreExtractedData()

        # Explicit action items
        for m in _EXPLICIT_ACTION_RE.finditer(text):
            item = m.group(1).strip()
            if item:
                data.explicit_actions.append(item)

        # @mention actions
        for m in _AT_MENTION_RE.finditer(text):
            person = m.group(1).strip()
            action = m.group(2).strip()
            if action:
                data.at_mention_actions.append((person, action))

        # "Name will …" actions
        for m in _NAME_VERB_RE.finditer(text):
            person = m.group(1).strip()
            action = m.group(2).strip()
            if action and len(person) > 1:
                data.name_verb_actions.append((person, action))

        # Decision sentences
        for m in _DECISION_RE.finditer(text):
            sentence = m.group(0).strip()
            if sentence:
                data.decision_sentences.append(sentence)

        # Date hints
        for m in _DATE_HINT_RE.finditer(text):
            hint = (m.group(1) or m.group(2) or "").strip()
            if hint and hint not in data.date_hints:
                data.date_hints.append(hint)

        # Participants
        seen: set[str] = set()
        for m in _PARTICIPANT_RE.finditer(text):
            name = (m.group(1) or m.group(2) or "").strip()
            if name and name.lower() not in seen:
                seen.add(name.lower())
                data.participants.append(name)

        return data


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------
_meeting_extractor: MeetingExtractor | None = None


def get_meeting_extractor() -> MeetingExtractor:
    """Return the shared :class:`MeetingExtractor` singleton."""
    global _meeting_extractor
    if _meeting_extractor is None:
        _meeting_extractor = MeetingExtractor()
    return _meeting_extractor
