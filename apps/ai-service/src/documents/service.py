from __future__ import annotations

"""Document service layer"""
from typing import BinaryIO
from uuid import UUID, uuid4

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from .models import Document
from .processor import get_document_processor
from .repository import DocumentRepository
from .schemas import DocumentUpload


class DocumentService:
    """Service for document business logic"""

    def __init__(self, db: AsyncSession = Depends(get_db)):
        self.db = db
        self.repository = DocumentRepository(db)
        self.processor = get_document_processor(db)

    async def upload_and_process_document(
        self,
        file: BinaryIO,
        file_name: str,
        file_type: str,
        file_size: int,
        project_id: UUID,
        organization_id: UUID,
    ) -> Document:
        """Upload and process a new document."""
        # Create document record
        document_id = uuid4()
        document = Document(
            id=document_id,
            project_id=project_id,
            organization_id=organization_id,
            name=file_name,
            file_path="",  # Will be set during processing
            file_type=file_type,
            file_size=file_size,
            status="pending",
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)

        # Process document asynchronously (in background)
        # In production, this would be a background task (Celery, Cloud Tasks, etc.)
        try:
            processed_doc = await self.processor.process_document(
                document_id=document_id,
                file=file,
                file_name=file_name,
                file_type=file_type,
                organization_id=organization_id,
                project_id=project_id,
            )
            return processed_doc
        except Exception as e:
            # If processing fails, document status will be "failed"
            await self.db.refresh(document)
            raise

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

    async def list_documents(
        self,
        organization_id: UUID,
        project_id: UUID | None = None,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Document], int]:
        """List documents for an org with optional project filter"""
        return await self.repository.get_by_org(organization_id, project_id, skip, limit)

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
        # Also delete file from storage
        document = await self.repository.get_by_id(document_id, organization_id)
        if document and document.file_path:
            from .storage import get_storage_service

            storage = get_storage_service()
            await storage.delete_file(document.file_path)

        return await self.repository.delete(document_id, organization_id)

    async def reprocess_document(
        self, document_id: UUID, organization_id: UUID
    ) -> Document:
        """Reprocess an existing document."""
        return await self.processor.reprocess_document(document_id, organization_id)
