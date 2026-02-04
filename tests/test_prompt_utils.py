"""
Tests for prompt formatting utilities
"""
from src.utils.prompt import (
    format_kb_chunk,
    format_kb_context,
)


class TestFormatKBChunk:
    """Tests for format_kb_chunk function"""

    def test_format_kb_chunk_from_dict(self):
        """Test formatting KB chunk from dict"""
        chunk = {
            "chunk": "Test content",
            "source": "test.md",
            "score": 0.85,
        }
        result = format_kb_chunk(chunk, 1)
        assert "[1]" in result
        assert "test.md" in result
        assert "0.85" in result
        assert "Test content" in result

    def test_format_kb_chunk_without_score(self):
        """Test formatting KB chunk without score"""
        chunk = {
            "chunk": "Test content",
            "source": "test.md",
            "score": 0.85,
        }
        result = format_kb_chunk(chunk, 1, include_score=False)
        assert "[1]" in result
        assert "test.md" in result
        assert "0.85" not in result
        assert "relevance" not in result

    def test_format_kb_chunk_custom_index(self):
        """Test formatting with custom index"""
        chunk = {
            "chunk": "Content",
            "source": "doc.md",
            "score": 0.9,
        }
        result = format_kb_chunk(chunk, 5)
        assert "[5]" in result

    def test_format_kb_chunk_missing_fields(self):
        """Test formatting chunk with missing fields"""
        chunk = {"chunk": "Content only"}
        result = format_kb_chunk(chunk, 1)
        assert "Content only" in result
        assert "Unknown" in result  # Default source


class TestFormatKBContext:
    """Tests for format_kb_context function"""

    def test_format_empty_chunks(self):
        """Test formatting empty chunks list"""
        result = format_kb_context([])
        assert result == ""

    def test_format_single_chunk(self):
        """Test formatting single chunk"""
        chunks = [
            {"chunk": "Test content", "source": "test.md", "score": 0.9}
        ]
        result = format_kb_context(chunks)
        assert "[1]" in result
        assert "Test content" in result

    def test_format_multiple_chunks(self):
        """Test formatting multiple chunks"""
        chunks = [
            {"chunk": "Content 1", "source": "a.md", "score": 0.9},
            {"chunk": "Content 2", "source": "b.md", "score": 0.8},
        ]
        result = format_kb_context(chunks)
        assert "[1]" in result
        assert "[2]" in result
        assert "Content 1" in result
        assert "Content 2" in result

    def test_format_with_max_chunks(self):
        """Test formatting with max_chunks limit"""
        chunks = [
            {"chunk": f"Content {i}", "source": f"{i}.md", "score": 0.9}
            for i in range(10)
        ]
        result = format_kb_context(chunks, max_chunks=3)
        assert "[1]" in result
        assert "[2]" in result
        assert "[3]" in result
        assert "[4]" not in result

    def test_format_without_score(self):
        """Test formatting without scores"""
        chunks = [
            {"chunk": "Content", "source": "test.md", "score": 0.9}
        ]
        result = format_kb_context(chunks, include_score=False)
        assert "0.9" not in result
        assert "relevance" not in result

    def test_format_with_custom_separator(self):
        """Test formatting with custom separator"""
        chunks = [
            {"chunk": "Content 1", "source": "a.md", "score": 0.9},
            {"chunk": "Content 2", "source": "b.md", "score": 0.8},
        ]
        result = format_kb_context(chunks, separator="\n---\n")
        assert "\n---\n" in result
