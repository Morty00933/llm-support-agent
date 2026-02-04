"""
Advanced RAG - Document Parser

Parses PDF, DOCX, TXT, MD files and chunks them for knowledge base.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, BinaryIO
import structlog

logger = structlog.get_logger(__name__)


class DocumentChunk:
    """Represents a chunk of document content."""

    def __init__(
        self,
        content: str,
        metadata: Dict[str, Any],
        page_number: int | None = None,
        section: str | None = None,
    ):
        self.content = content.strip()
        self.metadata = metadata
        self.page_number = page_number
        self.section = section

    def to_dict(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "metadata": self.metadata,
            "page_number": self.page_number,
            "section": self.section,
        }


class DocumentParser:
    """
    Parses various document formats and chunks them intelligently.

    Supported formats:
    - PDF (.pdf) - requires pypdf
    - DOCX (.docx) - requires python-docx
    - TXT (.txt) - plain text
    - MD (.md) - Markdown
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        min_chunk_size: int = 100,
    ):
        """
        Initialize document parser.

        Args:
            chunk_size: Target size for each chunk (characters)
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum chunk size to keep
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    async def parse_file(
        self,
        file: BinaryIO,
        filename: str,
        source: str = "upload",
    ) -> List[DocumentChunk]:
        """
        Parse a file and return chunks.

        Args:
            file: Binary file object
            filename: Original filename
            source: Source identifier

        Returns:
            List of DocumentChunk objects

        Raises:
            ValueError: If file format is not supported
        """
        suffix = Path(filename).suffix.lower()

        logger.info("parsing_document", filename=filename, format=suffix)

        if suffix == ".pdf":
            chunks = await self._parse_pdf(file, filename, source)
        elif suffix == ".docx":
            chunks = await self._parse_docx(file, filename, source)
        elif suffix in [".txt", ".md"]:
            chunks = await self._parse_text(file, filename, source)
        else:
            raise ValueError(f"Unsupported file format: {suffix}")

        logger.info("document_parsed", filename=filename, chunks=len(chunks))
        return chunks

    async def _parse_pdf(
        self,
        file: BinaryIO,
        filename: str,
        source: str,
    ) -> List[DocumentChunk]:
        """Parse PDF file."""
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ImportError(
                "pypdf is required for PDF parsing. "
                "Install with: pip install pypdf"
            )

        file.seek(0)
        reader = PdfReader(file)

        all_chunks = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            if not text or len(text.strip()) < self.min_chunk_size:
                continue

            # Clean text
            text = self._clean_text(text)

            # Create metadata
            metadata = {
                "source": source,
                "filename": filename,
                "format": "pdf",
                "total_pages": len(reader.pages),
            }

            # Chunk the page text
            page_chunks = self._chunk_text(
                text=text,
                metadata=metadata,
                page_number=page_num,
            )

            all_chunks.extend(page_chunks)

        return all_chunks

    async def _parse_docx(
        self,
        file: BinaryIO,
        filename: str,
        source: str,
    ) -> List[DocumentChunk]:
        """Parse DOCX file."""
        try:
            from docx import Document
        except ImportError:
            raise ImportError(
                "python-docx is required for DOCX parsing. "
                "Install with: pip install python-docx"
            )

        file.seek(0)
        doc = Document(file)

        # Extract all paragraphs
        full_text = []
        current_section = None

        for para in doc.paragraphs:
            text = para.text.strip()
            if not text:
                continue

            # Detect section headers (bold, large, etc.)
            if para.style.name.startswith("Heading"):
                current_section = text

            full_text.append(text)

        if not full_text:
            return []

        # Join all text
        combined_text = "\n\n".join(full_text)
        combined_text = self._clean_text(combined_text)

        # Create metadata
        metadata = {
            "source": source,
            "filename": filename,
            "format": "docx",
            "paragraphs": len(full_text),
        }

        # Chunk the document
        chunks = self._chunk_text(
            text=combined_text,
            metadata=metadata,
            section=current_section,
        )

        return chunks

    async def _parse_text(
        self,
        file: BinaryIO,
        filename: str,
        source: str,
    ) -> List[DocumentChunk]:
        """Parse plain text or markdown file."""
        file.seek(0)
        text = file.read().decode("utf-8", errors="ignore")

        if not text or len(text.strip()) < self.min_chunk_size:
            return []

        text = self._clean_text(text)

        suffix = Path(filename).suffix.lower()
        metadata = {
            "source": source,
            "filename": filename,
            "format": "markdown" if suffix == ".md" else "text",
        }

        chunks = self._chunk_text(text=text, metadata=metadata)
        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove multiple spaces
        text = re.sub(r"\s+", " ", text)

        # Remove excessive newlines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # Remove special characters that might cause issues
        text = text.replace("\x00", "")

        return text.strip()

    def _chunk_text(
        self,
        text: str,
        metadata: Dict[str, Any],
        page_number: int | None = None,
        section: str | None = None,
    ) -> List[DocumentChunk]:
        """
        Split text into overlapping chunks.

        Uses a sliding window approach with overlap to preserve context.
        """
        chunks = []

        # If text is smaller than chunk size, return as single chunk
        if len(text) <= self.chunk_size:
            chunk = DocumentChunk(
                content=text,
                metadata=metadata.copy(),
                page_number=page_number,
                section=section,
            )
            chunks.append(chunk)
            return chunks

        # Split into chunks with overlap
        start = 0
        while start < len(text):
            end = start + self.chunk_size

            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence end in the next 100 characters
                sentence_end = text.find(". ", end, end + 100)
                if sentence_end != -1:
                    end = sentence_end + 1

            chunk_text = text[start:end]

            # Only keep chunk if it's above minimum size
            if len(chunk_text.strip()) >= self.min_chunk_size:
                chunk = DocumentChunk(
                    content=chunk_text,
                    metadata=metadata.copy(),
                    page_number=page_number,
                    section=section,
                )
                chunks.append(chunk)

            # Move start position with overlap
            start = end - self.chunk_overlap

            # Avoid infinite loop
            if end >= len(text):
                break

        return chunks

    def _detect_sections(self, text: str) -> List[tuple[str, str]]:
        """
        Detect sections in document based on headers.

        Returns:
            List of (section_name, section_text) tuples
        """
        sections = []

        # Simple heuristic: lines that are all caps or start with #
        lines = text.split("\n")
        current_section = "Introduction"
        current_text = []

        for line in lines:
            line = line.strip()

            # Markdown header
            if line.startswith("#"):
                if current_text:
                    sections.append((current_section, "\n".join(current_text)))
                    current_text = []
                current_section = line.lstrip("#").strip()

            # All caps line (potential header)
            elif line.isupper() and len(line) > 3 and len(line) < 100:
                if current_text:
                    sections.append((current_section, "\n".join(current_text)))
                    current_text = []
                current_section = line

            else:
                if line:  # Skip empty lines
                    current_text.append(line)

        # Add last section
        if current_text:
            sections.append((current_section, "\n".join(current_text)))

        return sections


class RAGOptimizer:
    """Optimizes chunks for RAG retrieval."""

    @staticmethod
    def add_context_to_chunks(chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """
        Add contextual information to chunks for better retrieval.

        For each chunk, prepends section/page information.
        """
        enhanced_chunks = []

        for chunk in chunks:
            context_prefix = []

            # Add filename context
            if "filename" in chunk.metadata:
                context_prefix.append(f"Document: {chunk.metadata['filename']}")

            # Add section context
            if chunk.section:
                context_prefix.append(f"Section: {chunk.section}")

            # Add page context
            if chunk.page_number:
                context_prefix.append(f"Page: {chunk.page_number}")

            if context_prefix:
                prefix = " | ".join(context_prefix)
                enhanced_content = f"[{prefix}]\n\n{chunk.content}"
            else:
                enhanced_content = chunk.content

            enhanced_chunk = DocumentChunk(
                content=enhanced_content,
                metadata=chunk.metadata,
                page_number=chunk.page_number,
                section=chunk.section,
            )
            enhanced_chunks.append(enhanced_chunk)

        return enhanced_chunks

    @staticmethod
    def deduplicate_chunks(chunks: List[DocumentChunk], threshold: float = 0.9) -> List[DocumentChunk]:
        """
        Remove duplicate or very similar chunks.

        Args:
            chunks: List of chunks
            threshold: Similarity threshold (0-1), higher means more strict

        Returns:
            Deduplicated list of chunks
        """
        if not chunks:
            return []

        unique_chunks = [chunks[0]]

        for chunk in chunks[1:]:
            is_duplicate = False

            for existing in unique_chunks:
                # Simple similarity: ratio of common words
                words1 = set(chunk.content.lower().split())
                words2 = set(existing.content.lower().split())

                if not words1 or not words2:
                    continue

                intersection = len(words1 & words2)
                union = len(words1 | words2)

                similarity = intersection / union if union > 0 else 0

                if similarity >= threshold:
                    is_duplicate = True
                    break

            if not is_duplicate:
                unique_chunks.append(chunk)

        return unique_chunks
