from __future__ import annotations
import asyncio

from celery import Celery

from .config import settings
from .metrics import TASKS_TOTAL

celery = Celery(
    main=settings.APP_NAME,
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND,
)

celery.conf.task_acks_late = True
celery.conf.task_track_started = True
celery.conf.result_expires = 3600
celery.conf.worker_prefetch_multiplier = 1


def run_async(coro, *, timeout: float | None = None):
    async def _runner():
        if timeout is not None:
            return await asyncio.wait_for(coro, timeout=timeout)
        return await coro

    return asyncio.run(_runner())


@celery.task(bind=True, name="health.ping")
def ping(self):
    TASKS_TOTAL.labels(self.name, "started").inc()
    try:
        return "pong"
    finally:
        TASKS_TOTAL.labels(self.name, "succeeded").inc()


celery_app = celery
