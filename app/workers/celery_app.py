"""Celery application — Redis broker for background workers."""

from __future__ import annotations

from celery import Celery

from app.config import settings


def _broker_url() -> str:
    return settings.celery_broker_url or settings.redis_url


def _result_backend() -> str:
    return settings.celery_result_backend or settings.celery_broker_url or settings.redis_url


celery_app = Celery(
    "mindguess",
    broker=_broker_url(),
    backend=_result_backend(),
    include=["app.workers.tasks"],
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
    task_default_retry_delay=settings.celery_retry_delay_seconds,
    task_always_eager=settings.celery_task_always_eager,
    task_eager_propagates=True,
    broker_connection_retry_on_startup=True,
    result_expires=settings.celery_result_expires_seconds,
    beat_schedule={
        "abandon-stale-sessions": {
            "task": "app.workers.tasks.abandon_stale_sessions",
            "schedule": float(settings.celery_cleanup_interval_seconds),
        },
    },
)
