"""Схемы для интеграций."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IntegrationSyncRequest(BaseModel):
    """Запрос на синхронизацию с внешней системой."""
    
    system: str = Field(..., min_length=1, description="Название системы (jira, zendesk)")
    reference: str = Field(..., min_length=1, description="Внешний идентификатор")
    status: str | None = Field(default="synced", description="Статус синхронизации")
    metadata: dict[str, Any] | None = Field(default=None, description="Дополнительные данные")
    details: dict[str, Any] | None = Field(default=None, description="Детали синхронизации")


class IntegrationSyncResponse(BaseModel):
    """Ответ на синхронизацию."""
    
    system: str
    reference: str
    status: str
    message: str | None = None
    error: str | None = None


class JiraWebhookPayload(BaseModel):
    """Payload от Jira webhook."""
    
    webhookEvent: str
    issue: dict[str, Any] | None = None
    comment: dict[str, Any] | None = None
    changelog: dict[str, Any] | None = None


class ZendeskWebhookPayload(BaseModel):
    """Payload от Zendesk webhook."""
    
    ticket: dict[str, Any] | None = None
    current_user: dict[str, Any] | None = None
