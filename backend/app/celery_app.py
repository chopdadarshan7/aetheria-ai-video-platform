from celery import Celery
from .config import settings

celery_app = Celery(
    "tasks",
    broker=settings.broker_url,
    backend=settings.result_backend
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)

# Auto-discover tasks from tasks.py
celery_app.autodiscover_tasks(["app"])
