from __future__ import annotations
from typing import Any

from pydantic import BaseModel, Field, validator


class KBChunkIn(BaseModel):
    content: str = Field(..., min_length=1)
    language: str | None = Field(None, min_length=2, max_length=8)
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None

    @validator("tags", pre=True)
    def _normalize_tags(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            value = [value]
        return [str(t).strip() for t in value if str(t).strip()]


class KBUpsert(BaseModel):
    source: str = Field(..., min_length=1)
    chunks: list[KBChunkIn]
    default_language: str | None = Field(None, min_length=2, max_length=8)
    default_tags: list[str] | None = None

    @validator("default_tags", pre=True)
    def _normalize_default_tags(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            value = [value]
        return [str(t).strip() for t in value if str(t).strip()]


class KBSearchIn(BaseModel):
    query: str = Field(..., min_length=1)
    limit: int = Field(5, ge=1, le=50)
    source: str | None = None
    tags: list[str] | None = None
    language: str | None = Field(None, min_length=2, max_length=8)
    include_metadata: bool = False

    @validator("tags", pre=True)
    def _normalize_tags(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            value = [value]
        return [str(t).strip() for t in value if str(t).strip()]
