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
        self._cache.set(
            self._key(session.session_id),
            encode_live_session(session),
            self._ttl_seconds,
        )

    def get(self, session_id: UUID) -> LiveSession | None:
        payload = self._cache.get(self._key(session_id))
        if payload is None:
            return None
        if isinstance(payload, LiveSession):
            return payload
        return decode_live_session(payload)

    def delete(self, session_id: UUID) -> None:
        self._cache.delete(self._key(session_id))

    def purge_expired(self) -> int:
        return self._cache.purge_expired()


def _default_session_store() -> SessionStore:
    return SessionStore()


# Process singleton — shared Redis URL → coherent multi-worker sessions
# Lazy via module attribute pattern would still need settings; construct on import
# when the app loads. Tests inject their own SessionStore(cache=...).
try:
    session_store = SessionStore()
except Exception:
    # Offline / missing JWT during isolated module import — memory store placeholder.
    # App startup with valid Settings replaces this via normal import path.
    from app.cache.memory import MemoryCache

    session_store = SessionStore(cache=MemoryCache(), ttl_minutes=30)
