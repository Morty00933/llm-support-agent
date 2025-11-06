from __future__ import annotations
from fastapi import APIRouter

router = APIRouter(prefix="/v1/admin", tags=["admin"])


@router.get("/ping")
async def ping():
    return {"pong": True}
