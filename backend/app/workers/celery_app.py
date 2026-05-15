"""
Celery application initialization and configuration.
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "lodge_link_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks", "app.workers.email_tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Worker configuration
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
    task_acks_late=True,
)
