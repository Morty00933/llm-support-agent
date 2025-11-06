from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import jwt
from passlib.context import CryptContext
from .config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)

def create_access_token(subject: str, tenant: int, expires_minutes: Optional[int] = None) -> str:
    exp = datetime.now(tz=timezone.utc) + timedelta(minutes=expires_minutes or settings.JWT_EXPIRE_MIN)
    payload = {
        "sub": subject,
        "tenant": tenant,
        "aud": settings.JWT_AUD,
        "iss": settings.JWT_ISS,
        "exp": exp,
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG)
    return token
