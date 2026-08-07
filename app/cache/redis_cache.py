"""Redis cache backend — shared session storage across API instances."""

from __future__ import annotations

import json
from typing import Any

import redis


class RedisCache:
    """
    JSON-valued Redis cache with native key TTL.

    Multiple FastAPI / uvicorn workers share the same Redis instance so live
    sessions stay coherent without sticky routing. Expired keys are removed by
    Redis automatically — purge_expired is a no-op compatibility shim.
    """

    def __init__(
        self,
        url: str = "redis://localhost:6379/0",
        *,
        key_prefix: str = "mindguess:",
        client: redis.Redis | None = None,
    ):
        self._url = url
        self._key_prefix = key_prefix
        self._client = client or redis.Redis.from_url(
            url,
            decode_responses=True,
            socket_connect_timeout=2.0,
            socket_timeout=2.0,
        )

    def _full_key(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    def get(self, key: str) -> Any | None:
        raw = self._client.get(self._full_key(key))
        if raw is None:
            return None
        return json.loads(raw)

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        payload = json.dumps(value)
        full = self._full_key(key)
        if ttl_seconds is not None and ttl_seconds > 0:
            # Redis EX requires an integer second count
            self._client.set(full, payload, ex=max(1, int(ttl_seconds)))
        else:
            self._client.set(full, payload)

    def delete(self, key: str) -> None:
        self._client.delete(self._full_key(key))

    def purge_expired(self) -> int:
        """Redis expires keys natively; nothing to scan client-side."""
        return 0

    def ttl(self, key: str) -> int:
        """Remaining TTL in seconds (-1 no expiry, -2 missing)."""
        return int(self._client.ttl(self._full_key(key)))

    def ping(self) -> bool:
        return bool(self._client.ping())
