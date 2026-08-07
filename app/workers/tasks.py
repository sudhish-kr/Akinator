"""Celery tasks — learning, analytics, and maintenance (with retries)."""

from __future__ import annotations

import logging
from uuid import UUID

from app.config import settings
from app.workers.async_jobs import (
    run_abandon_stale,
    run_analytics_guess_outcome,
    run_analytics_question_ig,
    run_async,
    run_learning_correct,
    run_learning_wrong,
)
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

_RETRY = {
    "autoretry_for": (Exception,),
    "retry_backoff": True,
    "retry_backoff_max": 600,
    "retry_jitter": True,
    "retry_kwargs": {"max_retries": None},  # patched after settings load
}


def _max_retries() -> int:
    return settings.celery_task_max_retries


@celery_app.task(
    bind=True,
    name="app.workers.tasks.process_learning",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def process_learning(
    self,
    session_id: str,
    character_id: str,
    wrong_guess: bool = False,
    distinguishing_question_id: str | None = None,
    distinguishing_answer: str | None = None,
) -> dict:
    """Apply post-game learning updates to the knowledge base."""
    # Celery binds max_retries from decorator; keep in sync with settings when possible
    self.max_retries = _max_retries()
    sid = UUID(session_id)
    cid = UUID(character_id)
    dist_q = UUID(distinguishing_question_id) if distinguishing_question_id else None
    if wrong_guess:
        updates = run_async(run_learning_wrong(sid, cid, dist_q, distinguishing_answer))
    else:
        updates = run_async(run_learning_correct(sid, cid))
    logger.info(
        "Learning job done session=%s character=%s updates=%s wrong=%s",
        session_id,
        character_id,
        updates,
        wrong_guess,
    )
    return {"session_id": session_id, "updates": updates, "wrong_guess": wrong_guess}


@celery_app.task(
    bind=True,
    name="app.workers.tasks.process_analytics",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_backoff_max=600,
    retry_jitter=True,
    max_retries=5,
)
def process_analytics(
    self,
    session_id: str,
    correct: bool = True,
    guessed_character_id: str | None = None,
    actual_character_id: str | None = None,
    update_question_ig: bool = True,
) -> dict:
    """Update analytics counters / question IG after a game outcome."""
    self.max_retries = _max_retries()
    sid = UUID(session_id)
    guessed = UUID(guessed_character_id) if guessed_character_id else None
    actual = UUID(actual_character_id) if actual_character_id else None
    counters = run_async(
        run_analytics_guess_outcome(
            guessed_character_id=guessed,
            actual_character_id=actual,
            correct=correct,
        )
    )
    ig_updates = 0
    if update_question_ig:
        ig_updates = run_async(run_analytics_question_ig(sid))
    logger.info(
        "Analytics job done session=%s counters=%s ig=%s",
        session_id,
        counters,
        ig_updates,
    )
    return {
        "session_id": session_id,
        "counters": counters,
        "ig_updates": ig_updates,
    }


@celery_app.task(
    bind=True,
    name="app.workers.tasks.abandon_stale_sessions",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def abandon_stale_sessions(self) -> dict:
    count = run_async(run_abandon_stale())
    return {"abandoned": count}
