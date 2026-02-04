"""Security utilities for password hashing and JWT tokens."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import jwt
from passlib.context import CryptContext

from .config import settings

import bcrypt as _bcrypt_module
_original_hashpw = _bcrypt_module.hashpw


def _patched_hashpw(password, salt):
    """Wrapper for bcrypt.hashpw that truncates passwords > 72 bytes."""
    if isinstance(password, str):
        password = password.encode('utf-8')
    if len(password) > 72:
        password = password[:72]
    return _original_hashpw(password, salt)


_bcrypt_module.hashpw = _patched_hashpw

logger = logging.getLogger(__name__)


COMMON_PASSWORDS = {
    "password", "12345678", "qwerty123", "admin123",
    "welcome123", "password123", "pass1234", "letmein123",
    "admin1234", "test1234", "user1234"
}


def validate_password_strength(password: str, email: str | None = None) -> tuple[bool, str | None]:
    """Validate password strength."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"

    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"

    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"

    if password.lower() in COMMON_PASSWORDS:
        return False, "Password is too common, please choose a stronger password"

    if email and password.lower() == email.lower():
        return False, "Password cannot be the same as email"

    return True, None


pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__ident="2b",
    bcrypt__truncate_error=False
)


def hash_password(password: str) -> str:
    """Hash password using bcrypt via passlib."""
    if len(password.encode('utf-8')) > 72:
        password = password.encode('utf-8')[:72].decode('utf-8', errors='ignore')

    return pwd_context.hash(password)


def get_password_hash(password: str) -> str:
    """Alias for hash_password for backward compatibility."""
    return hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except (ValueError, TypeError) as e:
        logger.warning(f"Password verification failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in password verification: {e}", exc_info=True)
        return False


def create_access_token(
    data: dict[str, Any] | None = None,
    subject: str | None = None,
    tenant: int | None = None,
    expires_delta: timedelta | None = None,
    expires_minutes: Optional[int] = None,
) -> str:
    """Create JWT access token."""
    if subject is not None and tenant is not None:
        to_encode = {
            "sub": subject,
            "tenant": tenant,
        }
    elif data is not None:
        to_encode = data.copy()
    else:
        raise ValueError("Either 'data' or both 'subject' and 'tenant' must be provided")

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    elif expires_minutes:
        expire = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.expire_minutes
        )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access",
        "aud": settings.jwt.audience,
        "iss": settings.jwt.issuer,
    })

    token = jwt.encode(to_encode, settings.jwt.secret, algorithm=settings.jwt.algorithm)
    return token


def create_refresh_token(data: dict[str, Any]) -> str:
    """Create JWT refresh token."""
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt.refresh_expire_days
    )

    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh",
        "aud": settings.jwt.audience,
        "iss": settings.jwt.issuer,
    })

    return jwt.encode(to_encode, settings.jwt.secret, algorithm=settings.jwt.algorithm)


__all__ = [
    "validate_password_strength",
    "hash_password",
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
]
