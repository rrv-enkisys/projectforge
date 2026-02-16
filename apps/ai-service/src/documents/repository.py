"""Document repository for database operations"""
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from .models import Document, DocumentChunk
from .schemas import DocumentUpload


class DocumentRepository:
    """Repository for document database operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, data: DocumentUpload, organization_id: UUID) -> Document:
        """Create a new document"""
        document = Document(
            **data.model_dump(),
            organization_id=organization_id,
            status="pending"
        )
        self.db.add(document)
        await self.db.commit()
        await self.db.refresh(document)
        return document

    async def get_by_id(
        self,
        document_id: UUID,
        organization_id: UUID,
        with_chunks: bool = False
    ) -> Document | None:
        """Get document by ID"""
        query = select(Document).where(
            Document.id == document_id,
            Document.organization_id == organization_id
        )

        if with_chunks:
            query = query.options(selectinload(Document.chunks))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_project(
        self,
        project_id: UUID,
        organization_id: UUID,
        skip: int = 0,
        limit: int = 20
    ) -> tuple[list[Document], int]:
        """Get documents by project ID with pagination"""
        # Get total count
        count_query = select(func.count(Document.id)).where(
            Document.project_id == project_id,
            Document.organization_id == organization_id
        )
        total = await self.db.scalar(count_query) or 0

        # Get paginated results
        query = (
            select(Document)
            .where(
                Document.project_id == project_id,
                Document.organization_id == organization_id
            )
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        documents = list(result.scalars().all())

        return documents, total

    async def update_status(
        self,
        document_id: UUID,
        status: str,
        error_message: str | None = None
    ) -> Document | None:
        """Update document status"""
        document = await self.db.get(Document, document_id)
        if document:
            document.status = status
            if error_message:
                document.error_message = error_message
            await self.db.commit()
            await self.db.refresh(document)
        return document

    async def delete(self, document_id: UUID, organization_id: UUID) -> bool:
        """Delete document"""
        result = await self.db.execute(
            delete(Document).where(
                Document.id == document_id,
                Document.organization_id == organization_id
            )
        )
        await self.db.commit()
        return result.rowcount > 0

    async def create_chunk(
        self,
        document_id: UUID,
        content: str,
        chunk_index: int,
        token_count: int,
        embedding: list[float]
    ) -> DocumentChunk:
        """Create a document chunk with embedding"""
        chunk = DocumentChunk(
            document_id=document_id,
            content=content,
            chunk_index=chunk_index,
            token_count=token_count,
            embedding=embedding
        )
        self.db.add(chunk)
        await self.db.commit()
        await self.db.refresh(chunk)
        return chunk

    async def vector_search(
        self,
        query_embedding: list[float],
        project_id: UUID,
        organization_id: UUID,
        limit: int = 5
    ) -> list[tuple[DocumentChunk, float]]:
        """
        Perform vector similarity search using cosine distance
        Returns chunks with their similarity scores
        """
        # Subquery to get document IDs for the project
        doc_ids_query = select(Document.id).where(
            Document.project_id == project_id,
            Document.organization_id == organization_id,
            Document.status == "completed"
        )

        # Vector similarity search using cosine distance
        # pgvector: <=> operator is cosine distance (lower is more similar)
        # Similarity = 1 - distance
        query = (
            select(
                DocumentChunk,
                (1 - DocumentChunk.embedding.cosine_distance(query_embedding)).label("similarity")
            )
            .where(DocumentChunk.document_id.in_(doc_ids_query))
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(limit)
        )

        result = await self.db.execute(query)
        return [(row[0], float(row[1])) for row in result.all()]
