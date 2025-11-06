from __future__ import annotations
from typing import Any

from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class KBChunkIn(BaseModel):
    content: str = Field(..., min_length=1)
    language: str | None = Field(None, min_length=2, max_length=8)
    tags: list[str] | None = None
    metadata: dict[str, Any] | None = None

    @field_validator("language", mode="before")
    @classmethod
    def _normalize_language(cls, value: Any) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value.lower() or None

    @field_validator("tags", mode="before")
    @classmethod
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

    @field_validator("default_language", mode="before")
    @classmethod
    def _normalize_default_language(cls, value: Any) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value.lower() or None

    @field_validator("default_tags", mode="before")
    @classmethod
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
    include_archived: bool = False

    @field_validator("language", mode="before")
    @classmethod
    def _normalize_language(cls, value: Any) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value.lower() or None

    @field_validator("tags", mode="before")
    @classmethod
    def _normalize_tags(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, str):
            value = [value]
        return [str(t).strip() for t in value if str(t).strip()]


class KBArchiveIn(BaseModel):
    ids: list[int] | None = None
    source: str | None = None
    before: datetime | None = None
    archived: bool = True

    @model_validator(mode="after")
    def _ensure_filters(self) -> "KBArchiveIn":
        if not any([self.ids, self.source, self.before]):
            raise ValueError("at least one of ids, source or before must be provided")
        return self


class KBDeleteIn(BaseModel):
    ids: list[int] | None = None
    source: str | None = None

    @model_validator(mode="after")
    def _ensure_filters(self) -> "KBDeleteIn":
        if not any([self.ids, self.source]):
            raise ValueError("ids or source must be provided")
        return self


class KBReindexIn(BaseModel):
    ids: list[int] | None = None
    source: str | None = None
    include_archived: bool = False
    batch_size: int = Field(16, ge=1, le=128)
