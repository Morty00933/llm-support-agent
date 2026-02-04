# -*- coding: utf-8 -*-
"""Authentication router - FIXED VERSION.

ИСПРАВЛЕНИЯ:
1. Добавлен PATCH /me для обновления профиля
2. Добавлен POST /change-password для смены пароля
3. Исправлен login_json для использования tenant_id из body
4. Улучшена валидация паролей
5. Добавлен demo mode
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.db import get_db
from src.core.exceptions import (
    EmailAlreadyExistsException,
    InactiveUserException,
    InvalidCredentialsException,
    InvalidTokenException,
    BadRequestException,
)
from src.core.security import (
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    validate_password_strength,
)
from src.domain.models import User
from src.domain.repos import UserRepository


router = APIRouter(tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


class UserCreate(BaseModel):
    """User registration schema."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str | None = Field(None, max_length=255)
    tenant_id: int = Field(default=1)


class UserLogin(BaseModel):
    """User login schema (JSON body)."""
    email: EmailStr
    password: str = Field(..., max_length=72)
    tenant_id: int = Field(default=1, description="Tenant ID for multi-tenant support")


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token payload data."""
    user_id: int | None = None
    tenant_id: int | None = None
    email: str | None = None


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    email: str
    full_name: str | None
    tenant_id: int
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class UserUpdate(BaseModel):
    """Update user profile schema."""
    full_name: str | None = Field(None, max_length=255)


class ChangePasswordRequest(BaseModel):
    """Change password schema."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=72)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret,
            algorithms=[settings.jwt.algorithm],
            audience=settings.jwt.audience,
            issuer=settings.jwt.issuer,
        )

        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        token_type = payload.get("type", "access")
        if token_type != "access":
            raise credentials_exception

    except JWTError:
        raise credentials_exception
    
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))
    
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Get current active user."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def _create_token_response(user: User) -> dict:
    """Create token response for a user.

    This helper function eliminates duplication across login endpoints.

    Args:
        user: Authenticated user

    Returns:
        Dict with access_token, refresh_token, token_type, expires_in
    """
    access_token = create_access_token(
        data={"sub": str(user.id), "tenant_id": user.tenant_id, "email": user.email}
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id), "tenant_id": user.tenant_id}
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": settings.jwt.expire_minutes * 60,
    }


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Register a new user."""
    user_repo = UserRepository(db)

    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.password, user_data.email)
    if not is_valid:
        raise BadRequestException(error_msg)

    # Check if user exists
    existing = await user_repo.get_by_email(user_data.tenant_id, user_data.email)
    if existing:
        raise EmailAlreadyExistsException(user_data.email)

    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = await user_repo.create(
        tenant_id=user_data.tenant_id,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role="user",
    )
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Login with OAuth2 form (username/password)."""
    user_repo = UserRepository(db)

    # Try to find user (tenant_id defaults to 1 for form login)
    user = await user_repo.get_by_email(1, form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise InvalidCredentialsException()

    if not user.is_active:
        raise InactiveUserException()

    # Use helper function to create tokens
    return _create_token_response(user)


@router.post("/login/json", response_model=Token)
async def login_json(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Login with JSON body."""
    user_repo = UserRepository(db)

    user = await user_repo.get_by_email(credentials.tenant_id, credentials.email)

    if not user or not verify_password(credentials.password, user.hashed_password):
        raise InvalidCredentialsException()

    if not user.is_active:
        raise InactiveUserException()

    # Use helper function to create tokens
    return _create_token_response(user)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Refresh access token using refresh token."""
    try:
        payload = jwt.decode(
            request.refresh_token,
            settings.jwt.secret,
            algorithms=[settings.jwt.algorithm],
            audience=settings.jwt.audience,
            issuer=settings.jwt.issuer,
        )

        if payload.get("type") != "refresh":
            raise InvalidTokenException("Invalid token type")

        user_id = payload.get("sub")
        tenant_id = payload.get("tenant_id")

        if not user_id:
            raise InvalidTokenException("Invalid token")

    except JWTError:
        raise InvalidTokenException("Invalid refresh token")

    # Verify user still exists and is active
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(int(user_id))

    if not user:
        raise InvalidTokenException("User not found")

    if not user.is_active:
        raise InactiveUserException()

    # Use helper function to create new tokens
    return _create_token_response(user)


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Get current user profile."""
    return current_user


@router.patch("/me", response_model=UserResponse)
async def update_me(
    update_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Update current user profile."""
    user_repo = UserRepository(db)
    
    # Build update dict
    update_dict: dict[str, Any] = {}
    if update_data.full_name is not None:
        update_dict["full_name"] = update_data.full_name
    
    if update_dict:
        updated_user = await user_repo.update(current_user.id, **update_dict)
        await db.flush()
        # Commit is handled by get_db() dependency

        if updated_user:
            return updated_user

    return current_user


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    request: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Change current user's password."""
    # Verify current password
    if not verify_password(request.current_password, current_user.hashed_password):
        raise BadRequestException("Current password is incorrect")

    # Check new password is different
    if request.current_password == request.new_password:
        raise BadRequestException("New password must be different from current password")

    # Update password
    user_repo = UserRepository(db)
    new_hash = get_password_hash(request.new_password)

    await user_repo.update(current_user.id, hashed_password=new_hash)
    await db.flush()
    # Commit is handled by get_db() dependency

    return {"message": "Password changed successfully"}


__all__ = [
    "router",
    "get_current_user",
    "get_current_active_user",
    "get_password_hash",
    "verify_password",
    "create_access_token",
    "create_refresh_token",
    "User",
]
