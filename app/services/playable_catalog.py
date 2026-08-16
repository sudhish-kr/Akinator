"""Process-level cache of active characters, questions, and likelihoods.

Gameplay must NOT reload hundreds of thousands of likelihood rows from
Postgres/SQLite or Redis on every /game/start or /game/answer. The catalog is
read-mostly; learning updates the DB asynchronously and callers can
invalidate() when mappings change.

Production note: the full CharacterAnswer table (~characters × questions for
each category rule) is too large to materialize twice in RAM on a small Render
instance. Load is deferred until first gameplay request and streamed in batches.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from uuid import UUID

from app.engine.models import LikelihoodEntry, QuestionRef

logger = logging.getLogger(__name__)

# Fallback when Settings is unavailable. Learning invalidates explicitly;
# a 5-minute TTL caused periodic full-table reloads (Render exit 137).
DEFAULT_TTL_SECONDS = 3600.0


@dataclass
class PlayableCatalog:
    character_ids: list[UUID]
    question_ids: list[UUID]
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry]
    question_refs: dict[UUID, QuestionRef]
    character_names: dict[UUID, str]
    character_categories: dict[UUID, str]
    character_popularity: dict[UUID, int]
    question_sample_totals: dict[UUID, int] = field(default_factory=dict)
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


def _catalog_ttl_seconds(override: float | None) -> float:
    if override is not None:
        return override
    try:
        from app.config import settings

        return float(settings.playable_catalog_ttl_seconds)
    except Exception:
        return DEFAULT_TTL_SECONDS


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


def _as_uuid(value) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def _intern_uuid(cache: dict[UUID, UUID], value) -> UUID:
    """Reuse one UUID object per id so the likelihood dict does not clone millions."""
    key = value if isinstance(value, UUID) else UUID(str(value))
    existing = cache.get(key)
    if existing is not None:
        return existing
    cache[key] = key
    return key


async def get_playable_catalog(
    repo, *, ttl_seconds: float | None = None
) -> PlayableCatalog:
    """Return a warm catalog, loading from DB at most once per TTL window."""
    global _catalog
    ttl = _catalog_ttl_seconds(ttl_seconds)
    identity = _db_identity(repo)
    current = _catalog
    if (
        current is not None
        and current.is_fresh(ttl)
        and current.db_identity == identity
    ):
        return current

    async with _lock:
        current = _catalog
        if (
            current is not None
            and current.is_fresh(ttl)
            and current.db_identity == identity
        ):
            return current
        started = time.perf_counter()
        logger.info("playable_catalog_loading")
        loaded = await _load_catalog(repo, identity=identity)
        _catalog = loaded
        elapsed_ms = (time.perf_counter() - started) * 1000
        logger.info(
            "playable_catalog_loaded characters=%s questions=%s likelihoods=%s "
            "elapsed_ms=%.1f ttl_seconds=%.0f",
            loaded.character_count,
            loaded.question_count,
            loaded.likelihood_count,
            elapsed_ms,
            ttl,
        )
        return loaded


async def _iter_likelihood_rows(repo):
    iterator = getattr(repo, "iter_active_likelihood_rows", None)
    if iterator is not None:
        async for row in iterator():
            yield row
        return
    rows = await repo.get_active_likelihood_rows()
    for row in rows:
        yield row


async def _load_catalog(repo, *, identity: int) -> PlayableCatalog:
    characters = await repo.get_active_characters()
    questions = await repo.get_active_questions()
    if not characters:
        raise ValueError("No active characters available")
    if not questions:
        raise ValueError("No active questions available")

    intern: dict[UUID, UUID] = {}
    character_ids = [_intern_uuid(intern, c.id) for c in characters]
    question_ids = [_intern_uuid(intern, q.id) for q in questions]

    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry] = {}
    sample_totals: dict[UUID, int] = {}
    async for character_id, question_id, likelihood, sample_size in _iter_likelihood_rows(
        repo
    ):
        cid = _intern_uuid(intern, character_id)
        qid = _intern_uuid(intern, question_id)
        n = int(sample_size)
        likelihoods[(cid, qid)] = LikelihoodEntry(
            likelihood=float(likelihood),
            sample_size=n,
        )
        sample_totals[qid] = sample_totals.get(qid, 0) + n

    return PlayableCatalog(
        character_ids=character_ids,
        question_ids=question_ids,
        likelihoods=likelihoods,
        question_refs={
            _intern_uuid(intern, q.id): QuestionRef(
                id=_intern_uuid(intern, q.id), text=q.text, category=q.category
            )
            for q in questions
        },
        character_names={_intern_uuid(intern, c.id): c.name for c in characters},
        character_categories={_intern_uuid(intern, c.id): c.category for c in characters},
        character_popularity={
            _intern_uuid(intern, c.id): int(getattr(c, "popularity_score", 0) or 0)
            for c in characters
        },
        question_sample_totals=sample_totals,
        character_count=len(character_ids),
        question_count=len(question_ids),
        likelihood_count=len(likelihoods),
        db_identity=identity,
    )
