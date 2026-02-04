# -*- coding: utf-8 -*-
"""Domain package - models and repositories.

This package contains:
- SQLAlchemy models (entities)
- Repository functions and classes
- Domain exceptions

Usage:
    from src.domain import Ticket, User, repos
    from src.domain.models import TicketStatus, TicketPriority
"""
from src.domain.models import (
    Base,
    Tenant,
    User,
    Ticket,
    Message,
    KBChunk,
    TicketExternalRef,
    IntegrationSyncLog,
    MessageRole,
    TicketStatus,
    TicketPriority,
)
from src.domain import repos

__all__ = [
    # Base
    "Base",
    # Models
    "Tenant",
    "User",
    "Ticket",
    "Message",
    "KBChunk",
    "TicketExternalRef",
    "IntegrationSyncLog",
    # Enums
    "MessageRole",
    "TicketStatus",
    "TicketPriority",
    # Repos module
    "repos",
]
