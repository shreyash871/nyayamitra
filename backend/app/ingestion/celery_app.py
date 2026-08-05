from celery import Celery

from app.core.config import settings

# This is the Celery application object.
# broker = where tasks are queued (Redis /0)
# backend = where results are stored (Redis /1)
celery_app = Celery(
    "nyayamitra",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

# Tell Celery where to find task functions
celery_app.autodiscover_tasks(["app.ingestion"])

celery_app.conf.update(
    task_track_started=True,
    task_time_limit=600,  # kill a task if it runs longer than 10 min
)
