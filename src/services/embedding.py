"""Embedding service for semantic search.

Handles:
- Generating embeddings via Ollama
- Storing embeddings in pgvector
- Semantic similarity search
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import KBChunk
from src.services.ollama import OllamaClient, get_ollama_client, OllamaError

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Semantic search result."""
    id: int
    source: str
    chunk: str
    score: float  # Similarity score (0-1, higher is better)
    metadata: dict[str, Any] | None = None


class EmbeddingService:
    """Service for generating and searching embeddings.
    
    Usage:
        service = EmbeddingService(db_session)
        
        # Generate embedding
        vector = await service.embed_text("Hello world")
        
        # Search
        results = await service.search(tenant_id, "query", limit=5)
    """
    
    def __init__(
        self,
        db: AsyncSession,
        ollama: OllamaClient | None = None,
    ):
        self.db = db
        self.ollama = ollama or get_ollama_client()
    
    async def embed_text(self, text: str) -> list[float]:
        """Generate embedding vector for text.
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector (768 dimensions for nomic-embed-text)
        """
        return await self.ollama.embed(text)
    
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding vectors
        """
        return await self.ollama.embed_batch(texts)
    
    async def update_chunk_embedding(
        self,
        chunk_id: int,
        embedding: list[float],
    ) -> bool:
        """Update embedding for a KB chunk.
        
        Args:
            chunk_id: Chunk ID
            embedding: Embedding vector
        
        Returns:
            True if updated successfully
        """
        try:
            # Convert embedding to pgvector format
            embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
            
            # Use proper parameter binding
            stmt = text("""
                UPDATE kb_chunks 
                SET embedding_vector = cast(:embedding as vector)
                WHERE id = :chunk_id
            """).bindparams(
                embedding=embedding_str,
                chunk_id=chunk_id,
            )
            await self.db.execute(stmt)
            return True
        except Exception as e:
            logger.error(f"Failed to update embedding for chunk {chunk_id}: {e}")
            return False
    
    async def search_semantic(
        self,
        tenant_id: int,
        query: str,
        limit: int = 5,
        min_score: float = 0.3,
    ) -> list[SearchResult]:
        """Semantic search in knowledge base.
        
        Args:
            tenant_id: Tenant ID for data isolation
            query: Search query text
            limit: Maximum results to return
            min_score: Minimum similarity score (0-1)
        
        Returns:
            List of SearchResult ordered by relevance
        """
        # Generate query embedding
        try:
            query_embedding = await self.embed_text(query)
        except OllamaError as e:
            logger.warning(f"Failed to generate query embedding: {e}")
            # Fallback to text search
            return await self._text_search_fallback(tenant_id, query, limit)
        
        # Search using pgvector
        try:
            results = await self._pgvector_search(
                tenant_id, query_embedding, limit, min_score
            )
            if results:
                return results
        except Exception as e:
            logger.warning(f"pgvector search failed: {e}, falling back to text search")
            # Rollback the failed transaction to allow subsequent queries
            try:
                await self.db.rollback()
            except Exception as rollback_error:
                logger.warning(f"Rollback failed during error recovery: {rollback_error}")
        
        # Fallback to text search
        try:
            return await self._text_search_fallback(tenant_id, query, limit)
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}, falling back to text search")
            # Try one more rollback and retry
            try:
                await self.db.rollback()
                return await self._text_search_fallback(tenant_id, query, limit)
            except Exception as final_error:
                logger.error(f"All search methods failed: {final_error}", exc_info=True)
                return []
    
    async def _pgvector_search(
        self,
        tenant_id: int,
        embedding: list[float],
        limit: int,
        min_score: float,
    ) -> list[SearchResult]:
        """Search using pgvector cosine similarity.
        
        Note: cosine_distance returns distance (0 = identical, 2 = opposite)
        We convert to similarity score: score = 1 - (distance / 2)
        """
        # Convert embedding list to pgvector format string
        embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"
        
        # Use raw SQL with proper parameter binding for asyncpg
        # Note: SQLAlchemy text() with :param works, we need to bind the vector cast differently
        stmt = text("""
            SELECT 
                id,
                source,
                chunk,
                metadata_json,
                1 - (embedding_vector <=> cast(:embedding as vector)) / 2 as score
            FROM kb_chunks
            WHERE tenant_id = :tenant_id
              AND is_current = true
              AND embedding_vector IS NOT NULL
            ORDER BY embedding_vector <=> cast(:embedding as vector)
            LIMIT :limit
        """).bindparams(
            tenant_id=tenant_id,
            embedding=embedding_str,
            limit=limit * 2,
        )
        
        result = await self.db.execute(stmt)
        
        rows = result.fetchall()
        
        results = []
        for row in rows:
            score = float(row.score) if row.score else 0.0
            if score >= min_score:
                results.append(SearchResult(
                    id=row.id,
                    source=row.source,
                    chunk=row.chunk,
                    score=score,
                    metadata=row.metadata_json,
                ))
        
        return results[:limit]
    
    async def _text_search_fallback(
        self,
        tenant_id: int,
        query: str,
        limit: int,
    ) -> list[SearchResult]:
        """Fallback text search when embeddings unavailable."""
        # Ensure clean transaction
        try:
            await self.db.rollback()
        except Exception as rollback_error:
            logger.debug(f"Rollback during text search initialization: {rollback_error}")
        
        try:
            stmt = (
                select(KBChunk)
                .where(
                    and_(
                        KBChunk.tenant_id == tenant_id,
                        KBChunk.is_current == True,
                    )
                )
                .limit(100)
            )
            
            result = await self.db.execute(stmt)
            chunks = result.scalars().all()
        except Exception as e:
            logger.warning(f"Text search fallback also failed: {e}")
            return []
        
        # Simple word matching
        query_words = set(query.lower().split())
        
        scored_results = []
        for chunk in chunks:
            chunk_words = set(chunk.chunk.lower().split())
            common = query_words & chunk_words
            
            if common:
                # Score based on overlap ratio
                score = len(common) / max(len(query_words), 1)
                scored_results.append(SearchResult(
                    id=chunk.id,
                    source=chunk.source,
                    chunk=chunk.chunk,
                    score=min(score, 0.95),  # Cap at 0.95 for text search
                    metadata=chunk.metadata_json,
                ))
        
        # Sort by score
        scored_results.sort(key=lambda x: x.score, reverse=True)
        return scored_results[:limit]
    
    async def reindex_chunks(
        self,
        tenant_id: int,
        source: str | None = None,
        batch_size: int = 10,
    ) -> dict[str, int]:
        """Reindex embeddings for KB chunks.
        
        Args:
            tenant_id: Tenant ID
            source: Optional source filter
            batch_size: Batch size for embedding generation
        
        Returns:
            Dict with counts: processed, success, failed
        """
        # Get chunks to reindex
        stmt = select(KBChunk).where(
            and_(
                KBChunk.tenant_id == tenant_id,
                KBChunk.is_current == True,
            )
        )
        
        if source:
            stmt = stmt.where(KBChunk.source == source)
        
        result = await self.db.execute(stmt)
        chunks = result.scalars().all()
        
        processed = 0
        success = 0
        failed = 0
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            texts = [c.chunk for c in batch]
            
            try:
                embeddings = await self.embed_texts(texts)
                
                for chunk, embedding in zip(batch, embeddings):
                    processed += 1
                    if embedding:
                        updated = await self.update_chunk_embedding(
                            chunk.id, embedding
                        )
                        if updated:
                            success += 1
                        else:
                            failed += 1
                    else:
                        failed += 1
                        
            except Exception as e:
                logger.error(f"Batch embedding failed: {e}")
                failed += len(batch)
                processed += len(batch)
        
        await self.db.commit()
        
        return {
            "processed": processed,
            "success": success,
            "failed": failed,
        }


def get_embedding_service(db: AsyncSession) -> EmbeddingService:
    """Factory function for EmbeddingService."""
    return EmbeddingService(db)
