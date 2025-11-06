from __future__ import annotations
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter
from pydantic import BaseModel, Field
from jose import jwt
from ...core.config import settings

router = APIRouter(prefix="/v1/auth", tags=["auth"])


class LoginIn(BaseModel):
    email: str
    password: str
    tenant: int = Field(1, ge=1)


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=LoginOut)
async def login(body: LoginIn):
    """
    Демонстрационная ручка логина — принимает любую пару.
    В реальном проекте проверь пароль, вытащи пользователя из БД и т.д.
    """
    exp = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.JWT_EXPIRE_MIN)
    token = jwt.encode(
        {
            "sub": body.email,
            "tenant": body.tenant,
            "aud": settings.JWT_AUD,
            "iss": settings.JWT_ISS,
            "exp": exp,
        },
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALG,
    )
    return LoginOut(access_token=token)
