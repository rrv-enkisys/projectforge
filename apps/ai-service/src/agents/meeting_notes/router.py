from __future__ import annotations

"""Meeting Notes agent — FastAPI router."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, UploadFile, status

from .analyzer import MeetingAnalyzer, get_meeting_analyzer
from .schemas import MeetingNotesParseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/meeting", tags=["agents", "meeting-notes"])

_ALLOWED_TEXT_TYPES = frozenset({
    "text/plain",
    "text/markdown",
    "text/vtt",      # WebVTT subtitles / transcripts
    "text/csv",
})
_ALLOWED_EXTENSIONS = frozenset({"txt", "md", "vtt", "csv"})
_MAX_FILE_BYTES = 5 * 1024 * 1024   # 5 MB
_MAX_TEXT_CHARS = 200_000            # ~50k words — well within Gemini context


@router.post(
    "/analyze",
    response_model=MeetingNotesParseResponse,
    status_code=status.HTTP_200_OK,
)
async def analyze_meeting_notes(
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
    file: UploadFile | None = File(default=None),
    text: str | None = Form(default=None),
    analyzer: MeetingAnalyzer = Depends(get_meeting_analyzer),
) -> MeetingNotesParseResponse:
    """Analyze a meeting transcript and extract action items and decisions.

    Accepts either:
    - ``file``: a plain-text transcript file (TXT, MD, VTT) up to 5 MB.
    - ``text``: raw transcript pasted as a form field (up to 200 k chars).

    Returns structured :class:`MeetingNotesParseResponse` with action items,
    decisions, follow-ups, and detected participants.
    """
    transcript: str
    source_type: str

    if file is not None and file.filename:
        # --- File upload path ---
        content_type = file.content_type or "application/octet-stream"
        if content_type not in _ALLOWED_TEXT_TYPES:
            filename = file.filename or ""
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            if ext not in _ALLOWED_EXTENSIONS:
                raise HTTPException(
                    status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                    detail=(
                        f"Unsupported file type '{content_type}'. "
                        "Accepted: TXT, Markdown, VTT."
                    ),
                )

        file_bytes = await file.read()
        if not file_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )
        if len(file_bytes) > _MAX_FILE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds {_MAX_FILE_BYTES // (1024 * 1024)} MB limit.",
            )

        transcript = file_bytes.decode("utf-8", errors="replace")
        source_type = "file"

    elif text:
        # --- Plain-text path ---
        if len(text) > _MAX_TEXT_CHARS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Text exceeds {_MAX_TEXT_CHARS:,} character limit.",
            )
        transcript = text
        source_type = "text"

    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide either a 'file' upload or a 'text' form field.",
        )

    if not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript is empty.",
        )

    logger.info(
        "Meeting analysis request: org=%s source=%s chars=%d",
        x_organization_id,
        source_type,
        len(transcript),
    )

    result = await analyzer.analyze(transcript, source_type=source_type)

    logger.info(
        "Meeting analysis complete: org=%s actions=%d decisions=%d confidence=%.2f",
        x_organization_id,
        len(result.analysis.action_items),
        len(result.analysis.decisions),
        result.analysis.confidence,
    )

    return result
