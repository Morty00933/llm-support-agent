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

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)

@celery.task(bind=True, name="health.ping")
def ping(self):
    TASKS_TOTAL.labels(self.name, "started").inc()
    try:
        return "pong"
    finally:
        TASKS_TOTAL.labels(self.name, "succeeded").inc()
