"""
Role-Based Access Control (RBAC) System

Defines permissions and role-based access control decorators.
"""

from enum import Enum
from functools import wraps
from typing import Callable, List

from fastapi import HTTPException, status
from src.domain.models import User


class Permission(str, Enum):
    """System permissions."""

    # User permissions
    USER_READ = "user:read"
    USER_CREATE = "user:create"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # Ticket permissions
    TICKET_READ_OWN = "ticket:read:own"
    TICKET_READ_ALL = "ticket:read:all"
    TICKET_CREATE = "ticket:create"
    TICKET_UPDATE_OWN = "ticket:update:own"
    TICKET_UPDATE_ALL = "ticket:update:all"
    TICKET_DELETE_OWN = "ticket:delete:own"
    TICKET_DELETE_ALL = "ticket:delete:all"
    TICKET_ASSIGN = "ticket:assign"

    # Knowledge Base permissions
    KB_READ = "kb:read"
    KB_CREATE = "kb:create"
    KB_UPDATE = "kb:update"
    KB_DELETE = "kb:delete"
    KB_UPLOAD = "kb:upload"

    # Tenant permissions
    TENANT_READ = "tenant:read"
    TENANT_CREATE = "tenant:create"
    TENANT_UPDATE = "tenant:update"
    TENANT_DELETE = "tenant:delete"
    TENANT_MANAGE_USERS = "tenant:manage:users"

    # Analytics permissions
    ANALYTICS_VIEW = "analytics:view"
    ANALYTICS_EXPORT = "analytics:export"

    # Integration permissions
    INTEGRATION_MANAGE = "integration:manage"

    # System permissions
    SYSTEM_ADMIN = "system:admin"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    "user": {
        Permission.TICKET_READ_OWN,
        Permission.TICKET_CREATE,
        Permission.TICKET_UPDATE_OWN,
        Permission.TICKET_DELETE_OWN,
        Permission.KB_READ,
    },
    "agent": {
        # All user permissions
        Permission.TICKET_READ_OWN,
        Permission.TICKET_CREATE,
        Permission.TICKET_UPDATE_OWN,
        Permission.TICKET_DELETE_OWN,
        Permission.KB_READ,
        # Agent-specific permissions
        Permission.TICKET_READ_ALL,
        Permission.TICKET_UPDATE_ALL,
        Permission.TICKET_ASSIGN,
        Permission.KB_CREATE,
        Permission.KB_UPDATE,
        Permission.ANALYTICS_VIEW,
    },
    "admin": {
        # All permissions
        Permission.USER_READ,
        Permission.USER_CREATE,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.TICKET_READ_OWN,
        Permission.TICKET_READ_ALL,
        Permission.TICKET_CREATE,
        Permission.TICKET_UPDATE_OWN,
        Permission.TICKET_UPDATE_ALL,
        Permission.TICKET_DELETE_OWN,
        Permission.TICKET_DELETE_ALL,
        Permission.TICKET_ASSIGN,
        Permission.KB_READ,
        Permission.KB_CREATE,
        Permission.KB_UPDATE,
        Permission.KB_DELETE,
        Permission.KB_UPLOAD,
        Permission.TENANT_READ,
        Permission.TENANT_UPDATE,
        Permission.TENANT_MANAGE_USERS,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.INTEGRATION_MANAGE,
    },
}

# Superadmin gets all admin permissions plus additional ones
ROLE_PERMISSIONS["superadmin"] = {
    *ROLE_PERMISSIONS["admin"],
    Permission.TENANT_CREATE,
    Permission.TENANT_DELETE,
    Permission.SYSTEM_ADMIN,
}


def has_permission(user: User, permission: Permission) -> bool:
    """
    Check if user has a specific permission.

    Args:
        user: User object
        permission: Permission to check

    Returns:
        bool: True if user has permission
    """
    if not user or not user.is_active:
        return False

    user_permissions = ROLE_PERMISSIONS.get(user.role, set())
    return permission in user_permissions


def has_any_permission(user: User, permissions: List[Permission]) -> bool:
    """
    Check if user has any of the specified permissions.

    Args:
        user: User object
        permissions: List of permissions to check

    Returns:
        bool: True if user has at least one permission
    """
    return any(has_permission(user, perm) for perm in permissions)


def has_all_permissions(user: User, permissions: List[Permission]) -> bool:
    """
    Check if user has all of the specified permissions.

    Args:
        user: User object
        permissions: List of permissions to check

    Returns:
        bool: True if user has all permissions
    """
    return all(has_permission(user, perm) for perm in permissions)


def require_permission(permission: Permission):
    """
    Decorator to require specific permission for an endpoint.

    Usage:
        @require_permission(Permission.TICKET_DELETE_ALL)
        async def delete_ticket(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current_user from kwargs
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if not has_permission(current_user, permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission.value} required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_any_permission(permissions: List[Permission]):
    """
    Decorator to require any of the specified permissions.

    Usage:
        @require_any_permission([Permission.TICKET_UPDATE_OWN, Permission.TICKET_UPDATE_ALL])
        async def update_ticket(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if not has_any_permission(current_user, permissions):
                perm_names = [p.value for p in permissions]
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: one of {perm_names} required"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_role(allowed_roles: List[str]):
    """
    Decorator to require specific role(s).

    Usage:
        @require_role(["admin", "superadmin"])
        async def admin_endpoint(...):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if current_user.role not in allowed_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role {current_user.role} not authorized. Required: {allowed_roles}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator


def can_access_ticket(user: User, ticket_user_id: int) -> bool:
    """
    Check if user can access a specific ticket.

    Args:
        user: Current user
        ticket_user_id: ID of ticket creator

    Returns:
        bool: True if user can access ticket
    """
    # Admins and agents can access all tickets
    if has_permission(user, Permission.TICKET_READ_ALL):
        return True

    # Users can only access their own tickets
    return user.id == ticket_user_id


def can_update_ticket(user: User, ticket_user_id: int) -> bool:
    """
    Check if user can update a specific ticket.

    Args:
        user: Current user
        ticket_user_id: ID of ticket creator

    Returns:
        bool: True if user can update ticket
    """
    # Admins and agents can update all tickets
    if has_permission(user, Permission.TICKET_UPDATE_ALL):
        return True

    # Users can only update their own tickets
    if has_permission(user, Permission.TICKET_UPDATE_OWN):
        return user.id == ticket_user_id

    return False


def can_delete_ticket(user: User, ticket_user_id: int) -> bool:
    """
    Check if user can delete a specific ticket.

    Args:
        user: Current user
        ticket_user_id: ID of ticket creator

    Returns:
        bool: True if user can delete ticket
    """
    # Admins can delete all tickets
    if has_permission(user, Permission.TICKET_DELETE_ALL):
        return True

    # Users can only delete their own tickets
    if has_permission(user, Permission.TICKET_DELETE_OWN):
        return user.id == ticket_user_id

    return False
