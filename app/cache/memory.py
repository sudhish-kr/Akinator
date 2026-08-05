import time
from typing import Any


class MemoryCache:
    """TTL in-memory cache. Correctness under multi-worker deployments comes
    from session rehydration (see docs/ARCHITECTURE.md), not from this cache."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, float | None]] = {}

    def get(self, key: str) -> Any | None:
        entry = self._data.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at is not None and time.monotonic() > expires_at:
            del self._data[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        expires_at = time.monotonic() + ttl_seconds if ttl_seconds else None
        self._data[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def purge_expired(self) -> int:
        now = time.monotonic()
        expired = [k for k, (_, exp) in self._data.items() if exp is not None and now > exp]
        for key in expired:
            del self._data[key]
        return len(expired)
