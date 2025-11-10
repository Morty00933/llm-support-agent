"""Сервисы работы с базой знаний (upsert + поиск)."""

from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime, timezone
import logging
from typing import Any, Sequence

from sqlalchemy import func, select, delete, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..domain.models import KBChunk, HAS_PGVECTOR
from ..schemas.kb import (
    KBUpsert,
    KBSearchIn,
    KBChunkIn,
    KBArchiveIn,
    KBDeleteIn,
    KBReindexIn,
)
from .embeddings import embed_texts, EmbeddingServiceError
from .search import cosine_similarity_bytes


logger = logging.getLogger(__name__)


class KnowledgeBaseError(Exception):
    """Доменные ошибки работы с базой знаний."""

    def __init__(self, message: str, *, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


def _guess_language(text: str) -> str:
    if re.search(r"[А-Яа-яЁё]", text):
        return "ru"
    if re.search(r"[A-Za-z]", text):
        return "en"
    return "unknown"


def _normalize_tags(tags: list[str] | None) -> list[str] | None:
    if not tags:
        return None
    normalized = sorted({t.strip().lower() for t in tags if t.strip()})
    return normalized or None


def _build_metadata(chunk: str, payload: dict[str, Any]) -> dict[str, Any]:
    meta = {k: v for k, v in payload.items() if v is not None}
    meta["char_count"] = len(chunk)
    meta["word_count"] = len(chunk.split())
    meta.setdefault("embedding_model", settings.OLLAMA_MODEL_EMBED)
    return meta


def _score_chunks_cpu(
    rows: Sequence[KBChunk],
    query_embedding: bytes,
    filters: KBSearchIn | None,
) -> list[tuple[float, float, KBChunk]]:
    scored: list[tuple[float, float, KBChunk]] = []
    now = datetime.now(timezone.utc)
    for chunk in rows:
        if not chunk.embedding:
            continue
        meta = chunk.metadata_json or {}
        if filters:
            if filters.language and meta.get("language") != filters.language:
                continue
            if filters.tags:
                row_tags = set(meta.get("tags", []) or [])
                if not set(filters.tags).issubset(row_tags):
                    continue
        similarity = cosine_similarity_bytes(query_embedding, chunk.embedding)
        updated_at = getattr(chunk, "updated_at", None) or getattr(
            chunk, "created_at", None
        )
        age_seconds = 0.0
        if updated_at:
            age_seconds = max((now - updated_at).total_seconds(), 0.0)
        recency_boost = math.exp(-age_seconds / 172800)  # ~2 day half-life
        quality = float((meta.get("quality_score") or 1.0))
        score = float(similarity) * 0.85 + recency_boost * 0.1 + quality * 0.05
        scored.append((score, float(similarity), chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return scored


async def upsert_kb(
    session: AsyncSession, tenant_id: int, data: KBUpsert
) -> dict[str, int]:
    if not data.chunks:
        return {"created": 0, "updated": 0, "skipped": 0}

    skipped = 0
    filtered: list[tuple[KBChunkIn, str]] = []
    texts: list[str] = []
    for chunk in data.chunks:
        content = chunk.content.strip()
        if not content:
            skipped += 1
            continue
        texts.append(content)
        filtered.append((chunk, content))

    if not texts:
        return {"created": 0, "updated": 0, "skipped": skipped}

    try:
        embeddings = await embed_texts(texts)
    except EmbeddingServiceError as exc:
        logger.warning(
            "Failed to embed KB chunks for tenant %s source %s: %s",
            tenant_id,
            data.source,
            exc,
        )
        raise KnowledgeBaseError(str(exc), status_code=exc.status_code)

    created = updated = 0
    processed = 0
    for (chunk_in, chunk_text), emb in zip(filtered, embeddings):
        chunk_hash = hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()

        combined_tags: list[str] = []
        if chunk_in.tags:
            combined_tags.extend(chunk_in.tags)
        if data.default_tags:
            combined_tags.extend(data.default_tags)
        tags = _normalize_tags(combined_tags)
        language = (
            chunk_in.language or data.default_language or _guess_language(chunk_text)
        )
        if language:
            language = language.lower()

        payload: dict[str, Any] = {
            "language": language,
            "tags": tags,
            "source": data.source,
        }
        if chunk_in.metadata:
            payload.update(chunk_in.metadata)
        metadata = _build_metadata(chunk_text, payload)

        vector_payload = emb.vector if HAS_PGVECTOR else None
        insert_stmt = pg_insert(KBChunk).values(
            tenant_id=tenant_id,
            source=data.source,
            chunk=chunk_text,
            chunk_hash=chunk_hash,
            embedding=emb.buffer,
            embedding_vector=vector_payload,
            metadata=metadata,
        )
        excluded = insert_stmt.excluded
        stmt = (
            insert_stmt.on_conflict_do_update(
                index_elements=[KBChunk.tenant_id, KBChunk.source, KBChunk.chunk_hash],
                set_={
                    "chunk": excluded.chunk,
                    "embedding": excluded.embedding,
                    "embedding_vector": excluded.embedding_vector,
                    "metadata": excluded["metadata"],
                    "updated_at": func.now(),
                    "archived_at": None,
                },
                where=(
                    (KBChunk.chunk != excluded.chunk)
                    | (KBChunk.metadata_json != excluded["metadata"])
                    | (KBChunk.embedding != excluded.embedding)
                ),
            )
            .returning(KBChunk.created_at, KBChunk.updated_at)
        )

        result = await session.execute(stmt)
        row = result.fetchone()
        if row is None:
            skipped += 1
        else:
            processed += 1
            created_at, updated_at = row
            if created_at == updated_at:
                created += 1
            else:
                updated += 1

    return {
        "created": created,
        "updated": updated,
        "skipped": skipped,
        "processed": processed,
    }


async def search_kb(
    session: AsyncSession,
    tenant_id: int,
    query: str,
    limit: int = 5,
    *,
    filters: KBSearchIn | None = None,
) -> list[dict[str, Any]]:
    query = query.strip()
    if not query:
        return []

    # Эмбеддинг запроса
    try:
        query_embedding = (await embed_texts([query]))[0]
    except EmbeddingServiceError as exc:
        logger.warning(
            "Failed to embed KB search query for tenant %s: %s",
            tenant_id,
            exc,
        )
        raise KnowledgeBaseError(str(exc), status_code=exc.status_code)

    include_archived = bool(filters and filters.include_archived)
    limit = max(1, limit)

    if HAS_PGVECTOR:
        distance_clause = KBChunk.embedding_vector.cosine_distance(
            query_embedding.vector
        )

        stmt = (
            select(
                KBChunk,
                (1 - distance_clause).label("similarity"),
            )
            .where(KBChunk.tenant_id == tenant_id)
            .where(KBChunk.embedding_vector.isnot(None))
        )

        if filters and filters.source:
            stmt = stmt.where(KBChunk.source == filters.source)

        if not include_archived:
            stmt = stmt.where(KBChunk.archived_at.is_(None))

        if filters and filters.language:
            stmt = stmt.where(
                KBChunk.metadata_json.contains({"language": filters.language})
            )

        if filters and filters.tags:
            stmt = stmt.where(KBChunk.metadata_json["tags"].contains(filters.tags))

        stmt = stmt.order_by(distance_clause).limit(limit)

        rows = await session.execute(stmt)

        scored: list[tuple[float, float, KBChunk]] = []
        now = datetime.now(timezone.utc)
        for chunk, similarity in rows.all():
            meta = chunk.metadata_json or {}
            updated_at = getattr(chunk, "updated_at", None) or getattr(
                chunk, "created_at", None
            )
            age_seconds = 0.0
            if updated_at:
                age_seconds = max((now - updated_at).total_seconds(), 0.0)
            recency_boost = math.exp(-age_seconds / 172800)  # ~2 day half-life
            quality = float(meta.get("quality_score", 1.0) or 1.0)
            score = float(similarity) * 0.85 + recency_boost * 0.1 + quality * 0.05
            scored.append((score, float(similarity), chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        chosen = scored[:limit]

    else:
        stmt = select(KBChunk).where(KBChunk.tenant_id == tenant_id)
        if filters and filters.source:
            stmt = stmt.where(KBChunk.source == filters.source)
        if not include_archived:
            stmt = stmt.where(KBChunk.archived_at.is_(None))

        rows = (await session.execute(stmt)).scalars().all()
        scored = _score_chunks_cpu(rows, query_embedding.buffer, filters)
        chosen = scored[:limit]

    results: list[dict[str, Any]] = []
    for score, similarity, chunk in chosen:
        payload: dict[str, Any] = {
            "id": chunk.id,
            "source": chunk.source,
            "chunk": chunk.chunk,
            "score": round(score, 4),
            "similarity": round(similarity, 4),
            "archived": chunk.archived_at is not None,
        }
        if chunk.updated_at:
            payload["updated_at"] = chunk.updated_at.isoformat()
        if chunk.archived_at:
            payload["archived_at"] = chunk.archived_at.isoformat()
        if filters is None or filters.include_metadata:
            payload["metadata"] = chunk.metadata_json or {}
        results.append(payload)
    return results


async def archive_kb_chunks(
    session: AsyncSession, tenant_id: int, payload: KBArchiveIn
) -> dict[str, int]:
    if not any([payload.ids, payload.source, payload.before]):
        raise ValueError("At least one filter must be provided for archiving")

    filters: list[Any] = [KBChunk.tenant_id == tenant_id]
    if payload.ids:
        filters.append(KBChunk.id.in_(payload.ids))
    if payload.source:
        filters.append(KBChunk.source == payload.source)
    if payload.before:
        filters.append(KBChunk.updated_at <= payload.before)
    if not filters:
        return {"updated": 0}

    archived_at = func.now() if payload.archived else None
    stmt = (
        update(KBChunk)
        .where(*filters)
        .values(archived_at=archived_at)
        .returning(KBChunk.id)
    )
    rows = await session.execute(stmt)
    updated = len(rows.scalars().all())
    return {"updated": updated}


async def delete_kb_chunks(
    session: AsyncSession, tenant_id: int, payload: KBDeleteIn
) -> dict[str, int]:
    if not payload.ids and not payload.source:
        raise ValueError("At least one filter (ids or source) must be provided")

    filters: list[Any] = [KBChunk.tenant_id == tenant_id]
    if payload.ids:
        filters.append(KBChunk.id.in_(payload.ids))
    if payload.source:
        filters.append(KBChunk.source == payload.source)

    stmt = delete(KBChunk).where(*filters).returning(KBChunk.id)
    rows = await session.execute(stmt)
    deleted = len(rows.scalars().all())
    return {"deleted": deleted}


async def reindex_kb_chunks(
    session: AsyncSession, tenant_id: int, payload: KBReindexIn
) -> dict[str, int]:
    filters: list[Any] = [KBChunk.tenant_id == tenant_id]
    if payload.ids:
        filters.append(KBChunk.id.in_(payload.ids))
    if payload.source:
        filters.append(KBChunk.source == payload.source)
    if not payload.include_archived:
        filters.append(KBChunk.archived_at.is_(None))

    stmt = select(KBChunk).where(*filters).order_by(KBChunk.id)
    rows = (await session.execute(stmt)).scalars().all()
    if not rows:
        return {"processed": 0}

    processed = 0
    batch_size = payload.batch_size
    for i in range(0, len(rows), batch_size):
        batch = rows[i : i + batch_size]
        try:
            embeddings = await embed_texts([row.chunk for row in batch])
        except EmbeddingServiceError as exc:
            logger.warning(
                "Failed to reindex KB chunks for tenant %s: %s",
                tenant_id,
                exc,
            )
            raise KnowledgeBaseError(str(exc), status_code=exc.status_code)
        for row_obj, emb in zip(batch, embeddings):
            row_obj.embedding = emb.buffer
            row_obj.embedding_vector = emb.vector if HAS_PGVECTOR else None
            processed += 1
    return {"processed": processed}
