"""Cache backend factory for session storage."""

from __future__ import annotations

from app.cache.backend import CacheBackend
from app.cache.memory import MemoryCache
from app.cache.redis_cache import RedisCache


def build_cache_backend(
    backend: str | None = None,
    *,
    redis_url: str | None = None,
    redis_key_prefix: str | None = None,
    redis_client=None,
) -> CacheBackend:
    """
    Build the configured session cache backend.

    backend: "redis" (default) or "memory" (local/dev fallback).
    redis_client: optional injected client (fakeredis in tests).
    """
    # Lazy import so unit tests that only need LiveSession / SessionManager
    # do not require full Settings (JWT_SECRET) at collection time.
    from app.config import settings

    name = (backend or settings.session_cache_backend).strip().lower()
    if name == "memory":
        return MemoryCache()
    if name == "redis":
        cache = RedisCache(
            redis_url or settings.redis_url,
            key_prefix=redis_key_prefix or settings.redis_key_prefix,
            client=redis_client,
        )
        if redis_client is None:
            try:
                cache.ping()
            except Exception:
                if settings.debug or settings.environment in {"development", "test"}:
                    return MemoryCache()
                raise
        return cache
    raise ValueError(f"Unknown session cache backend: {name!r}")
