"""Unit tests for TextChunker."""
from __future__ import annotations

import pytest

from src.embeddings.chunker import TextChunker


@pytest.fixture
def chunker() -> TextChunker:
    """Default chunker with small sizes for testing."""
    return TextChunker(chunk_size=100, chunk_overlap=20)


@pytest.fixture
def short_text() -> str:
    return "Hello world. This is a short test text."


@pytest.fixture
def long_text() -> str:
    # ~300 tokens of text
    return " ".join([f"word{i}" for i in range(300)])


class TestChunkText:
    def test_empty_text_returns_empty_list(self, chunker: TextChunker) -> None:
        result = chunker.chunk_text("")
        assert result == []

    def test_short_text_returns_single_chunk(self, chunker: TextChunker, short_text: str) -> None:
        result = chunker.chunk_text(short_text)
        assert len(result) == 1
        chunk_text, token_count = result[0]
        assert short_text in chunk_text or chunk_text in short_text
        assert token_count > 0

    def test_long_text_returns_multiple_chunks(self, chunker: TextChunker, long_text: str) -> None:
        result = chunker.chunk_text(long_text)
        assert len(result) > 1

    def test_chunks_have_correct_format(self, chunker: TextChunker, long_text: str) -> None:
        result = chunker.chunk_text(long_text)
        for chunk_text, token_count in result:
            assert isinstance(chunk_text, str)
            assert isinstance(token_count, int)
            assert token_count > 0
            assert len(chunk_text) > 0

    def test_chunk_size_respected(self, chunker: TextChunker, long_text: str) -> None:
        result = chunker.chunk_text(long_text)
        for _, token_count in result:
            assert token_count <= chunker.chunk_size

    def test_overlap_creates_continuity(self, chunker: TextChunker) -> None:
        """Chunks should overlap - end of chunk N should appear in start of chunk N+1."""
        text = " ".join([f"token{i}" for i in range(250)])
        result = chunker.chunk_text(text)
        assert len(result) >= 2

        # The overlap means chunks should share tokens
        chunk1_text = result[0][0]
        chunk2_text = result[1][0]

        # Last few words of chunk1 should appear at start of chunk2
        chunk1_words = chunk1_text.split()[-5:]
        chunk2_start = chunk2_text[:100]
        overlap_found = any(word in chunk2_start for word in chunk1_words)
        assert overlap_found, "Overlap not found between consecutive chunks"

    def test_all_content_covered(self, chunker: TextChunker) -> None:
        """All tokens should appear in at least one chunk."""
        words = [f"unique_word_{i}" for i in range(50)]
        text = " ".join(words)
        result = chunker.chunk_text(text)

        all_chunks_text = " ".join(chunk for chunk, _ in result)
        # Each unique word should appear in the combined chunks
        for word in words:
            assert word in all_chunks_text

    def test_whitespace_only_text(self, chunker: TextChunker) -> None:
        result = chunker.chunk_text("   \n\t  ")
        # Whitespace-only may produce no meaningful tokens
        assert isinstance(result, list)

    def test_single_word(self, chunker: TextChunker) -> None:
        result = chunker.chunk_text("hello")
        assert len(result) == 1
        assert result[0][1] > 0


class TestCountTokens:
    def test_empty_string(self, chunker: TextChunker) -> None:
        assert chunker.count_tokens("") == 0

    def test_single_word(self, chunker: TextChunker) -> None:
        count = chunker.count_tokens("hello")
        assert count == 1

    def test_sentence(self, chunker: TextChunker) -> None:
        count = chunker.count_tokens("Hello, world!")
        assert count > 0

    def test_longer_text_more_tokens(self, chunker: TextChunker) -> None:
        short_count = chunker.count_tokens("hello world")
        long_count = chunker.count_tokens("hello world this is a longer sentence with more words")
        assert long_count > short_count

    def test_consistency_with_chunking(self, chunker: TextChunker) -> None:
        """Token count should match what chunking produces."""
        text = "This is a test sentence for consistency checking."
        total_tokens = chunker.count_tokens(text)
        chunks = chunker.chunk_text(text)
        # Single chunk for short text - token count should match
        if chunks:
            _, chunk_tokens = chunks[0]
            assert chunk_tokens == total_tokens


class TestChunkerConfig:
    def test_custom_chunk_size(self) -> None:
        chunker = TextChunker(chunk_size=50, chunk_overlap=10)
        assert chunker.chunk_size == 50
        assert chunker.chunk_overlap == 10

    def test_no_overlap_chunker(self) -> None:
        chunker = TextChunker(chunk_size=50, chunk_overlap=0)
        text = " ".join([f"word{i}" for i in range(200)])
        result = chunker.chunk_text(text)
        assert len(result) > 1
        # With no overlap, chunks should not share content (except at exact boundaries)
        for _, token_count in result:
            assert token_count <= chunker.chunk_size
