from __future__ import annotations

"""Vertex AI client for embeddings and LLM"""
import logging
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)


class VertexAIClient:
    """Client for Vertex AI services.

    All initialisation is deferred until the first actual API call so that
    importing this module (and constructing the singleton) never blocks or
    raises when GCP credentials are absent.
    """

    def __init__(self) -> None:
        self._initialized: bool = False
        self._embedding_model: Any = None
        self._llm_model: Any = None

    def _ensure_initialized(self) -> None:
        """Lazily initialise the Vertex AI SDK on first use."""
        if self._initialized:
            return

        try:
            from google.cloud import aiplatform
            from vertexai.generative_models import GenerativeModel  # noqa: F401 (import check)
            from vertexai.language_models import TextEmbeddingModel  # noqa: F401

            aiplatform.init(
                project=settings.gcp_project_id,
                location=settings.gcp_location,
            )
            self._initialized = True
            logger.info("Vertex AI SDK initialised (project=%s, location=%s)",
                        settings.gcp_project_id, settings.gcp_location)
        except Exception as exc:
            logger.warning("Vertex AI initialisation failed (credentials missing?): %s", exc)
            raise

    @property
    def embedding_model(self) -> Any:
        if self._embedding_model is None:
            self._ensure_initialized()
            from vertexai.language_models import TextEmbeddingModel
            self._embedding_model = TextEmbeddingModel.from_pretrained(
                settings.vertex_embedding_model
            )
        return self._embedding_model

    @property
    def llm_model(self) -> Any:
        if self._llm_model is None:
            self._ensure_initialized()
            from vertexai.generative_models import GenerativeModel
            self._llm_model = GenerativeModel(settings.vertex_llm_model)
        return self._llm_model

    async def generate_embeddings(
        self,
        texts: list[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
    ) -> list[list[float]]:
        """Generate embeddings for a list of texts."""
        from vertexai.language_models import TextEmbeddingInput

        inputs = [
            TextEmbeddingInput(text=text, task_type=task_type)
            for text in texts
        ]

        batch_size = 5
        all_embeddings: list[list[float]] = []

        for i in range(0, len(inputs), batch_size):
            batch = inputs[i:i + batch_size]
            embeddings = self.embedding_model.get_embeddings(batch)
            all_embeddings.extend([emb.values for emb in embeddings])

        logger.info("Generated %d embeddings", len(all_embeddings))
        return all_embeddings

    async def generate_query_embedding(self, query: str) -> list[float]:
        """Generate embedding for a search query."""
        embeddings = await self.generate_embeddings([query], task_type="RETRIEVAL_QUERY")
        return embeddings[0]

    async def generate_text(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
        top_p: float = 0.95,
        top_k: int = 40,
    ) -> str:
        """Generate text using Gemini LLM."""
        response = self.llm_model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
                "top_p": top_p,
                "top_k": top_k,
            },
        )
        return response.text

    async def generate_text_stream(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_output_tokens: int = 2048,
    ) -> Any:
        """Generate text with streaming response."""
        response = self.llm_model.generate_content(
            prompt,
            generation_config={
                "temperature": temperature,
                "max_output_tokens": max_output_tokens,
            },
            stream=True,
        )
        return response


# ---------------------------------------------------------------------------
# Module-level singleton — constructed cheaply (no network I/O at import time)
# ---------------------------------------------------------------------------
_vertex_client: VertexAIClient | None = None


def get_vertex_client() -> VertexAIClient:
    """Return the shared VertexAIClient singleton."""
    global _vertex_client
    if _vertex_client is None:
        _vertex_client = VertexAIClient()
    return _vertex_client
