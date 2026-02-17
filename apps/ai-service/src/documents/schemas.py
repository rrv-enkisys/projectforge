from __future__ import annotations

"""Document schemas for validation"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentUpload(BaseModel):
    """Schema for document upload"""

    name: str = Field(..., min_length=1, max_length=255)
    project_id: UUID
    file_type: str
    file_size: int = Field(..., gt=0)
    file_path: str  # GCS path


class DocumentUpdate(BaseModel):
    """Schema for document update"""

    status: str | None = None
    error_message: str | None = None


class ChunkResponse(BaseModel):
    """Schema for document chunk response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    document_id: UUID
    content: str
    chunk_index: int
    token_count: int
    created_at: datetime


class DocumentResponse(BaseModel):
    """Schema for document response"""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    organization_id: UUID
    name: str
    file_path: str
    file_type: str
    file_size: int
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class DocumentWithChunks(DocumentResponse):
    """Document response with chunks"""

    chunks: list[ChunkResponse]


class DocumentListResponse(BaseModel):
    """Paginated list of documents"""

    items: list[DocumentResponse]
    total: int
    skip: int
    limit: int
