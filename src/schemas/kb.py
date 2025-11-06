from __future__ import annotations
from pydantic import BaseModel, Field


class KBChunkIn(BaseModel):
    content: str = Field(..., min_length=1)


class KBUpsert(BaseModel):
    source: str = Field(..., min_length=1)
    chunks: list[KBChunkIn]


class KBSearchIn(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(5, ge=1, le=50)
