"""RAG API endpoints"""
from uuid import UUID

from fastapi import APIRouter, Depends, Header
from fastapi.responses import StreamingResponse

from .schemas import RAGQuery, RAGResponse
from .service import RAGService

router = APIRouter(prefix="/rag", tags=["rag"])


@router.post("/query", response_model=RAGResponse)
async def query_documents(
    data: RAGQuery,
    service: RAGService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> RAGResponse:
    """
    Query project documents using RAG.
    Returns an AI-generated answer based on relevant document chunks.
    """
    result = await service.query(
        question=data.question,
        project_id=data.project_id,
        organization_id=x_organization_id,
        max_chunks=data.max_chunks
    )
    return RAGResponse(**result)


@router.post("/query/stream")
async def query_documents_stream(
    data: RAGQuery,
    service: RAGService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> StreamingResponse:
    """
    Query project documents using RAG with streaming response.
    Returns answer as a text stream for better UX.
    """
    async def generate():
        async for chunk in service.stream_query(
            question=data.question,
            project_id=data.project_id,
            organization_id=x_organization_id,
            max_chunks=data.max_chunks
        ):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/plain"
    )
