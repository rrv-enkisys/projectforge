from __future__ import annotations

"""Document service layer"""
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from .models import Document
from .repository import DocumentRepository
from .schemas import DocumentUpload


class DocumentService:
    """Service for document business logic"""

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.repository = DocumentRepository(db)

    async def create_document(
        self,
        data: DocumentUpload,
        organization_id: UUID
    ) -> Document:
        """Create a new document and initiate processing"""
        return await self.repository.create(data, organization_id)

    async def get_document(
        self,
        document_id: UUID,
        organization_id: UUID,
        with_chunks: bool = False
    ) -> Document | None:
        """Get document by ID"""
        return await self.repository.get_by_id(document_id, organization_id, with_chunks)

    async def list_project_documents(
        self,
        project_id: UUID,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Document], int]:
        """List documents for a project"""
        return await self.repository.get_by_project(project_id, organization_id, skip, limit)

    async def update_document_status(
        self,
        document_id: UUID,
        status: str,
        error_message: str | None = None
    ) -> Document | None:
        """Update document processing status"""
        return await self.repository.update_status(document_id, status, error_message)

    async def delete_document(
        self,
        document_id: UUID,
        organization_id: UUID
    ) -> bool:
        """Delete a document and its chunks"""
        return await self.repository.delete(document_id, organization_id)
