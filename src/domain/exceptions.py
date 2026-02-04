# -*- coding: utf-8 -*-
"""Domain exceptions."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DomainError(Exception):
    """Base domain exception."""
    
    message: str
    code: str = "DOMAIN_ERROR"
    details: dict[str, Any] = field(default_factory=dict)
    
    def __str__(self) -> str:
        return self.message


@dataclass
class EntityNotFoundError(DomainError):
    """Entity not found."""
    
    entity_type: str = ""
    entity_id: Any = None
    code: str = "ENTITY_NOT_FOUND"
    
    def __post_init__(self):
        if not self.message:
            self.message = f"{self.entity_type} with id={self.entity_id} not found"


@dataclass
class EntityAlreadyExistsError(DomainError):
    """Entity already exists."""
    
    entity_type: str = ""
    code: str = "ENTITY_ALREADY_EXISTS"


@dataclass
class EntityValidationError(DomainError):
    """Entity validation error."""
    
    code: str = "VALIDATION_ERROR"
    field_name: str | None = None


class TenantNotFoundError(EntityNotFoundError):
    """Tenant not found."""
    
    def __init__(self, tenant_id: int):
        super().__init__(
            message=f"Tenant {tenant_id} not found",
            entity_type="Tenant",
            entity_id=tenant_id,
        )


class UserNotFoundError(EntityNotFoundError):
    """User not found."""
    
    def __init__(self, identifier: str | int):
        super().__init__(
            message=f"User {identifier} not found",
            entity_type="User",
            entity_id=identifier,
        )


class TicketNotFoundError(EntityNotFoundError):
    """Ticket not found."""
    
    def __init__(self, ticket_id: int):
        super().__init__(
            message=f"Ticket {ticket_id} not found",
            entity_type="Ticket",
            entity_id=ticket_id,
        )


class KBChunkNotFoundError(EntityNotFoundError):
    """KB Chunk not found."""
    
    def __init__(self, chunk_id: int):
        super().__init__(
            message=f"KB Chunk {chunk_id} not found",
            entity_type="KBChunk",
            entity_id=chunk_id,
        )


@dataclass
class InvalidStateTransitionError(DomainError):
    """Invalid state transition."""
    
    current_state: str = ""
    target_state: str = ""
    code: str = "INVALID_STATE_TRANSITION"
    
    def __post_init__(self):
        if not self.message:
            self.message = (
                f"Cannot transition from {self.current_state} to {self.target_state}"
            )


@dataclass
class TenantMismatchError(DomainError):
    """Tenant mismatch."""
    
    code: str = "TENANT_MISMATCH"
    expected_tenant: int = 0
    actual_tenant: int = 0


@dataclass
class AuthenticationError(DomainError):
    """Authentication error."""
    
    code: str = "AUTHENTICATION_ERROR"


@dataclass
class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials."""
    
    code: str = "INVALID_CREDENTIALS"
    
    def __post_init__(self):
        if not self.message:
            self.message = "Invalid email or password"


__all__ = [
    "DomainError",
    "EntityNotFoundError",
    "EntityAlreadyExistsError",
    "EntityValidationError",
    "TenantNotFoundError",
    "UserNotFoundError",
    "TicketNotFoundError",
    "KBChunkNotFoundError",
    "InvalidStateTransitionError",
    "TenantMismatchError",
    "AuthenticationError",
    "InvalidCredentialsError",
]
