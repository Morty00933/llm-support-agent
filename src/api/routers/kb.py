from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..deps import get_db, tenant_dep
from ...schemas.kb import KBUpsert, KBSearchIn, KBArchiveIn, KBDeleteIn, KBReindexIn
from ...services.knowledge import (
    upsert_kb,
    search_kb,
    archive_kb_chunks,
    delete_kb_chunks,
    reindex_kb_chunks,
)

router = APIRouter(prefix="/v1/kb", tags=["kb"])


@router.post("/upsert")
async def kb_upsert(
    body: KBUpsert,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    if not body.chunks:
        raise HTTPException(status_code=400, detail="chunks is empty")
    stats = await upsert_kb(db, tenant, body)
    return {"summary": stats}


@router.post("/search")
async def kb_search(
    body: KBSearchIn,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    results = await search_kb(db, tenant, body.query, body.limit, filters=body)
    return {"results": results}


@router.post("/archive")
async def kb_archive(
    body: KBArchiveIn,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    try:
        result = await archive_kb_chunks(db, tenant, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"summary": result}


@router.post("/delete")
async def kb_delete(
    body: KBDeleteIn,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    try:
        result = await delete_kb_chunks(db, tenant, body)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"summary": result}


@router.post("/reindex")
async def kb_reindex(
    body: KBReindexIn,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    result = await reindex_kb_chunks(db, tenant, body)
    return {"summary": result}
