"""Document API endpoints"""
import io
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, UploadFile, status

from .schemas import DocumentListResponse, DocumentResponse, DocumentWithChunks
from .service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"], redirect_slashes=False)


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    project_id: UUID | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: DocumentService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
) -> DocumentListResponse:
    """List documents for the organization, optionally filtered by project"""
    documents, total = await service.list_documents(
        organization_id=x_organization_id,
        project_id=project_id,
        skip=skip,
        limit=limit,
    )
    return DocumentListResponse(
        data=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    project_id: UUID = Form(...),
    name: str | None = Form(None),
    service: DocumentService = Depends(),
    x_organization_id: UUID = Header(..., alias="X-Organization-ID"),
    x_user_id: str = Header(default="", alias="X-User-ID"),
) -> DocumentResponse:
    """Upload a new document. Will be chunked and embedded asynchronously."""
    content = await file.read()
    file_name = name or file.filename or "document"
    file_type = file.content_type or "application/octet-stream"

    # Resolve uploaded_by: use X-User-ID if it's a valid UUID, else fall back to org's first user
    try:
        uploaded_by = UUID(x_user_id)
    except (ValueError, AttributeError):
        uploaded_by = await service.get_default_user_id(x_organization_id)

    document = await service.upload_and_process_document(
        file=io.BytesIO(content),
        file_name=file_name,
        file_type=file_type,
        file_size=len(content),
        project_id=project_id,
        organization_id=x_organization_id,
        uploaded_by=uploaded_by,
    )
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
        data=[DocumentResponse.model_validate(doc) for doc in documents],
        total=total,
        skip=skip,
        limit=limit,
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
