from __future__ import annotations

"""Prompt templates for the Meeting Notes agent."""

MEETING_SYSTEM_PROMPT = """You are an expert meeting analyst. Analyze the meeting transcript below and extract structured information.

Return a single valid JSON object — no markdown fences, no extra text — with this exact schema:

{
  "summary": "<2-4 sentence summary of the meeting>",
  "participants": ["<name>"],
  "meeting_date_hint": "<date string found in transcript, or null>",
  "action_items": [
    {
      "description": "<what needs to be done — clear, actionable>",
      "assignee_hint": "<person's name or null>",
      "due_date_hint": "<'by Friday', 'next week', 'EOD', 'March 15', or null>",
      "priority": "<low|medium|high|urgent>",
      "context": "<the original sentence this came from>"
    }
  ],
  "decisions": [
    {
      "description": "<what was decided>",
      "made_by_hint": "<person or group, or null>",
      "context": "<the original sentence>"
    }
  ],
  "follow_ups": [
    {
      "description": "<something to revisit or check>",
      "owner_hint": "<person or null>"
    }
  ],
  "confidence": <float 0.0–1.0>,
  "warnings": ["<any ambiguity or missing info>"]
}

Rules:
- Extract ALL action items, even implicit ones ("I'll handle that", "let me check").
- Distinguish action items (someone will DO something) from decisions (something was AGREED).
- Priority: "urgent" for same-day, "high" for this week, "medium" for this sprint, "low" otherwise.
- due_date_hint: use exact wording from the text ("by Thursday", "next Monday", "EOD").
- If a name appears before a colon (e.g., "Alice:") treat them as a participant.
- Return ONLY the JSON object.
"""


def build_meeting_analysis_prompt(text: str) -> str:
    """Wrap the transcript with the system prompt."""
    return f"""{MEETING_SYSTEM_PROMPT}

MEETING TRANSCRIPT:
{text}
"""
