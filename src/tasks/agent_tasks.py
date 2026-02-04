# -*- coding: utf-8 -*-
"""Celery tasks for agent operations - FIXED VERSION.

ИСПРАВЛЕНИЯ:
1. Исправлен импорт celery_app
2. Добавлены правильные retry настройки
"""
from __future__ import annotations

from typing import Any

import structlog

from src.core.config import settings
from src.core.metrics import TASKS_TOTAL
from src.core.celery_app import celery_app, run_async
from src.services.integrations.dispatcher import dispatch_ticket_sync

logger = structlog.get_logger(__name__)


@celery_app.task(
    bind=True,
    name="agent.sync_ticket",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=settings.celery.task_retry_backoff_max,
    retry_jitter=True,
    max_retries=settings.celery.task_max_retries,
    soft_time_limit=settings.celery.task_timeout_seconds,
    time_limit=settings.celery.task_timeout_seconds + 30,
)
def sync_ticket_task(
    self: Any,
    ticket_id: int,
    tenant_id: int,
    message_id: int | None = None,
    escalate: bool = False,
    kb_hits: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Deliver ticket updates to configured external integrations."""
    TASKS_TOTAL.labels(self.name, "started").inc()
    
    log = logger.bind(
        task=self.name,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
        message_id=message_id,
        escalate=escalate,
    )
    
    try:
        result = run_async(
            dispatch_ticket_sync(
                ticket_id=ticket_id,
                tenant_id=tenant_id,
                message_id=message_id,
                kb_hits=kb_hits or [],
                escalate=escalate,
            ),
            timeout=settings.celery.task_timeout_seconds,
        )
        
        TASKS_TOTAL.labels(self.name, "succeeded").inc()
        log.info("sync_ticket_completed", result=result)
        return result
        
    except Exception as exc:
        TASKS_TOTAL.labels(self.name, "failed").inc()
        log.error("sync_ticket_failed", error=str(exc))
        raise


@celery_app.task(
    bind=True,
    name="agent.generate_response",
    soft_time_limit=settings.celery.task_timeout_seconds,
    time_limit=settings.celery.task_timeout_seconds + 30,
)
def generate_response_task(
    self: Any,
    ticket_id: int,
    tenant_id: int,
    save_response: bool = True,
    max_context: int = 5,
) -> dict[str, Any]:
    """Generate AI response for a ticket in background."""
    TASKS_TOTAL.labels(self.name, "started").inc()
    
    log = logger.bind(
        task=self.name,
        tenant_id=tenant_id,
        ticket_id=ticket_id,
    )
    
    try:
        from src.core.db import get_session_context
        from src.services.agent import AgentService
        
        async def _generate():
            async with get_session_context() as session:
                agent = AgentService(session)
                response = await agent.respond_to_ticket(
                    tenant_id=tenant_id,
                    ticket_id=ticket_id,
                    save_response=save_response,
                    max_context_chunks=max_context,
                )
                return {
                    "content": response.content,
                    "needs_escalation": response.needs_escalation,
                    "escalation_reason": response.escalation_reason,
                    "model": response.model,
                }
        
        result = run_async(_generate(), timeout=settings.celery.task_timeout_seconds)
        
        TASKS_TOTAL.labels(self.name, "succeeded").inc()
        log.info("generate_response_completed", result=result)
        return result
        
    except Exception as exc:
        TASKS_TOTAL.labels(self.name, "failed").inc()
        log.error("generate_response_failed", error=str(exc))
        raise


@celery_app.task(
    bind=True,
    name="agent.reindex_kb",
    soft_time_limit=600,  # 10 minutes for large KB
    time_limit=660,
)
def reindex_kb_task(
    self: Any,
    tenant_id: int,
    source: str | None = None,
) -> dict[str, Any]:
    """Reindex knowledge base embeddings."""
    TASKS_TOTAL.labels(self.name, "started").inc()
    
    log = logger.bind(
        task=self.name,
        tenant_id=tenant_id,
        source=source,
    )
    
    try:
        from src.core.db import get_session_context
        from src.services.embedding import EmbeddingService
        
        async def _reindex():
            async with get_session_context() as session:
                embedding_service = EmbeddingService(session)
                return await embedding_service.reindex_chunks(
                    tenant_id=tenant_id,
                    source=source,
                )
        
        result = run_async(_reindex(), timeout=600)
        
        TASKS_TOTAL.labels(self.name, "succeeded").inc()
        log.info("reindex_kb_completed", result=result)
        return result
        
    except Exception as exc:
        TASKS_TOTAL.labels(self.name, "failed").inc()
        log.error("reindex_kb_failed", error=str(exc))
        raise


# Backward compatible alias
@celery_app.task(bind=True, name="agent.process_ticket")
def process_ticket(
    self: Any,
    ticket_id: int,
    tenant_id: int,
) -> dict[str, Any]:
    """Backward compatible wrapper."""
    return sync_ticket_task.delay(
        ticket_id=ticket_id,
        tenant_id=tenant_id,
    ).get()


__all__ = [
    "sync_ticket_task",
    "generate_response_task",
    "reindex_kb_task",
    "process_ticket",
]
