from __future__ import annotations
from pydantic import BaseModel, Field


class TicketIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)


class TicketOut(BaseModel):
    id: int
    title: str
    status: str


class MessageIn(BaseModel):
    role: str = Field(..., pattern="^(user|agent|system)$")
    content: str = Field(..., min_length=1)


class MessageOut(BaseModel):
    id: int
    role: str
    content: str
