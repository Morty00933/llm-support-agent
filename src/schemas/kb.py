"""Схемы для работы с базой знаний."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class KBChunkIn(BaseModel):
    """Входные данные для одного chunk."""
    content: str = Field(..., min_length=1)
    language: str | None = None
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None


class KBUpsert(BaseModel):
    """Запрос на добавление/обновление chunks."""
    source: str = Field(..., min_length=1)
    chunks: list[KBChunkIn] = Field(..., min_length=1)
    default_language: str | None = None
    default_tags: list[str] | None = None


class KBSearchIn(BaseModel):
    """Параметры поиска по KB."""
    source: str | None = None
    language: str | None = None
    tags: list[str] | None = None
    include_archived: bool = False
    include_metadata: bool = True


class KBChunkOut(BaseModel):
    """Выходные данные chunk."""
    id: int
    source: str
    chunk: str
    score: float | None = None
    similarity: float | None = None
    archived: bool = False
    updated_at: str | None = None
    archived_at: str | None = None
    metadata: dict[str, Any] | None = None


class KBArchiveIn(BaseModel):
    """Запрос на архивацию chunks."""
    ids: list[int] | None = None
    source: str | None = None
    before: datetime | None = None
    archived: bool = True


class KBDeleteIn(BaseModel):
    """Запрос на удаление chunks."""
    ids: list[int] | None = None
    source: str | None = None


class KBReindexIn(BaseModel):
    """Запрос на переиндексацию."""
    ids: list[int] | None = None
    source: str | None = None
    include_archived: bool = False
    batch_size: int = Field(default=50, ge=1, le=500)


class KBUpsertResponse(BaseModel):
    """Ответ на upsert."""
    created: int
    updated: int
    skipped: int
    processed: int = 0


class KBSearchResponse(BaseModel):
    """Ответ поиска."""
    items: list[KBChunkOut]
    query: str
    total: int
