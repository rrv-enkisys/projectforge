"""Document processing pipeline."""

import logging
from typing import BinaryIO
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..embeddings.chunker import get_chunker
from ..embeddings.vertex_client import get_vertex_client
from .extractor import get_text_extractor
from .models import Document, DocumentChunk
from .repository import DocumentRepository
from .storage import get_storage_service

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Orchestrates the document processing pipeline."""

    def __init__(self, db: AsyncSession):
        """Initialize document processor."""
        self.db = db
        self.repository = DocumentRepository(db)
        self.storage = get_storage_service()
        self.extractor = get_text_extractor()
        self.chunker = get_chunker()
        self.vertex_client = get_vertex_client()

    async def process_document(
        self,
        document_id: UUID,
        file: BinaryIO,
        file_name: str,
        file_type: str,
        organization_id: UUID,
        project_id: UUID,
    ) -> Document:
        """
        Process a document through the complete pipeline.

        Steps:
        1. Upload file to storage
        2. Extract text from file
        3. Chunk text
        4. Generate embeddings
        5. Store chunks with embeddings in database

        Args:
            document_id: Document UUID
            file: File object
            file_name: Original file name
            file_type: MIME type
            organization_id: Organization ID
            project_id: Project ID

        Returns:
            Processed document
        """
        try:
            # Update status to processing
            document = await self.repository.get_by_id(document_id, organization_id)
            if not document:
                raise ValueError(f"Document {document_id} not found")

            await self.repository.update_status(document_id, "processing")
            logger.info(f"Starting processing for document {document_id}: {file_name}")

            # Step 1: Upload to storage
            storage_path = await self.storage.upload_file(
                file, file_name, organization_id, project_id, file_type
            )
            logger.info(f"Uploaded to storage: {storage_path}")

            # Step 2: Download and extract text
            file_content = await self.storage.download_file(storage_path)
            text = await self.extractor.extract_text(file_content, file_type)

            if not text or not text.strip():
                raise ValueError("No text could be extracted from document")

            logger.info(f"Extracted {len(text)} characters from document")

            # Step 3: Chunk text
            chunks = self.chunker.chunk_text(text)
            logger.info(f"Created {len(chunks)} chunks from document")

            if not chunks:
                raise ValueError("No chunks created from document")

            # Step 4: Generate embeddings
            chunk_texts = [chunk[0] for chunk in chunks]
            embeddings = await self.vertex_client.generate_embeddings(
                chunk_texts, task_type="RETRIEVAL_DOCUMENT"
            )

            logger.info(f"Generated {len(embeddings)} embeddings")

            # Step 5: Store chunks with embeddings
            document_chunks = []
            for idx, ((chunk_text, token_count), embedding) in enumerate(
                zip(chunks, embeddings)
            ):
                chunk = DocumentChunk(
                    document_id=document_id,
                    content=chunk_text,
                    chunk_index=idx,
                    token_count=token_count,
                    embedding=embedding,
                )
                document_chunks.append(chunk)

            # Save chunks to database
            self.db.add_all(document_chunks)
            await self.db.commit()

            logger.info(f"Stored {len(document_chunks)} chunks in database")

            # Update document status to completed
            await self.repository.update_status(document_id, "completed")

            # Refresh document with chunks
            document = await self.repository.get_by_id(
                document_id, organization_id, with_chunks=True
            )

            logger.info(f"Successfully processed document {document_id}")
            return document

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}", exc_info=True)

            # Update status to failed
            await self.repository.update_status(
                document_id, "failed", error_message=str(e)
            )

            raise

    async def reprocess_document(
        self, document_id: UUID, organization_id: UUID
    ) -> Document:
        """
        Reprocess an existing document.

        Useful if:
        - Processing failed previously
        - Want to regenerate embeddings with new model
        - Document was updated

        Args:
            document_id: Document ID
            organization_id: Organization ID

        Returns:
            Reprocessed document
        """
        # Get document
        document = await self.repository.get_by_id(document_id, organization_id)
        if not document:
            raise ValueError(f"Document {document_id} not found")

        # Delete existing chunks
        await self.repository.delete_chunks(document_id)

        # Download file from storage
        file_content = await self.storage.download_file(document.file_path)

        # Create a file-like object
        import io

        file = io.BytesIO(file_content)

        # Reprocess
        return await self.process_document(
            document_id=document_id,
            file=file,
            file_name=document.name,
            file_type=document.file_type,
            organization_id=organization_id,
            project_id=document.project_id,
        )


def get_document_processor(db: AsyncSession) -> DocumentProcessor:
    """Get document processor instance."""
    return DocumentProcessor(db)
