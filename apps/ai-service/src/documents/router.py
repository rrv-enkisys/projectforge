"""Document API endpoints"""
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from .schemas import DocumentListResponse, DocumentResponse, DocumentUpload, DocumentWithChunks
from .service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("/", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    data: DocumentUpload,
    service: DocumentService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> DocumentResponse:
    """
    Upload a new document for processing.
    Document will be chunked and embedded asynchronously.
    """
    document = await service.create_document(data, x_organization_id)
    return DocumentResponse.model_validate(document)


@router.get("/{document_id}", response_model=DocumentWithChunks)
async def get_document(
    document_id: UUID,
    include_chunks: bool = False,
    service: DocumentService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> DocumentWithChunks:
    """Get document by ID, optionally including chunks"""
    document = await service.get_document(document_id, x_organization_id, include_chunks)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return DocumentWithChunks.model_validate(document)


@router.get("/project/{project_id}", response_model=DocumentListResponse)
async def list_project_documents(
    project_id: UUID,
    skip: int = 0,
    limit: int = 20,
    service: DocumentService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
) -> DocumentListResponse:
    """List all documents for a project"""
    documents, total = await service.list_project_documents(
        project_id,
        x_organization_id,
        skip,
        limit
    )
    return DocumentListResponse(
        items=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        skip=skip,
        limit=limit
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    service: DocumentService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID")
):
    """Delete a document and all its chunks"""
    deleted = await service.delete_document(document_id, x_organization_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
