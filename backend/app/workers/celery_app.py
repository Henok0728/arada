"""
Celery application initialization and configuration.
"""
from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "lodge_link_workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.workers.tasks"]
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
