"""Reusable FastAPI dependencies for common operations.

This module centralizes common dependency patterns to reduce code duplication
across route handlers. It includes helpers for:
- Resource validation (get-or-404 pattern)
- Permission checking
- Common dependency combinations
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.routers.auth import User, get_current_active_user
from src.core.db import get_db
from src.core.permissions import Permission, has_permission
from src.domain.repos import TicketRepository, UserRepository, TenantRepository
from src.domain.models import Ticket, User as UserModel, Tenant


# ============================================================
# RESOURCE VALIDATION DEPENDENCIES
# ============================================================

async def get_ticket_or_404(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Ticket:
    """Get ticket by ID or raise 404.

    Also validates that ticket belongs to current user's tenant.

    Args:
        ticket_id: Ticket ID to fetch
        db: Database session
        current_user: Current authenticated user

    Returns:
        Ticket object

    Raises:
        HTTPException: 404 if ticket not found or not in user's tenant
    """
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.get(current_user.tenant_id, ticket_id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ticket not found",
        )
    return ticket


async def get_user_or_404(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> UserModel:
    """Get user by ID or raise 404.

    Also validates that user belongs to current user's tenant.

    Args:
        user_id: User ID to fetch
        db: Database session
        current_user: Current authenticated user

    Returns:
        User object

    Raises:
        HTTPException: 404 if user not found or not in same tenant
    """
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user or user.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


async def get_tenant_or_404(
    tenant_id: int,
    db: AsyncSession = Depends(get_db),
) -> Tenant:
    """Get tenant by ID or raise 404.

    Args:
        tenant_id: Tenant ID to fetch
        db: Database session

    Returns:
        Tenant object

    Raises:
        HTTPException: 404 if tenant not found
    """
    tenant_repo = TenantRepository(db)
    tenant = await tenant_repo.get_by_id(tenant_id)

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return tenant


# ============================================================
# PERMISSION DEPENDENCIES
# ============================================================

async def require_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require admin role for endpoint access.

    Args:
        current_user: Current authenticated user

    Returns:
        User object if admin

    Raises:
        HTTPException: 403 if user is not admin
    """
    if current_user.role not in ("admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def require_agent_or_admin(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Require agent or admin role for endpoint access.

    Args:
        current_user: Current authenticated user

    Returns:
        User object if agent or admin

    Raises:
        HTTPException: 403 if user is not agent or admin
    """
    if current_user.role not in ("agent", "admin", "superadmin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Agent or admin access required",
        )
    return current_user


def require_permission(permission: Permission):
    """Create dependency that requires specific permission.

    Usage:
        @router.get("/tickets", dependencies=[Depends(require_permission(Permission.TICKET_READ_ALL))])
        async def list_all_tickets(): ...

    Args:
        permission: Permission enum value required

    Returns:
        Dependency function that checks permission
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if not has_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )
        return current_user

    return permission_checker


# ============================================================
# TICKET ACCESS VALIDATION
# ============================================================

async def validate_ticket_access(
    ticket: Ticket = Depends(get_ticket_or_404),
    current_user: User = Depends(get_current_active_user),
) -> Ticket:
    """Validate that current user can access the ticket.

    Users can access their own tickets.
    Agents and admins can access all tickets in their tenant.

    Args:
        ticket: Ticket object from get_ticket_or_404
        current_user: Current authenticated user

    Returns:
        Ticket object if access allowed

    Raises:
        HTTPException: 403 if user cannot access ticket
    """
    from src.core.permissions import can_access_ticket

    if not can_access_ticket(current_user, ticket.created_by_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this ticket",
        )

    return ticket


async def validate_ticket_update_access(
    ticket: Ticket = Depends(get_ticket_or_404),
    current_user: User = Depends(get_current_active_user),
) -> Ticket:
    """Validate that current user can update the ticket.

    Users can update their own tickets.
    Agents and admins can update all tickets in their tenant.

    Args:
        ticket: Ticket object from get_ticket_or_404
        current_user: Current authenticated user

    Returns:
        Ticket object if update allowed

    Raises:
        HTTPException: 403 if user cannot update ticket
    """
    from src.core.permissions import can_update_ticket

    if not can_update_ticket(current_user, ticket.created_by_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this ticket",
        )

    return ticket


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Resource validation
    "get_ticket_or_404",
    "get_user_or_404",
    "get_tenant_or_404",
    # Permission checks
    "require_admin",
    "require_agent_or_admin",
    "require_permission",
    # Ticket access validation
    "validate_ticket_access",
    "validate_ticket_update_access",
]
