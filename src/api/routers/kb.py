from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..deps import get_db, tenant_dep
from ...schemas.kb import KBUpsert, KBSearchIn
from ...services.knowledge import upsert_kb, search_kb

router = APIRouter(prefix="/v1/kb", tags=["kb"])


@router.post("/upsert")
async def kb_upsert(
    body: KBUpsert,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    if not body.chunks:
        raise HTTPException(status_code=400, detail="chunks is empty")
    inserted = await upsert_kb(db, tenant, body)
    return {"inserted": inserted}


@router.post("/search")
async def kb_search(
    body: KBSearchIn,
    db: AsyncSession = Depends(get_db),
    tenant: int = Depends(tenant_dep),
):
    results = await search_kb(db, tenant, body.query, body.limit)
    return {"results": results}
