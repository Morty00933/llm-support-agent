"""Users router - user management with role-based access control."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.routers.auth import get_current_active_user, User
from src.api.dependencies import require_admin
from src.core.db import get_db
from src.core.security import get_password_hash
from src.domain.repos import UserRepository

router = APIRouter(tags=["users"])


VALID_ROLES = ("user", "agent", "admin", "superadmin")


class UserResponse(BaseModel):
    """User response schema."""
    id: int
    email: str
    full_name: str | None
    tenant_id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserCreate(BaseModel):
    """Create user schema (admin only)."""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)
    full_name: str | None = Field(None, max_length=255)
    role: Literal["user", "agent", "admin"] = Field(default="user")


class UserUpdate(BaseModel):
    """Update user schema."""
    full_name: str | None = None
    is_active: bool | None = None


class RoleUpdate(BaseModel):
    """Update user role schema."""
    role: Literal["user", "agent", "admin"] = Field(
        ...,
        description="New role for the user. Superadmin can only be set via database."
    )


@router.get("", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list:
    """List all users in current tenant.

    Requires: admin role.
    """
    user_repo = UserRepository(db)
    users = await user_repo.list_by_tenant(
        tenant_id=current_user.tenant_id,
        skip=skip,
        limit=limit,
    )
    return list(users)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    """Create a new user in current tenant.

    Requires: admin role.

    Admin can create users with roles: user, agent, admin.
    Superadmin role can only be assigned via direct database access.
    """
    user_repo = UserRepository(db)

    # Check if user already exists
    existing = await user_repo.get_by_email(current_user.tenant_id, user_data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {user_data.email} already exists",
        )

    # Admin cannot create superadmin
    if user_data.role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create superadmin via API",
        )

    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = await user_repo.create(
        tenant_id=current_user.tenant_id,
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role,
    )
    await db.commit()
    await db.refresh(user)

    return user


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    """Get user by ID.

    Requires: admin role.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    """Update user details.

    Requires: admin role.

    Note: To change user role, use PATCH /users/{user_id}/role endpoint.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Cannot modify yourself through this endpoint
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Use /auth/me to update your own profile",
        )

    update_dict = user_data.model_dump(exclude_unset=True)
    if not update_dict:
        return user

    updated_user = await user_repo.update(user_id, **update_dict)
    await db.commit()

    return updated_user


@router.patch("/{user_id}/role", response_model=UserResponse)
async def update_user_role(
    user_id: int,
    role_data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> User:
    """Change user role.

    Requires: admin role.

    Role hierarchy:
    - user: Basic access, can create/view own tickets
    - agent: Can view/update all tickets, manage KB
    - admin: Full tenant management, user management
    - superadmin: Cross-tenant access (cannot be set via API)

    Restrictions:
    - Cannot change own role
    - Cannot set superadmin role via API
    - Cannot demote another admin (only superadmin can)
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Cannot change own role
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role",
        )

    # Cannot set superadmin via API
    if role_data.role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superadmin role can only be set via database",
        )

    # Admin cannot demote another admin (only superadmin can)
    if user.role == "admin" and current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can demote an admin",
        )

    # Cannot modify superadmin
    if user.role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify superadmin role",
        )

    updated_user = await user_repo.update(user_id, role=role_data.role)
    await db.commit()

    return updated_user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Deactivate a user (soft delete).

    Requires: admin role.

    This sets is_active=False, preventing login.
    User data is preserved for audit purposes.
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Cannot deactivate yourself
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate yourself",
        )

    # Cannot deactivate superadmin
    if user.role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot deactivate superadmin",
        )

    # Admin cannot deactivate another admin
    if user.role == "admin" and current_user.role != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superadmin can deactivate an admin",
        )

    await user_repo.update(user_id, is_active=False)
    await db.commit()
