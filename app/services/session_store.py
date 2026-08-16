"""Cache-backed live session storage (Redis by default)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.cache.backend import CacheBackend
from app.cache.session_codec import decode_live_session, encode_live_session
from app.services.live_session import LiveSession, StoredAnswer

# Re-export for existing call sites (GameService, tests)
__all__ = ["LiveSession", "StoredAnswer", "SessionStore", "session_store"]


class SessionStore:
    """Cache-backed session store. API unchanged: save / get / delete / purge_expired.

    Default backend is Redis so multiple API instances share live sessions.
    Values are JSON-encoded for cross-process portability; Redis TTL provides
    automatic session expiration.

    Likelihood matrices are NEVER written to Redis — they live in the process
    PlayableCatalog and are re-attached on get. This keeps /game/answer fast.
    """

    def __init__(
        self,
        cache: CacheBackend | None = None,
        ttl_minutes: int | None = None,
        *,
        ttl_seconds: int | None = None,
    ):
        if cache is not None:
            self._cache = cache
        else:
            from app.cache.factory import build_cache_backend

            self._cache = build_cache_backend()

        if ttl_seconds is not None:
            self._ttl_seconds = max(1, int(ttl_seconds))
        elif ttl_minutes is not None:
            self._ttl_seconds = max(1, int(ttl_minutes) * 60)
        else:
            from app.config import settings

            self._ttl_seconds = settings.session_abandon_minutes * 60

    @staticmethod
    def _key(session_id: UUID) -> str:
        return f"session:{session_id}"

    def save(self, session: LiveSession) -> None:
        session.last_activity_at = datetime.now(timezone.utc)
        # Compact payload — no likelihood blob, no catalog copies (reattached on get).
        self._cache.set(
            self._key(session.session_id),
            encode_live_session(session, include_likelihoods=False, include_catalog=False),
            self._ttl_seconds,
        )

    def get(self, session_id: UUID) -> LiveSession | None:
        payload = self._cache.get(self._key(session_id))
        if payload is None:
            return None
        if isinstance(payload, LiveSession):
            return payload
        live = decode_live_session(payload)
        from app.services.playable_catalog import peek_catalog

        catalog = peek_catalog()
        if catalog:
            if not live.engine.likelihoods:
                live.engine.likelihoods = catalog.likelihoods
            if live.engine.question_sample_totals is None:
                live.engine.question_sample_totals = catalog.question_sample_totals
            if not live.question_refs:
                live.question_refs = catalog.question_refs
            if not live.character_names:
                live.character_names = catalog.character_names
            if not live.character_categories:
                live.character_categories = catalog.character_categories
            if not live.character_popularity:
                live.character_popularity = catalog.character_popularity
            if not live.all_question_ids:
                live.all_question_ids = catalog.question_ids
        return live

    def delete(self, session_id: UUID) -> None:
        self._cache.delete(self._key(session_id))
        # Legacy sibling key from older builds — best-effort cleanup.
        self._cache.delete(f"session:{session_id}:likelihoods")

    def purge_expired(self) -> int:
        return self._cache.purge_expired()


def _default_session_store() -> SessionStore:
    return SessionStore()


# Process singleton — shared Redis URL → coherent multi-worker sessions
try:
    session_store = SessionStore()
except Exception:
    from app.cache.memory import MemoryCache

    session_store = SessionStore(cache=MemoryCache(), ttl_minutes=30)
