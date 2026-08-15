"""HTTP middleware — rate-limit /auth and /game without touching gameplay."""

from __future__ import annotations

import logging
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.security.rate_limiter import RateLimiter, rate_limiter

logger = logging.getLogger("mindguess.ratelimit")


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip() or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def optional_user_id_from_request(request: Request) -> str | None:
    """Decode JWT subject when present — never rejects invalid tokens here."""
    auth = request.headers.get("authorization")
    if not auth or not auth.lower().startswith("bearer "):
        return None
    token = auth.split(" ", 1)[1].strip()
    if not token:
        return None
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": False},
        )
        sub = payload.get("sub")
        return str(sub) if sub else None
    except JWTError:
        return None


def resolve_scope(path: str) -> str | None:
    if path.startswith("/auth"):
        return "auth"
    if path.startswith("/game"):
        return "game"
    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limiter: RateLimiter | None = None):
        super().__init__(app)
        self._limiter_override = limiter

    def _limiter(self) -> RateLimiter:
        # Resolve at request time so tests can patch the module singleton.
        return self._limiter_override or rate_limiter

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        scope = resolve_scope(request.url.path)
        if scope is None:
            return await call_next(request)

        ip = client_ip(request)
        user_id = optional_user_id_from_request(request)
        decision = self._limiter().check(scope=scope, client_ip=ip, user_id=user_id)

        if not decision.allowed:
            retry = decision.retry_after_seconds
            logger.warning(
                "Rate limit exceeded scope=%s ip=%s user=%s retry=%s",
                scope,
                ip,
                user_id,
                retry,
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "scope": decision.limiting_scope,
                    "retry_after_seconds": retry,
                },
                headers={
                    "Retry-After": str(retry),
                    "X-RateLimit-Scope": decision.limiting_scope or scope,
                },
            )

        response = await call_next(request)
        if decision.results:
            remaining = min(r.remaining for r in decision.results)
            limit = min(r.limit for r in decision.results)
            response.headers["X-RateLimit-Limit"] = str(limit)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response
