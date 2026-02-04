from __future__ import annotations
from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    email: str
    password: str
    tenant: int = Field(1, ge=1)


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
