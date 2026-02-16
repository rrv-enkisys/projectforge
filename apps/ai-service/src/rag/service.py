"""RAG service for question answering"""
import logging
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import settings
from ..database import get_db
from ..documents.repository import DocumentRepository
from ..embeddings.service import EmbeddingService
from ..embeddings.vertex_client import VertexAIClient, get_vertex_client
from .prompts import build_rag_prompt

logger = logging.getLogger(__name__)


class RAGService:
    """Service for RAG-based question answering"""

    def __init__(
        self,
        db: AsyncSession = Depends(get_db),
        vertex_client: VertexAIClient = Depends(get_vertex_client)
    ):
        self.db = db
        self.vertex_client = vertex_client
        self.embedding_service = EmbeddingService(vertex_client)
        self.document_repository = DocumentRepository(db)

    async def query(
        self,
        question: str,
        project_id: UUID,
        organization_id: UUID,
        max_chunks: int = settings.max_chunks_per_query
    ) -> dict:
        """
        Answer a question using RAG

        Args:
            question: User's question
            project_id: Project context
            organization_id: Organization context
            max_chunks: Maximum number of chunks to retrieve

        Returns:
            Dictionary with answer and source chunks
        """
        try:
            # 1. Generate embedding for the question
            query_embedding = await self.embedding_service.embed_query(question)

            # 2. Retrieve relevant chunks via vector similarity search
            chunks_with_scores = await self.document_repository.vector_search(
                query_embedding=query_embedding,
                project_id=project_id,
                organization_id=organization_id,
                limit=max_chunks
            )

            if not chunks_with_scores:
                return {
                    "answer": "I couldn't find any relevant information in the project documents to answer your question.",
                    "sources": [],
                    "confidence": "low"
                }

            # 3. Build context from retrieved chunks
            context_chunks = [
                (chunk.content, score)
                for chunk, score in chunks_with_scores
            ]

            # 4. Build RAG prompt
            prompt = build_rag_prompt(question, context_chunks)

            # 5. Generate answer using LLM
            answer = await self.vertex_client.generate_text(
                prompt=prompt,
                temperature=0.3,  # Lower temperature for more factual answers
                max_output_tokens=1024
            )

            # 6. Prepare source information
            sources = [
                {
                    "document_id": str(chunk.document_id),
                    "chunk_id": str(chunk.id),
                    "content": chunk.content[:200] + "..." if len(chunk.content) > 200 else chunk.content,
                    "similarity": float(score),
                    "chunk_index": chunk.chunk_index
                }
                for chunk, score in chunks_with_scores
            ]

            # Determine confidence based on top similarity score
            top_score = chunks_with_scores[0][1] if chunks_with_scores else 0
            confidence = "high" if top_score > 0.8 else "medium" if top_score > 0.6 else "low"

            logger.info(
                f"RAG query answered: {len(chunks_with_scores)} chunks retrieved, "
                f"confidence={confidence}"
            )

            return {
                "answer": answer,
                "sources": sources,
                "confidence": confidence,
                "chunks_retrieved": len(chunks_with_scores)
            }

        except Exception as e:
            logger.error(f"Error in RAG query: {e}")
            raise

    async def stream_query(
        self,
        question: str,
        project_id: UUID,
        organization_id: UUID,
        max_chunks: int = settings.max_chunks_per_query
    ):
        """
        Answer a question using RAG with streaming response

        Args:
            question: User's question
            project_id: Project context
            organization_id: Organization context
            max_chunks: Maximum number of chunks to retrieve

        Yields:
            Text chunks as they are generated
        """
        # 1. Generate embedding for the question
        query_embedding = await self.embedding_service.embed_query(question)

        # 2. Retrieve relevant chunks
        chunks_with_scores = await self.document_repository.vector_search(
            query_embedding=query_embedding,
            project_id=project_id,
            organization_id=organization_id,
            limit=max_chunks
        )

        if not chunks_with_scores:
            yield "I couldn't find any relevant information in the project documents."
            return

        # 3. Build prompt
        context_chunks = [
            (chunk.content, score)
            for chunk, score in chunks_with_scores
        ]
        prompt = build_rag_prompt(question, context_chunks)

        # 4. Stream answer
        response_stream = await self.vertex_client.generate_text_stream(
            prompt=prompt,
            temperature=0.3,
            max_output_tokens=1024
        )

        for chunk in response_stream:
            yield chunk.text
