from __future__ import annotations

"""Text chunking utilities"""
import logging
from typing import Any

import tiktoken

from ..config import settings

logger = logging.getLogger(__name__)


class TextChunker:
    """Utility for splitting text into chunks"""

    def __init__(
        self,
        chunk_size: int = settings.chunk_size,
        chunk_overlap: int = settings.chunk_overlap,
        encoding_name: str = "cl100k_base"  # GPT-4 encoding
    ):
        """
        Initialize text chunker

        Args:
            chunk_size: Maximum tokens per chunk
            chunk_overlap: Number of overlapping tokens between chunks
            encoding_name: Tiktoken encoding to use
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)

    def chunk_text(self, text: str) -> list[tuple[str, int]]:
        """
        Split text into chunks with overlap

        Args:
            text: Text to chunk

        Returns:
            List of tuples (chunk_text, token_count)
        """
        # Encode text to tokens
        tokens = self.encoding.encode(text)
        total_tokens = len(tokens)

        if total_tokens == 0:
            return []

        chunks: list[tuple[str, int]] = []
        start = 0

        while start < total_tokens:
            # Calculate end of chunk
            end = min(start + self.chunk_size, total_tokens)

            # Extract chunk tokens
            chunk_tokens = tokens[start:end]

            # Decode back to text
            chunk_text = self.encoding.decode(chunk_tokens)

            chunks.append((chunk_text, len(chunk_tokens)))

            # Move start position with overlap
            if end == total_tokens:
                break

            start = end - self.chunk_overlap

        logger.info(
            f"Chunked text: {total_tokens} tokens -> {len(chunks)} chunks "
            f"(size={self.chunk_size}, overlap={self.chunk_overlap})"
        )

        return chunks

    def count_tokens(self, text: str) -> int:
        """Count tokens in text"""
        return len(self.encoding.encode(text))


# Global chunker instance
_chunker: TextChunker | None = None


def get_chunker() -> TextChunker:
    """Get or create text chunker singleton"""
    global _chunker
    if _chunker is None:
        _chunker = TextChunker()
    return _chunker
