from celery import Celery

from core.config import config

celery_app = Celery(
    "worker",
    backend=config.celery_backend_url,
    broker=config.celery_broker_url,
)

celery_app.conf.task_routes = {"worker.celery_worker.test_celery": "test-queue"}
celery_app.conf.update(task_track_started=True)