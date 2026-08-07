"""Rate limiter service — per-IP and per-user checks for auth/game scopes."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import redis

from app.config import settings
from app.security.rate_limit_backend import (
    MemoryRateLimitBackend,
    RateLimitBackend,
    RateLimitResult,
    RedisRateLimitBackend,
)
from app.security.rate_limit_policy import RateLimitPolicy

logger = logging.getLogger("mindguess.ratelimit")

_CONFIG_KEY = "rate_limit:policy"


@dataclass
class RateLimitDecision:
    allowed: bool
    results: list[RateLimitResult]

    @property
    def retry_after_seconds(self) -> int:
        blocked = [r for r in self.results if not r.allowed]
        if not blocked:
            return 0
        return max(r.retry_after_seconds for r in blocked)

    @property
    def limiting_scope(self) -> str | None:
        for r in self.results:
            if not r.allowed:
                return r.scope
        return None


class RateLimiter:
    """
    Enforce auth/game rate limits.

    Policy defaults come from Settings; admins can override via Redis-backed
    (or in-memory) runtime config without changing gameplay code.
    """

    def __init__(
        self,
        backend: RateLimitBackend | None = None,
        *,
        policy: RateLimitPolicy | None = None,
        config_store: RateLimitBackend | MemoryRateLimitBackend | None = None,
        redis_client=None,
    ):
        self._backend = backend or self._default_backend(redis_client)
        self._default_policy = policy or RateLimitPolicy.from_settings()
        self._override: RateLimitPolicy | None = None
        self._redis = redis_client
        self._memory_override: dict | None = None

    @staticmethod
    def _default_backend(redis_client=None) -> RateLimitBackend:
        if redis_client is not None:
            return RedisRateLimitBackend(redis_client, key_prefix=f"{settings.redis_key_prefix}rl:")
        if not settings.rate_limit_enabled:
            return MemoryRateLimitBackend()
        try:
            client = redis.Redis.from_url(
                settings.redis_url,
                decode_responses=True,
                socket_connect_timeout=1.0,
                socket_timeout=1.0,
            )
            client.ping()
            return RedisRateLimitBackend(client, key_prefix=f"{settings.redis_key_prefix}rl:")
        except Exception:
            logger.warning("Rate-limit Redis unavailable; using in-memory counters")
            return MemoryRateLimitBackend()

    def get_policy(self) -> RateLimitPolicy:
        override = self._load_override()
        if override:
            return RateLimitPolicy.from_dict(override)
        return self._default_policy

    def set_policy(self, policy: RateLimitPolicy) -> RateLimitPolicy:
        payload = policy.to_dict()
        self._memory_override = payload
        if isinstance(self._backend, RedisRateLimitBackend):
            try:
                client = self._backend._client
                client.set(
                    f"{settings.redis_key_prefix}{_CONFIG_KEY}",
                    json.dumps(payload),
                )
            except Exception:
                logger.exception("Failed to persist rate-limit policy to Redis")
        elif self._redis is not None:
            try:
                self._redis.set(
                    f"{settings.redis_key_prefix}{_CONFIG_KEY}",
                    json.dumps(payload),
                )
            except Exception:
                logger.exception("Failed to persist rate-limit policy to Redis")
        self._override = policy
        return policy

    def _load_override(self) -> dict | None:
        if self._override is not None:
            return self._override.to_dict()
        if self._memory_override is not None:
            return self._memory_override
        client = None
        if isinstance(self._backend, RedisRateLimitBackend):
            client = self._backend._client
        elif self._redis is not None:
            client = self._redis
        if client is None:
            return None
        try:
            raw = client.get(f"{settings.redis_key_prefix}{_CONFIG_KEY}")
            if not raw:
                return None
            data = json.loads(raw)
            self._override = RateLimitPolicy.from_dict(data)
            return data
        except Exception:
            return None

    def check(
        self,
        *,
        scope: str,
        client_ip: str,
        user_id: str | None = None,
    ) -> RateLimitDecision:
        policy = self.get_policy()
        if not policy.enabled:
            return RateLimitDecision(allowed=True, results=[])

        results: list[RateLimitResult] = []

        if scope == "auth":
            results.append(
                self._backend.hit(
                    f"auth:ip:{client_ip}",
                    policy.auth_ip_limit,
                    policy.auth_ip_window_seconds,
                )
            )
            if user_id:
                results.append(
                    self._backend.hit(
                        f"auth:user:{user_id}",
                        policy.auth_user_limit,
                        policy.auth_user_window_seconds,
                    )
                )
        elif scope == "game":
            results.append(
                self._backend.hit(
                    f"game:ip:{client_ip}",
                    policy.game_ip_limit,
                    policy.game_ip_window_seconds,
                )
            )
            if user_id:
                results.append(
                    self._backend.hit(
                        f"game:user:{user_id}",
                        policy.game_user_limit,
                        policy.game_user_window_seconds,
                    )
                )
        else:
            return RateLimitDecision(allowed=True, results=[])

        allowed = all(r.allowed for r in results)
        return RateLimitDecision(allowed=allowed, results=results)


# Process singleton used by middleware / admin routes
rate_limiter = RateLimiter()
