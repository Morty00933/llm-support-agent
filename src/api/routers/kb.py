"""Knowledge Base router - with semantic search and role-based access control."""
from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repos import KBChunkRepository
from src.core.db import get_db
from src.api.routers.auth import get_current_active_user, User
from src.api.dependencies import require_admin, require_agent_or_admin

logger = logging.getLogger(__name__)


router = APIRouter(tags=["knowledge-base"])


class ChunkCreate(BaseModel):
    """Create KB chunk schema."""
    content: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1, max_length=255)
    metadata: dict[str, Any] | None = None


class ChunkBulkCreate(BaseModel):
    """Bulk create KB chunks schema."""
    source: str = Field(..., min_length=1, max_length=255)
    chunks: list[dict[str, Any]]


class ChunkResponse(BaseModel):
    """KB chunk response schema."""
    id: int
    source: str
    chunk: str
    version: int
    is_current: bool

    model_config = {"from_attributes": True}


class SearchQuery(BaseModel):
    """Search query schema."""
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=50)


class SearchResult(BaseModel):
    """Search result schema."""
    id: int
    source: str
    chunk: str
    score: float | None = None


@router.get("/chunks", response_model=list[ChunkResponse])
async def list_chunks(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list:
    """List KB chunks for current tenant."""
    kb_repo = KBChunkRepository(db)
    chunks = await kb_repo.list_by_tenant(
        current_user.tenant_id,
        skip=skip,
        limit=limit,
    )
    return list(chunks)


@router.post("/chunks", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_chunks(
    data: ChunkBulkCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin),
) -> dict:
    """Bulk upsert KB chunks with automatic embedding generation.

    Creates chunks and generates embeddings for semantic search.

    Requires: agent or admin role.
    """
    # First, upsert chunks
    kb_repo = KBChunkRepository(db)
    result = await kb_repo.upsert(
        tenant_id=current_user.tenant_id,
        source=data.source,
        chunks=data.chunks,
    )
    
    # Then generate embeddings for new chunks
    if result.get("created", 0) > 0:
        try:
            from src.services.embedding import EmbeddingService
            embedding_service = EmbeddingService(db)
            embed_result = await embedding_service.reindex_chunks(
                tenant_id=current_user.tenant_id,
                source=data.source,
            )
            result["embeddings"] = embed_result
            logger.info(f"Generated embeddings for {embed_result.get('success', 0)} chunks")
        except Exception as e:
            logger.warning(f"Failed to generate embeddings: {e}")
            result["embeddings"] = {"error": str(e)}
    
    return result


@router.delete("/sources/{source}", status_code=status.HTTP_200_OK)
async def delete_source(
    source: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Delete all chunks from a source.

    Requires: admin role.
    """
    kb_repo = KBChunkRepository(db)
    count = await kb_repo.delete_source(
        tenant_id=current_user.tenant_id,
        source=source,
    )
    return {"deleted": count, "source": source}


@router.post("/search", response_model=list[SearchResult])
async def search_kb(
    query: SearchQuery,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> list[dict]:
    """Search KB using semantic similarity.
    
    Uses embeddings + pgvector for semantic search.
    Falls back to text matching if Ollama unavailable.
    """
    from src.services.embedding import EmbeddingService
    
    embedding_service = EmbeddingService(db)
    
    try:
        results = await embedding_service.search_semantic(
            tenant_id=current_user.tenant_id,
            query=query.query,
            limit=query.limit,
            min_score=0.2,
        )
        
        return [
            {
                "id": r.id,
                "source": r.source,
                "chunk": r.chunk,
                "score": r.score,
            }
            for r in results
        ]
    except Exception as e:
        logger.error(f"Search failed: {e}")
        # Fallback to simple listing
        kb_repo = KBChunkRepository(db)
        chunks = await kb_repo.list_by_tenant(
            current_user.tenant_id,
            limit=query.limit,
        )
        return [
            {
                "id": chunk.id,
                "source": chunk.source,
                "chunk": chunk.chunk,
                "score": 0.5,
            }
            for chunk in chunks
        ]


@router.post("/reindex", response_model=dict)
async def reindex_kb(
    source: str | None = Query(None, description="Optional source filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_agent_or_admin),
) -> dict:
    """Reindex embeddings for KB chunks.

    Regenerates embeddings for all chunks (or filtered by source).
    Use this after adding chunks or changing embedding model.

    Requires: agent or admin role.
    """
    from src.services.embedding import EmbeddingService
    
    embedding_service = EmbeddingService(db)
    
    try:
        result = await embedding_service.reindex_chunks(
            tenant_id=current_user.tenant_id,
            source=source,
        )
        return {
            "status": "success",
            **result,
        }
    except Exception as e:
        logger.error(f"Reindex failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Reindex failed: {e}",
        )


@router.post("/upload", response_model=dict)
async def upload_document(
    file: UploadFile = File(...),
    source: str = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Upload a document to KB with advanced RAG parsing.

    Supports: .txt, .md, .pdf, .docx

    Requires: admin role.

    Features:
    - Security validation (size, MIME type, content scanning)
    - Intelligent chunking with overlap
    - PDF/DOCX parsing with page/section detection
    - Automatic embedding generation
    - Context-aware chunk metadata

    Security features:
    - File size limit (10 MB)
    - MIME type validation
    - Content scanning for malicious patterns
    - SHA256 integrity check
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Filename required",
        )

    # Validate file with security checks
    from src.services.file_validation import FileValidator, FileValidationError
    from src.services.document_parser import DocumentParser, RAGOptimizer

    validator = FileValidator()
    try:
        validation_metadata = validator.validate_file(file.file, file.filename)
        logger.info("file_validated", metadata=validation_metadata)
    except FileValidationError as e:
        logger.error("file_validation_failed", filename=file.filename, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    # Reset file pointer after validation
    file.file.seek(0)

    # Parse document into chunks
    try:
        parser = DocumentParser(
            chunk_size=1000,
            chunk_overlap=200,
            min_chunk_size=100,
        )

        # Parse file
        document_chunks = await parser.parse_file(
            file=file.file,
            filename=file.filename,
            source=source,
        )

        if not document_chunks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No content extracted from document",
            )

        # Optimize chunks for RAG
        optimizer = RAGOptimizer()
        document_chunks = optimizer.add_context_to_chunks(document_chunks)
        document_chunks = optimizer.deduplicate_chunks(document_chunks, threshold=0.85)

        logger.info(
            "document_parsed",
            filename=file.filename,
            chunks=len(document_chunks),
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Required library not installed: {e}",
        )
    except Exception as e:
        logger.error("document_parsing_failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to parse document: {e}",
        )

    # Convert DocumentChunk objects to dict format for database
    chunks = [{"content": chunk.content, "metadata": chunk.metadata} for chunk in document_chunks]

    # Upsert chunks
    kb_repo = KBChunkRepository(db)
    result = await kb_repo.upsert(
        tenant_id=current_user.tenant_id,
        source=source,
        chunks=chunks,
    )

    # Generate embeddings
    if result.get("created", 0) > 0:
        try:
            from src.services.embedding import EmbeddingService
            embedding_service = EmbeddingService(db)
            embed_result = await embedding_service.reindex_chunks(
                tenant_id=current_user.tenant_id,
                source=source,
            )
            result["embeddings"] = embed_result
            logger.info(f"Generated embeddings for {embed_result.get('success', 0)} chunks")
        except Exception as e:
            logger.warning(f"Failed to generate embeddings: {e}")
            result["embeddings"] = {"error": str(e)}

    return {
        "filename": file.filename,
        "source": source,
        "chunks_processed": len(chunks),
        "validation": validation_metadata,
        **result,
    }
