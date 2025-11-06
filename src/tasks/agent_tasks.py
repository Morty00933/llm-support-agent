from __future__ import annotations
from typing import Any

import structlog

from src.core.config import settings
from src.core.metrics import TASKS_TOTAL
from src.core.tasks import celery_app, run_async
from src.services.integrations.dispatcher import dispatch_ticket_sync


logger = structlog.get_logger(__name__)

@celery_app.task(
    bind=True,
    name="agent.sync_ticket",
    autoretry_for=(Exception,),
    retry_backoff=settings.CELERY_TASK_RETRY_BACKOFF_MIN,
    retry_backoff_max=settings.CELERY_TASK_RETRY_BACKOFF_MAX,
    retry_jitter=True,
    retry_kwargs={"max_retries": settings.CELERY_TASK_MAX_RETRIES},
    soft_time_limit=settings.CELERY_TASK_TIMEOUT_SECONDS,
    time_limit=settings.CELERY_TASK_TIMEOUT_SECONDS + 30,
)
def sync_ticket_task(
    self,
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
            timeout=settings.CELERY_TASK_TIMEOUT_SECONDS,
        )
    except Exception as exc:  # pragma: no cover - celery handles retry
        TASKS_TOTAL.labels(self.name, "failed").inc()
        log.error("sync_ticket_failed", error=str(exc))
        raise
    TASKS_TOTAL.labels(self.name, "succeeded").inc()
    log.info("sync_ticket_completed", result=result)
    return result


@celery_app.task(name="agent.process_ticket")
def process_ticket(self, ticket_id: int, tenant_id: int) -> dict[str, Any]:
    """Backward compatible wrapper that triggers integration sync."""

    return sync_ticket_task.run(  # type: ignore[attr-defined]
        ticket_id=ticket_id,
        tenant_id=tenant_id,
        message_id=None,
        escalate=False,
        kb_hits=None,
    )
