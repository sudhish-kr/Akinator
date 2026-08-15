"""Enqueue helpers — keep FastAPI handlers non-blocking."""

from __future__ import annotations

import logging
from uuid import UUID

from celery.result import AsyncResult

from app.config import settings
from app.workers.tasks import process_analytics, process_learning

logger = logging.getLogger("mindguess.workers.queue")


def _broker_reachable(timeout: float = 0.4) -> bool:
    """Fast Redis ping so missing broker never hangs HTTP handlers."""
    if settings.celery_task_always_eager:
        return False
    try:
        import redis

        client = redis.Redis.from_url(
            settings.celery_broker_url or settings.redis_url,
            socket_connect_timeout=timeout,
            socket_timeout=timeout,
        )
        return bool(client.ping())
    except Exception as exc:
        logger.warning("Celery broker unreachable (%s); using in-process fallback", exc)
        return False


def _dispatch(task, *args, **kwargs) -> AsyncResult:
    """Queue via Celery when broker is up; otherwise run the task inline."""
    if settings.celery_task_always_eager:
        return task.delay(*args, **kwargs)
    if not _broker_reachable():
        return task.apply(args=args, kwargs=kwargs)
    try:
        return task.delay(*args, **kwargs)
    except Exception as exc:
        logger.warning("Celery delay failed (%s); running task inline", exc)
        return task.apply(args=args, kwargs=kwargs)


def enqueue_learning(
    session_id: UUID,
    character_id: UUID,
    *,
    wrong_guess: bool = False,
    distinguishing_question_id: UUID | None = None,
    distinguishing_answer: str | None = None,
) -> AsyncResult:
    return _dispatch(
        process_learning,
        str(session_id),
        str(character_id),
        wrong_guess=wrong_guess,
        distinguishing_question_id=(
            str(distinguishing_question_id) if distinguishing_question_id else None
        ),
        distinguishing_answer=distinguishing_answer,
    )


def enqueue_analytics(
    session_id: UUID,
    *,
    correct: bool,
    guessed_character_id: UUID | None = None,
    actual_character_id: UUID | None = None,
    update_question_ig: bool = True,
) -> AsyncResult:
    return _dispatch(
        process_analytics,
        str(session_id),
        correct=correct,
        guessed_character_id=str(guessed_character_id) if guessed_character_id else None,
        actual_character_id=str(actual_character_id) if actual_character_id else None,
        update_question_ig=update_question_ig,
    )


def enqueue_post_game(
    session_id: UUID,
    character_id: UUID,
    *,
    wrong_guess: bool,
    guessed_character_id: UUID | None = None,
    distinguishing_question_id: UUID | None = None,
    distinguishing_answer: str | None = None,
) -> dict[str, str]:
    """Queue learning + analytics; returns Celery task ids."""
    learning = enqueue_learning(
        session_id,
        character_id,
        wrong_guess=wrong_guess,
        distinguishing_question_id=distinguishing_question_id,
        distinguishing_answer=distinguishing_answer,
    )
    # Learning on correct path already updates question IG — skip duplicate IG work
    analytics = enqueue_analytics(
        session_id,
        correct=not wrong_guess,
        guessed_character_id=guessed_character_id,
        actual_character_id=character_id,
        update_question_ig=wrong_guess,
    )
    return {"learning_job_id": learning.id, "analytics_job_id": analytics.id}
