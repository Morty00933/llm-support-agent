# -*- coding: utf-8 -*-
"""Celery tasks package."""
from src.tasks.agent_tasks import (
    sync_ticket_task,
    generate_response_task,
    reindex_kb_task,
    process_ticket,
)

__all__ = [
    "sync_ticket_task",
    "generate_response_task",
    "reindex_kb_task",
    "process_ticket",
]
