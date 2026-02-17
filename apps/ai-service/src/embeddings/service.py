from __future__ import annotations

"""Embedding generation service"""
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ..documents.repository import DocumentRepository
from .chunker import TextChunker, get_chunker
from .vertex_client import VertexAIClient, get_vertex_client

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and storing embeddings"""

    def __init__(
        self,
        vertex_client: VertexAIClient | None = None,
        chunker: TextChunker | None = None
    ):
        self.vertex_client = vertex_client or get_vertex_client()
        self.chunker = chunker or get_chunker()

    async def process_document(
        self,
        document_id: UUID,
        text: str,
        db: AsyncSession
    ) -> int:
        """
        Process document: chunk text and generate embeddings

        Args:
            document_id: ID of the document
            text: Full text content
            db: Database session

        Returns:
            Number of chunks created
        """
        repository = DocumentRepository(db)

        try:
            # Update document status to processing
            await repository.update_status(document_id, "processing")

            # Chunk the text
            chunks = self.chunker.chunk_text(text)

            if not chunks:
                await repository.update_status(
                    document_id,
                    "failed",
                    "No chunks generated from document"
                )
                return 0

            # Extract just the text for embedding
            chunk_texts = [chunk[0] for chunk in chunks]

            # Generate embeddings in batches
            embeddings = await self.vertex_client.generate_embeddings(chunk_texts)

            # Store chunks with embeddings
            for i, ((chunk_text, token_count), embedding) in enumerate(zip(chunks, embeddings)):
                await repository.create_chunk(
                    document_id=document_id,
                    content=chunk_text,
                    chunk_index=i,
                    token_count=token_count,
                    embedding=embedding
                )

            # Update document status to completed
            await repository.update_status(document_id, "completed")

            logger.info(f"Processed document {document_id}: {len(chunks)} chunks created")
            return len(chunks)

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            await repository.update_status(
                document_id,
                "failed",
                str(e)
            )
            raise

    async def embed_query(self, query: str) -> list[float]:
        """
        Generate embedding for a search query

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        return await self.vertex_client.generate_query_embedding(query)
