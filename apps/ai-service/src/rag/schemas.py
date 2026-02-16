"""RAG schemas"""
from uuid import UUID

from pydantic import BaseModel, Field


class RAGQuery(BaseModel):
    """Schema for RAG query request"""

    question: str = Field(..., min_length=1, max_length=1000)
    project_id: UUID
    max_chunks: int = Field(default=5, ge=1, le=10)


class SourceChunk(BaseModel):
    """Schema for source chunk information"""

    document_id: str
    chunk_id: str
    content: str
    similarity: float
    chunk_index: int


class RAGResponse(BaseModel):
    """Schema for RAG query response"""

    answer: str
    sources: list[SourceChunk]
    confidence: str  # high, medium, low
    chunks_retrieved: int
