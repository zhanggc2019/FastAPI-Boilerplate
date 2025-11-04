"""Celery task definitions for the application."""

from app.worker import celery_app


@celery_app.task(name="app.worker.celery_worker.test_celery")
def test_celery(word: str) -> str:
    """Demo task used for verifying Celery wiring."""
    return f"test {word}"
