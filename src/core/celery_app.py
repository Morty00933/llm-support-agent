from __future__ import annotations
from celery import Celery
from .config import settings

celery_app = Celery(
    main=settings.APP_NAME,
    broker=settings.BROKER_URL,
    backend=settings.RESULT_BACKEND,
)

celery_app.conf.task_acks_late = True
celery_app.conf.task_track_started = True
celery_app.conf.result_expires = 3600
celery_app.conf.worker_prefetch_multiplier = 1
