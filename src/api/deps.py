from __future__ import annotations
from typing import Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
from ..core.db import get_session
from ..core.config import settings


async def get_db() -> AsyncSession:
    """Dependency: выдать async-сессию БД с автокоммитом/автороллбеком."""
    async with get_session() as s:
        yield s


def _decode_jwt(token: str) -> dict:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALG],
            audience=settings.JWT_AUD,
            issuer=settings.JWT_ISS,
            options={"require": ["exp", "aud", "iss"]},
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


async def get_current_user(authorization: Optional[str] = Header(None)) -> dict:
    """Парсит и валидирует Bearer JWT из заголовка Authorization."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid auth scheme")
    return _decode_jwt(token)


async def tenant_dep(
    user: dict = Depends(get_current_user),
    x_tenant_id: Optional[str] = Header(None),
) -> int:
    """
    Достаём tenant: приоритет у токена, затем X-Tenant-Id.
    Ожидается целочисленный id; если нужен slug — адаптируй.
    """
    tenant = user.get("tenant") or x_tenant_id
    if tenant is None:
        raise HTTPException(status_code=400, detail="Tenant is required")
    try:
        return int(tenant)
    except ValueError:
        raise HTTPException(status_code=400, detail="Tenant must be integer id")
