"""Vertex AI client for embeddings and LLM"""
import logging
from typing import Any

from google.cloud import aiplatform
from vertexai.language_models import TextEmbeddingInput, TextEmbeddingModel
from vertexai.generative_models import GenerativeModel

from ..config import settings

logger = logging.getLogger(__name__)


class VertexAIClient:
    """Client for Vertex AI services"""

    def __init__(self):
        """Initialize Vertex AI client"""
        aiplatform.init(
            project=settings.gcp_project_id,
            location=settings.gcp_location
        )
        self.embedding_model = TextEmbeddingModel.from_pretrained(
            settings.vertex_embedding_model
        )
        self.llm_model = GenerativeModel(settings.vertex_llm_model)

    async def generate_embeddings(
        self,
        texts: list[str],
        task_type: str = "RETRIEVAL_DOCUMENT"
    ) -> list[list[float]]:
        """
        Generate embeddings for a list of texts

        Args:
            texts: List of text strings to embed
            task_type: Type of embedding task (RETRIEVAL_DOCUMENT, RETRIEVAL_QUERY, etc.)

        Returns:
            List of embedding vectors
        """
        try:
            # Create TextEmbeddingInput objects
            inputs = [
                TextEmbeddingInput(text=text, task_type=task_type)
                for text in texts
            ]

            # Get embeddings in batches (max 5 per request for gecko)
            batch_size = 5
            all_embeddings: list[list[float]] = []

            for i in range(0, len(inputs), batch_size):
                batch = inputs[i:i + batch_size]
                embeddings = self.embedding_model.get_embeddings(batch)
                all_embeddings.extend([emb.values for emb in embeddings])

            logger.info(f"Generated {len(all_embeddings)} embeddings")
            return all_embeddings

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise

    async def generate_query_embedding(self, query: str) -> list[float]:
        """
        Generate embedding for a search query

        Args:
            query: Query text

        Returns:
            Embedding vector
        """
        embeddings = await self.generate_embeddings([query], task_type="RETRIEVAL_QUERY")
        return embeddings[0]

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        top_p: float = 0.95,
        top_k: int = 40
    ) -> str:
        """
        Generate text using Gemini LLM

        Args:
            prompt: Input prompt
            temperature: Controls randomness (0.0 to 1.0)
            max_output_tokens: Maximum tokens to generate
            top_p: Nucleus sampling threshold
            top_k: Top-k sampling parameter

        Returns:
            Generated text
        """
        try:
            response = self.llm_model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                    "top_p": top_p,
                    "top_k": top_k,
                }
            )
            return response.text

        except Exception as e:
            logger.error(f"Error generating text: {e}")
            raise

    async def generate_text_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 2048
    ) -> Any:
        """
        Generate text with streaming response

        Args:
            prompt: Input prompt
            temperature: Controls randomness
            max_output_tokens: Maximum tokens to generate

        Returns:
            Stream of text chunks
        """
        try:
            response = self.llm_model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                },
                stream=True
            )
            return response

        except Exception as e:
            logger.error(f"Error generating text stream: {e}")
            raise


# Global client instance
_vertex_client: VertexAIClient | None = None


def get_vertex_client() -> VertexAIClient:
    """Get or create Vertex AI client singleton"""
    global _vertex_client
    if _vertex_client is None:
        _vertex_client = VertexAIClient()
    return _vertex_client
