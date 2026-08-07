"""Fixed-window counters — Redis when available, in-memory fallback."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int
    scope: str  # "ip" | "user"
    key: str


class RateLimitBackend(Protocol):
    def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitResult: ...

    def reset(self, key: str) -> None: ...


class MemoryRateLimitBackend:
    """Process-local fixed-window counter (tests / Redis-unavailable fallback)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        # key -> (window_start_epoch, count)
        self._windows: dict[str, tuple[float, int]] = {}

    def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        now = time.time()
        with self._lock:
            start, count = self._windows.get(key, (now, 0))
            if now - start >= window_seconds:
                start, count = now, 0
            count += 1
            self._windows[key] = (start, count)
            retry_after = max(1, int(window_seconds - (now - start)))
            allowed = count <= limit
            remaining = max(0, limit - count)
            return RateLimitResult(
                allowed=allowed,
                limit=limit,
                remaining=remaining,
                retry_after_seconds=0 if allowed else retry_after,
                scope="ip" if ":ip:" in key else "user",
                key=key,
            )

    def reset(self, key: str) -> None:
        with self._lock:
            self._windows.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._windows.clear()


class RedisRateLimitBackend:
    """Shared fixed-window counter via Redis INCR + EXPIRE."""

    def __init__(self, client, *, key_prefix: str = "mindguess:rl:"):
        self._client = client
        self._key_prefix = key_prefix

    def _full(self, key: str) -> str:
        return f"{self._key_prefix}{key}"

    def hit(self, key: str, limit: int, window_seconds: int) -> RateLimitResult:
        full = self._full(key)
        pipe = self._client.pipeline()
        pipe.incr(full)
        pipe.ttl(full)
        count, ttl = pipe.execute()
        if ttl is None or ttl < 0:
            self._client.expire(full, max(1, int(window_seconds)))
            ttl = int(window_seconds)
        allowed = int(count) <= limit
        remaining = max(0, limit - int(count))
        return RateLimitResult(
            allowed=allowed,
            limit=limit,
            remaining=remaining,
            retry_after_seconds=0 if allowed else max(1, int(ttl)),
            scope="ip" if ":ip:" in key else "user",
            key=key,
        )

    def reset(self, key: str) -> None:
        self._client.delete(self._full(key))
