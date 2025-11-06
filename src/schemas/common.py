from __future__ import annotations
from typing import Generic, TypeVar, List
from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorResponse(BaseModel):
    detail: str


class Page(BaseModel, Generic[T]):
    items: List[T] = Field(default_factory=list)
    total: int
    limit: int
    offset: int
