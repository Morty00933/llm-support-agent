"""Сервисы работы с базой знаний (upsert + поиск)."""

from __future__ import annotations

from sqlalchemy import insert, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..domain.models import KBChunk
from ..schemas.kb import KBUpsert
from .embeddings import embed_texts
from .search import cosine_similarity_bytes


async def upsert_kb(session: AsyncSession, tenant_id: int, data: KBUpsert) -> int:
    if not data.chunks:
        return 0
    chunks = [c.content for c in data.chunks]
    embs = await embed_texts(chunks)

    total = 0
    for chunk_text, emb in zip(chunks, embs):
        stmt = insert(KBChunk).values(
            tenant_id=tenant_id,
            source=data.source,
            chunk=chunk_text,
            embedding=emb,
        )
        await session.execute(stmt)
        total += 1
    # Коммит делается во внешнем контексте (см. core.db.get_session)
    return total


async def search_kb(
    session: AsyncSession, tenant_id: int, query: str, limit: int = 5
) -> list[dict]:
    if not query.strip():
        return []

    # Эмбеддинг запроса
    q_emb = (await embed_texts([query]))[0]

    # Берём разумный верхний предел выборки — для прод лучше хранить векторно (pgvector) и фильтровать в SQL
    rows = (
        (
            await session.execute(
                select(KBChunk)
                .where(KBChunk.tenant_id == tenant_id)
                .order_by(KBChunk.id.desc())
                .limit(2000)
            )
        )
        .scalars()
        .all()
    )

    scored: list[tuple[float, KBChunk]] = []
    for r in rows:
        if not r.embedding:
            continue
        s = cosine_similarity_bytes(q_emb, r.embedding)
        scored.append((s, r))

    scored.sort(key=lambda x: x[0], reverse=True)
    result = [
        {"id": r.id, "source": r.source, "chunk": r.chunk, "score": round(score, 4)}
        for score, r in scored[:limit]
    ]
    return result
