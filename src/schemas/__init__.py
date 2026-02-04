# -*- coding: utf-8 -*-
"""Pydantic schemas - CENTRALIZED VERSION.

Все схемы API в одном месте для избежания дублирования.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, EmailStr


# ============================================================
# AUTH SCHEMAS
# ============================================================

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
    tenant_id: int = Field(default=1)


class UserUpdate(BaseModel):
    """Update user profile schema."""
    full_name: str | None = Field(None, max_length=255)


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


class Token(BaseModel):
    """Token response schema."""
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema."""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password schema."""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=72)


# ============================================================
# TICKET SCHEMAS
# ============================================================

class TicketCreate(BaseModel):
    """Create ticket schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: str = Field(default="medium")
    source: str = Field(default="web")
    metadata: dict[str, Any] | None = None
    auto_respond: bool = Field(default=True)


class TicketUpdate(BaseModel):
    """Update ticket schema."""
    title: str | None = None
    description: str | None = None
    status: str | None = None
    priority: str | None = None
    assigned_to: int | None = None


class TicketResponse(BaseModel):
    """Ticket response schema."""
    id: int
    tenant_id: int
    title: str
    description: str | None
    status: str
    priority: str
    source: str
    assigned_to: int | None
    created_by_id: int | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    """Create message schema."""
    content: str = Field(..., min_length=1)
    role: str = Field(default="user")
    auto_respond: bool = Field(default=True)


class MessageResponse(BaseModel):
    """Message response schema."""
    id: int
    ticket_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# AGENT SCHEMAS
# ============================================================

class TicketRespondRequest(BaseModel):
    """Request to generate response for a ticket."""
    save_response: bool = Field(default=True)
    max_context: int = Field(default=5, ge=1, le=20)


class FreeformRequest(BaseModel):
    """Request for freeform question (playground)."""
    question: str = Field(..., min_length=1, max_length=2000)
    max_context: int = Field(default=5, ge=1, le=20)


class AgentResponseSchema(BaseModel):
    """Agent response schema."""
    content: str
    needs_escalation: bool
    escalation_reason: str | None
    context_used: list[dict[str, Any]]
    model: str


class HealthStatus(BaseModel):
    """Ollama health status."""
    ollama_available: bool
    chat_model: str
    embed_model: str
    models_loaded: list[str]


# ============================================================
# KB SCHEMAS
# ============================================================

class ChunkCreate(BaseModel):
    """Create KB chunk schema."""
    content: str = Field(..., min_length=1)
    source: str = Field(..., min_length=1, max_length=255)
    metadata: dict[str, Any] | None = None


class ChunkBulkCreate(BaseModel):
    """Bulk create KB chunks schema."""
    source: str = Field(..., min_length=1, max_length=255)
    chunks: list[dict[str, Any]]


class ChunkResponse(BaseModel):
    """KB chunk response schema."""
    id: int
    source: str
    chunk: str
    version: int
    is_current: bool

    model_config = {"from_attributes": True}


class SearchQuery(BaseModel):
    """Search query schema."""
    query: str = Field(..., min_length=1)
    limit: int = Field(default=5, ge=1, le=50)


class SearchResult(BaseModel):
    """Search result schema."""
    id: int
    source: str
    chunk: str
    score: float | None = None


# ============================================================
# TENANT SCHEMAS
# ============================================================

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
    tickets: dict[str, Any]
    users: int
    kb_chunks: int


# ============================================================
# INTEGRATION SCHEMAS
# ============================================================

class IntegrationStatus(BaseModel):
    """Integration status response."""
    system: str
    enabled: bool
    configured: bool
    last_sync: str | None = None


class IntegrationSyncRequest(BaseModel):
    """Integration sync request."""
    system: str
    reference: str
    status: str | None = None
    metadata: dict[str, Any] | None = None
    details: dict[str, Any] | None = None


class IntegrationSyncResponse(BaseModel):
    """Integration sync response."""
    system: str
    reference: str
    status: str
    message: str


class ExternalRefResponse(BaseModel):
    """External reference response."""
    id: int
    ticket_id: int
    system: str
    reference: str


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    # Auth
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "Token",
    "RefreshTokenRequest",
    "ChangePasswordRequest",
    # Tickets
    "TicketCreate",
    "TicketUpdate",
    "TicketResponse",
    "MessageCreate",
    "MessageResponse",
    # Agent
    "TicketRespondRequest",
    "FreeformRequest",
    "AgentResponseSchema",
    "HealthStatus",
    # KB
    "ChunkCreate",
    "ChunkBulkCreate",
    "ChunkResponse",
    "SearchQuery",
    "SearchResult",
    # Tenant
    "TenantCreate",
    "TenantUpdate",
    "TenantResponse",
    "TenantStats",
    # Integrations
    "IntegrationStatus",
    "IntegrationSyncRequest",
    "IntegrationSyncResponse",
    "ExternalRefResponse",
]
