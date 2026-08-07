"""Async helpers shared by Celery tasks (sync worker entrypoints)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import TypeVar
from uuid import UUID

from app.db.repositories.game_repository import GameRepository
from app.db.session import async_session_factory
from app.services.learning_service import LearningService
from app.workers.session_cleanup import abandon_stale_sessions_once

T = TypeVar("T")


def run_async(coro: Awaitable[T]) -> T:
    """Run an async coroutine from a sync Celery worker process.

    When Celery runs in eager mode inside FastAPI's event loop, asyncio.run()
    is unsafe — execute the coroutine on a dedicated thread instead.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)

    import concurrent.futures

    def _runner() -> T:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(_runner).result()


async def _with_repo(fn: Callable[[GameRepository], Awaitable[T]]) -> T:
    async with async_session_factory() as db:
        repo = GameRepository(db)
        result = await fn(repo)
        await repo.commit()
        return result


async def run_learning_correct(session_id: UUID, character_id: UUID) -> int:
    async def _inner(repo: GameRepository) -> int:
        return await LearningService(repo).learn_from_session(session_id, character_id)

    return await _with_repo(_inner)


async def run_learning_wrong(
    session_id: UUID,
    character_id: UUID,
    distinguishing_question_id: UUID | None = None,
    distinguishing_answer: str | None = None,
) -> int:
    async def _inner(repo: GameRepository) -> int:
        return await LearningService(repo).learn_from_wrong_guess(
            session_id,
            character_id,
            distinguishing_question_id=distinguishing_question_id,
            distinguishing_answer=distinguishing_answer,
        )

    return await _with_repo(_inner)


async def run_analytics_guess_outcome(
    *,
    guessed_character_id: UUID | None,
    actual_character_id: UUID | None,
    correct: bool,
) -> dict:
    """Update denormalized guess counters used by the analytics dashboard."""

    async def _inner(repo: GameRepository) -> dict:
        updated = {"correct": 0, "incorrect": 0}
        if correct and (guessed_character_id or actual_character_id):
            target = guessed_character_id or actual_character_id
            char = await repo.get_character(target)  # type: ignore[arg-type]
            if char:
                char.times_guessed_correctly += 1
                updated["correct"] = 1
        elif not correct and guessed_character_id:
            char = await repo.get_character(guessed_character_id)
            if char:
                char.times_guessed_incorrectly += 1
                updated["incorrect"] = 1
        return updated

    return await _with_repo(_inner)


async def run_analytics_question_ig(session_id: UUID) -> int:
    """Refresh rolling average information-gain stats from a finished session."""

    async def _inner(repo: GameRepository) -> int:
        answers = await repo.get_session_answers(session_id)
        updated = 0
        for i, game_answer in enumerate(answers):
            if game_answer.entropy_before is None or i + 1 >= len(answers):
                continue
            next_entropy = answers[i + 1].entropy_before
            if next_entropy is None:
                continue
            actual_gain = game_answer.entropy_before - next_entropy
            await repo.update_question_avg_ig(game_answer.question_id, actual_gain)
            updated += 1
        return updated

    return await _with_repo(_inner)


async def run_abandon_stale() -> int:
    return await abandon_stale_sessions_once()
