"""
Celery Application — Retraining pipeline.

File: backend/pipelines/retraining/celery_app.py
"""

from celery import Celery

from shared.config import settings

celery_app = Celery(
    "bravola_retraining",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

# Auto-discover tasks
celery_app.autodiscover_tasks(["pipelines.retraining"])
