from __future__ import annotations

"""SOW Parser agent — FastAPI router."""
import logging
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, UploadFile, status

from .analyzer import SOWAnalyzer, get_sow_analyzer
from .extractor import SOWExtractor, get_sow_extractor
from .schemas import SOWParseResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents/sow", tags=["agents", "sow-parser"])

_ALLOWED_CONTENT_TYPES = frozenset({
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
    "text/markdown",
})

_ALLOWED_EXTENSIONS = frozenset({"pdf", "docx", "txt", "md"})

_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post("/parse", response_model=SOWParseResponse, status_code=status.HTTP_200_OK)
async def parse_sow(
    file: UploadFile,
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
    extractor: SOWExtractor = Depends(get_sow_extractor),
    analyzer: SOWAnalyzer = Depends(get_sow_analyzer),
) -> SOWParseResponse:
    """Parse a Statement of Work document and return a structured project plan.

    Accepts PDF, DOCX, TXT, or Markdown files up to 10 MB.

    Returns:
        Suggested project, milestones, tasks, and extracted document sections.
    """
    content_type = file.content_type or "application/octet-stream"

    # Normalise content type: fall back to extension-based detection
    if content_type not in _ALLOWED_CONTENT_TYPES:
        filename = file.filename or ""
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in _ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=(
                    f"Unsupported file type '{content_type}'. "
                    "Accepted formats: PDF, DOCX, TXT, Markdown."
                ),
            )
        content_type = f".{ext}"

    file_bytes = await file.read()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    if len(file_bytes) > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds the maximum allowed size of {_MAX_FILE_BYTES // (1024 * 1024)} MB.",
        )

    logger.info(
        "SOW parse request: org=%s filename=%r size=%d bytes",
        x_organization_id,
        file.filename,
        len(file_bytes),
    )

    doc = await extractor.extract(file_bytes, content_type)
    result = await analyzer.analyze(doc)

    logger.info(
        "SOW parse complete: org=%s project=%r milestones=%d tasks=%d confidence=%.2f",
        x_organization_id,
        result.project.name,
        len(result.milestones),
        len(result.tasks),
        result.confidence,
    )

    return result
