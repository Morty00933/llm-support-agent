"""Сервисы работы с базой знаний (upsert + поиск)."""

from __future__ import annotations

import hashlib
import math
import re
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.config import settings
from ..domain.models import KBChunk
from ..schemas.kb import KBUpsert, KBSearchIn, KBChunkIn
from .embeddings import embed_texts
from .search import cosine_similarity_bytes


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

    embeddings = await embed_texts(texts)

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

        payload: dict[str, Any] = {
            "language": language,
            "tags": tags,
            "source": data.source,
        }
        if chunk_in.metadata:
            payload.update(chunk_in.metadata)
        metadata = _build_metadata(chunk_text, payload)

        stmt = (
            pg_insert(KBChunk)
            .values(
                tenant_id=tenant_id,
                source=data.source,
                chunk=chunk_text,
                chunk_hash=chunk_hash,
                embedding=emb,
                metadata=metadata,
            )
            .on_conflict_do_update(
                index_elements=[KBChunk.tenant_id, KBChunk.source, KBChunk.chunk_hash],
                set_={
                    "chunk": pg_insert.excluded.chunk,
                    "embedding": pg_insert.excluded.embedding,
                    "metadata": pg_insert.excluded.metadata,
                    "updated_at": func.now(),
                },
                where=(
                    (KBChunk.chunk != pg_insert.excluded.chunk)
                    | (KBChunk.metadata_json != pg_insert.excluded.metadata)
                    | (KBChunk.embedding != pg_insert.excluded.embedding)
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
    q_emb = (await embed_texts([query]))[0]

    stmt = select(KBChunk).where(KBChunk.tenant_id == tenant_id)
    if filters and filters.source:
        stmt = stmt.where(KBChunk.source == filters.source)
    stmt = stmt.order_by(KBChunk.updated_at.desc()).limit(4000)

    rows = (await session.execute(stmt)).scalars().all()

    scored: list[tuple[float, KBChunk]] = []
    now = datetime.now(timezone.utc)
    for r in rows:
        if not r.embedding:
            continue
        meta = r.metadata_json or {}
        if filters:
            if filters.language and meta.get("language") != filters.language:
                continue
            if filters.tags:
                row_tags = set(meta.get("tags", []) or [])
                if not set(filters.tags).issubset(row_tags):
                    continue
        similarity = cosine_similarity_bytes(q_emb, r.embedding)
        age_seconds = 0.0
        updated_at = getattr(r, "updated_at", None) or getattr(r, "created_at", None)
        if updated_at:
            age_seconds = max((now - updated_at).total_seconds(), 0.0)
        recency_boost = math.exp(-age_seconds / 86400)  # ~1 day half-life
        quality = meta.get("quality_score", 1.0)
        score = similarity * 0.75 + recency_boost * 0.2 + float(quality) * 0.05
        scored.append((score, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    results: list[dict[str, Any]] = []
    for score, r in scored[:limit]:
        payload = {
            "id": r.id,
            "source": r.source,
            "chunk": r.chunk,
            "score": round(score, 4),
        }
        if filters is None or filters.include_metadata:
            payload["metadata"] = r.metadata_json or {}
        results.append(payload)
    return results
