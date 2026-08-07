"""Enqueue helpers — keep FastAPI handlers non-blocking."""

from __future__ import annotations

from uuid import UUID

from celery.result import AsyncResult

from app.workers.tasks import process_analytics, process_learning


def enqueue_learning(
    session_id: UUID,
    character_id: UUID,
    *,
    wrong_guess: bool = False,
    distinguishing_question_id: UUID | None = None,
    distinguishing_answer: str | None = None,
) -> AsyncResult:
    return process_learning.delay(
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
    return process_analytics.delay(
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
