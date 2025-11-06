from __future__ import annotations
from core.tasks import celery_app

@celery_app.task(name="agent.process_ticket")
def process_ticket(ticket_id: int) -> str:
    return f"processed {ticket_id}"
