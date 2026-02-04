"""Tenants router - FIXED VERSION."""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.repos import TenantRepository
from src.core.db import get_db
from src.api.routers.auth import get_current_active_user, User


router = APIRouter(tags=["tenants"])


class TenantCreate(BaseModel):
    """Create tenant schema."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str | None = Field(None, max_length=64)


class TenantUpdate(BaseModel):
    """Update tenant schema."""
    name: str | None = None
    is_active: bool | None = None


class TenantResponse(BaseModel):
    """Tenant response schema."""
    id: int
    name: str
    slug: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TenantStats(BaseModel):
    """Tenant statistics schema."""
    tickets_by_status: dict[str, int]
    total_tickets: int
    total_users: int
    total_kb_chunks: int


def require_admin(current_user: User = Depends(get_current_active_user)) -> User:
    """Require admin role."""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("", response_model=list[TenantResponse])
async def list_tenants(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list:
    """List all tenants (admin only)."""
    tenant_repo = TenantRepository(db)
    tenants = await tenant_repo.list()
    return list(tenants)


@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    data: TenantCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Create a new tenant (admin only)."""
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.create(
        name=data.name,
        slug=data.slug,
    )
    await db.commit()
    return tenant


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get current user's tenant."""
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id(current_user.tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return tenant


@router.get("/current/stats", response_model=TenantStats)
async def get_current_tenant_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Get statistics for current tenant."""
    tenant_repo = TenantRepository(db)
    stats = await tenant_repo.get_stats(current_user.tenant_id)
    return stats


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Get a tenant by ID (admin only)."""
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return tenant


@router.patch("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Update a tenant (admin only)."""
    tenant_repo = TenantRepository(db)
    
    existing = await tenant_repo.get_by_id(tenant_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return existing
    
    tenant = await tenant_repo.update(tenant_id, **update_data)
    return tenant


@router.get("/{tenant_id}/stats", response_model=TenantStats)
async def get_tenant_stats(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> dict:
    """Get statistics for a tenant (admin only)."""
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id(tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    stats = await tenant_repo.get_stats(tenant_id)
    return stats
