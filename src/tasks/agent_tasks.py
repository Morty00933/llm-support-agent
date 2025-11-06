from __future__ import annotations
from typing import Any

from src.core.tasks import celery_app, run_async
from src.services.integrations.dispatcher import dispatch_ticket_sync


@celery_app.task(name="agent.sync_ticket")
def sync_ticket_task(
    ticket_id: int,
    tenant_id: int,
    message_id: int | None = None,
    escalate: bool = False,
    kb_hits: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Deliver ticket updates to configured external integrations."""

    return run_async(
        dispatch_ticket_sync(
            ticket_id=ticket_id,
            tenant_id=tenant_id,
            message_id=message_id,
            kb_hits=kb_hits or [],
            escalate=escalate,
        )
    )



@celery_app.task(name="agent.process_ticket")
def process_ticket(ticket_id: int, tenant_id: int) -> dict[str, Any]:
    """Backward compatible wrapper that triggers integration sync."""

    return sync_ticket_task(ticket_id=ticket_id, tenant_id=tenant_id)
