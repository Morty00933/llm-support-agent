# -*- coding: utf-8 -*-
"""Celery application configuration - UNIFIED VERSION."""
from __future__ import annotations

import asyncio
from typing import Any, Coroutine, TypeVar

from celery import Celery

from src.core.config import settings
from src.core.metrics import TASKS_TOTAL

T = TypeVar("T")


# ============================================================
# CELERY APP
# ============================================================

celery_app = Celery(
    "llm-support-agent",
    broker=settings.celery.broker_url,
    backend=settings.celery.result_backend,
)

# Configure Celery
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Timezone
    timezone="UTC",
    enable_utc=True,
    
    # Task settings
    task_track_started=True,
    task_acks_late=True,
    task_time_limit=settings.celery.task_timeout_seconds + 30,
    task_soft_time_limit=settings.celery.task_timeout_seconds,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    
    # Results
    result_expires=3600,  # 1 hour
    
    # Retry settings (с fallback на разумные значения)
    task_default_retry_delay=getattr(settings.celery, "task_retry_backoff_min", 60),
    task_max_retries=getattr(settings.celery, "task_max_retries", 3),
    
    task_always_eager=settings.celery.task_always_eager,
    task_ignore_result=settings.celery.task_ignore_result,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["src.tasks"])


# ============================================================
# ASYNC HELPER
# ============================================================

def run_async(
    coro: Coroutine[Any, Any, T],
    *,
    timeout: float | None = None,
) -> T:
    """Run async coroutine in sync context."""
    async def _runner() -> T:
        if timeout is not None:
            return await asyncio.wait_for(coro, timeout=timeout)
        return await coro

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(_runner())
    finally:
        loop.close()


# ============================================================
# BUILT-IN TASKS
# ============================================================

@celery_app.task(bind=True, name="health.ping")
def ping(self: Any) -> str:
    """Health check task."""
    TASKS_TOTAL.labels(self.name, "started").inc()
    try:
        return "pong"
    finally:
        TASKS_TOTAL.labels(self.name, "succeeded").inc()


@celery_app.task(bind=True, name="health.check_db")
def check_db_task(self: Any) -> dict[str, Any]:
    """Check database connectivity."""
    from src.core.db import check_db_connection
    
    TASKS_TOTAL.labels(self.name, "started").inc()
    try:
        is_connected = run_async(check_db_connection())
        return {"database": "connected" if is_connected else "disconnected"}
    except Exception as e:
        TASKS_TOTAL.labels(self.name, "failed").inc()
        return {"database": "error", "error": str(e)}
    finally:
        TASKS_TOTAL.labels(self.name, "succeeded").inc()


# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "celery_app",
    "run_async",
    "ping",
    "check_db_task",
]