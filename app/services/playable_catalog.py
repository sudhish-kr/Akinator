"""Process-level cache of active characters, questions, and likelihoods.

Gameplay must NOT reload ~1M likelihood rows from SQLite/Postgres or Redis on
every /game/start or /game/answer. The catalog is read-mostly; learning updates
the DB asynchronously and callers can invalidate() when mappings change.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from uuid import UUID

from app.engine.models import LikelihoodEntry, QuestionRef

logger = logging.getLogger(__name__)

# Refresh automatically after this many seconds (learning may have landed).
DEFAULT_TTL_SECONDS = 300.0


@dataclass
class PlayableCatalog:
    character_ids: list[UUID]
    question_ids: list[UUID]
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry]
    question_refs: dict[UUID, QuestionRef]
    character_names: dict[UUID, str]
    character_categories: dict[UUID, str]
    character_popularity: dict[UUID, int]
    loaded_at: float = field(default_factory=time.monotonic)
    character_count: int = 0
    question_count: int = 0
    likelihood_count: int = 0
    db_identity: int = 0

    def is_fresh(self, ttl_seconds: float = DEFAULT_TTL_SECONDS) -> bool:
        return (time.monotonic() - self.loaded_at) < ttl_seconds


_catalog: PlayableCatalog | None = None
_lock = asyncio.Lock()


def _db_identity(repo) -> int:
    """Distinguish engines (critical for sqlite :memory: test isolation)."""
    try:
        bind = repo.db.get_bind()
        return id(bind)
    except Exception:
        return 0


def peek_catalog() -> PlayableCatalog | None:
    """Non-blocking access to the warm catalog (may be None / stale)."""
    return _catalog


def peek_likelihoods() -> dict[tuple[UUID, UUID], LikelihoodEntry] | None:
    cat = _catalog
    if cat is None:
        return None
    return cat.likelihoods


def invalidate_playable_catalog() -> None:
    """Drop the cache so the next request reloads from the DB."""
    global _catalog
    _catalog = None
    logger.info("playable_catalog_invalidated")


async def get_playable_catalog(repo, *, ttl_seconds: float = DEFAULT_TTL_SECONDS) -> PlayableCatalog:
    """Return a warm catalog, loading from DB at most once per TTL window."""
    global _catalog
    identity = _db_identity(repo)
    current = _catalog
    if (
        current is not None
        and current.is_fresh(ttl_seconds)
        and current.db_identity == identity
    ):
        return current

    async with _lock:
        current = _catalog
        if (
            current is not None
            and current.is_fresh(ttl_seconds)
            and current.db_identity == identity
        ):
            return current
        started = time.perf_counter()
        loaded = await _load_catalog(repo, identity=identity)
        _catalog = loaded
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "playable_catalog_loaded characters=%s questions=%s likelihoods=%s elapsed_ms=%.1f",
            loaded.character_count,
            loaded.question_count,
            loaded.likelihood_count,
            elapsed_ms,
        )
        return loaded


async def _load_catalog(repo, *, identity: int) -> PlayableCatalog:
    characters = await repo.get_active_characters()
    questions = await repo.get_active_questions()
    if not characters:
        raise ValueError("No active characters available")
    if not questions:
        raise ValueError("No active questions available")

    character_ids = [c.id for c in characters]
    question_ids = [q.id for q in questions]
    rows = await repo.get_likelihoods(character_ids, question_ids)
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry] = {
        (row.character_id, row.question_id): LikelihoodEntry(
            likelihood=row.likelihood,
            sample_size=row.sample_size,
        )
        for row in rows
    }
    return PlayableCatalog(
        character_ids=character_ids,
        question_ids=question_ids,
        likelihoods=likelihoods,
        question_refs={
            q.id: QuestionRef(id=q.id, text=q.text, category=q.category) for q in questions
        },
        character_names={c.id: c.name for c in characters},
        character_categories={c.id: c.category for c in characters},
        character_popularity={
            c.id: int(getattr(c, "popularity_score", 0) or 0) for c in characters
        },
        character_count=len(character_ids),
        question_count=len(question_ids),
        likelihood_count=len(likelihoods),
        db_identity=identity,
    )
