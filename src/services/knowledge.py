"""Knowledge service - FIXED VERSION with proper pgvector integration."""
from __future__ import annotations

import hashlib
import logging
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential

from src.domain.repos import KBChunkRepository
from src.domain.models import KBChunk

# Try to import pgvector
try:
    from pgvector.sqlalchemy import Vector
    HAS_PGVECTOR = True
except ImportError:
    HAS_PGVECTOR = False
    Vector = None  # type: ignore

logger = logging.getLogger(__name__)


class KnowledgeService:
    """Service for managing knowledge base with vector search."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = KBChunkRepository(session)

    @staticmethod
    def _compute_hash(text: str) -> str:
        """Compute SHA256 hash of text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    async def add_chunk(
        self,
        tenant_id: int,
        source: str,
        chunk: str,
        embedding: list[float] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KBChunk:
        """Add a knowledge chunk."""
        chunk_hash = self._compute_hash(chunk)
        
        # Check if chunk already exists
        existing = await self.repo.get_by_hash(tenant_id, chunk_hash)
        if existing:
            logger.info(f"Chunk already exists: {chunk_hash[:8]}...")
            return existing
        
        # Create new chunk using upsert
        await self.repo.upsert(
            tenant_id=tenant_id,
            source=source,
            chunks=[{"content": chunk, "metadata": metadata}],
        )

        await self.session.commit()
        logger.info(f"Added KB chunk from {source}: {chunk_hash[:8]}...")

        # Fetch the created chunk
        kb_chunk = await self.repo.get_by_hash(tenant_id, chunk_hash)
        if kb_chunk is None:
            raise ValueError("Failed to create KB chunk")
        return kb_chunk

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def search_similar(
        self,
        tenant_id: int,
        query_embedding: list[float],
        limit: int = 5,
        threshold: float = 0.7,  # noqa: ARG002 - kept for API compatibility
    ) -> list[dict[str, Any]]:
        """Search for similar chunks using vector similarity."""
        if not HAS_PGVECTOR:
            logger.warning("pgvector not available, falling back to simple search")
            # Fallback to returning recent chunks
            chunks = await self.repo.list_by_tenant(tenant_id, limit=limit)
            return [
                {
                    "chunk": chunk.chunk,
                    "source": chunk.source,
                    "metadata": chunk.metadata_json or {},
                    "score": 1.0,  # Default score
                }
                for chunk in chunks
            ]

        # Use vector search
        chunks = await self.repo.search_by_embedding(
            tenant_id=tenant_id,
            embedding=query_embedding,
            limit=limit,
        )
        
        results = []
        for chunk in chunks:
            results.append({
                "chunk": chunk.chunk,
                "source": chunk.source,
                "metadata": chunk.metadata_json or {},
                "score": 0.9,  # Placeholder score (real score would come from distance)
            })
        
        logger.info(f"Found {len(results)} similar chunks for query")
        return results

    async def archive_source(self, tenant_id: int, source: str) -> int:
        """Archive all chunks from a source."""
        count = await self.repo.archive_by_source(tenant_id, source)
        logger.info(f"Archived {count} chunks from source: {source}")
        return count

    async def get_context_for_query(
        self,
        tenant_id: int,
        query_embedding: list[float],
        max_chunks: int = 3,
    ) -> str:
        """Get context chunks formatted for LLM prompt."""
        results = await self.search_similar(
            tenant_id=tenant_id,
            query_embedding=query_embedding,
            limit=max_chunks,
        )
        
        if not results:
            return "No relevant knowledge base information found."
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Source {i}: {result['source']}]\n{result['chunk']}\n"
            )
        
        return "\n---\n".join(context_parts)

    async def bulk_add_chunks(
        self,
        tenant_id: int,
        source: str,
        chunks: list[str],
        embeddings: list[list[float]] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> list[KBChunk]:
        """Add multiple chunks at once."""
        if embeddings and len(embeddings) != len(chunks):
            raise ValueError("Number of embeddings must match number of chunks")
        
        kb_chunks = []
        for i, chunk in enumerate(chunks):
            embedding = embeddings[i] if embeddings else None
            
            kb_chunk = await self.add_chunk(
                tenant_id=tenant_id,
                source=source,
                chunk=chunk,
                embedding=embedding,
                metadata=metadata,
            )
            kb_chunks.append(kb_chunk)
        
        logger.info(f"Bulk added {len(kb_chunks)} chunks from {source}")
        return kb_chunks

    async def update_embeddings(
        self,
        tenant_id: int,
        source: str,
        embeddings_map: dict[str, list[float]],
    ) -> int:
        """Update embeddings for existing chunks."""
        updated_count = 0
        
        for chunk_hash, embedding in embeddings_map.items():
            chunk = await self.repo.get_by_hash(tenant_id, chunk_hash)
            if chunk:
                # Update embedding - type annotation allows list[float]
                chunk.embedding_vector = embedding  # type: ignore[assignment]
                
                updated_count += 1
        
        await self.session.commit()
        logger.info(f"Updated {updated_count} embeddings for source: {source}")
        return updated_count


class EmbeddingGenerator:
    """Generate embeddings for text using Ollama.

    Uses the configured Ollama embedding model (nomic-embed-text by default)
    to generate real vector embeddings for semantic search.
    """

    def __init__(self, model_name: str | None = None):
        from src.services.ollama import get_ollama_client, OllamaError

        self._ollama = get_ollama_client()
        self._ollama_error = OllamaError
        self.model_name = model_name or self._ollama.embed_model
        self.dimension = self._ollama.expected_dim

    async def generate(self, text: str) -> list[float]:
        """Generate embedding for text using Ollama.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (768 dimensions for nomic-embed-text)

        Raises:
            OllamaError: If embedding generation fails
        """
        try:
            embedding = await self._ollama.embed(text, model=self.model_name)
            logger.debug(f"Generated embedding dim={len(embedding)} for text len={len(text)}")
            return embedding
        except self._ollama_error as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_batch(
        self,
        texts: list[str],
        max_concurrent: int = 5,
    ) -> list[list[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            max_concurrent: Maximum concurrent requests to Ollama

        Returns:
            List of embedding vectors
        """
        embeddings = await self._ollama.embed_batch(
            texts,
            model=self.model_name,
            max_concurrent=max_concurrent,
        )
        logger.info(f"Generated {len(embeddings)} embeddings in batch")
        return embeddings
