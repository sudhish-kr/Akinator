from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from app.cache.backend import CacheBackend
from app.cache.memory import MemoryCache
from app.config import settings
from app.engine.models import GameEngineState, QuestionRef


@dataclass(frozen=True)
class StoredAnswer:
    """One user answer recorded during the session."""

    question_id: UUID
    answer: str


@dataclass
class LiveSession:
    """In-memory game session state. Source of truth is the game_answers log;
    this object is rebuilt from it on cache miss (see docs/ARCHITECTURE.md)."""

    session_id: UUID
    engine: GameEngineState
    question_refs: dict[UUID, QuestionRef]
    character_names: dict[UUID, str]
    all_question_ids: list[UUID]
    pending_question_id: UUID | None = None
    last_answered_question_id: UUID | None = None
    awaiting_guess: bool = False
    answers: list[StoredAnswer] = field(default_factory=list)
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class SessionStore:
    """Cache-backed session manager. Swap MemoryCache for Redis via the
    CacheBackend protocol without touching call sites."""

    def __init__(self, cache: CacheBackend | None = None, ttl_minutes: int | None = None):
        self._cache = cache or MemoryCache()
        self._ttl_seconds = (ttl_minutes or settings.session_abandon_minutes) * 60

    @staticmethod
    def _key(session_id: UUID) -> str:
        return f"session:{session_id}"

    def save(self, session: LiveSession) -> None:
        session.last_activity_at = datetime.now(timezone.utc)
        self._cache.set(self._key(session.session_id), session, self._ttl_seconds)

    def get(self, session_id: UUID) -> LiveSession | None:
        return self._cache.get(self._key(session_id))

    def delete(self, session_id: UUID) -> None:
        self._cache.delete(self._key(session_id))

    def purge_expired(self) -> int:
        return self._cache.purge_expired()


# Singleton for the FastAPI process
session_store = SessionStore()
