"""Rate-limit policy — defaults from Settings, runtime overrides for admins."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields

from app.config import settings


@dataclass
class RateLimitPolicy:
    """Limits apply per rolling window (seconds)."""

    enabled: bool = True

    auth_ip_limit: int = 20
    auth_ip_window_seconds: int = 60
    auth_user_limit: int = 40
    auth_user_window_seconds: int = 60

    game_ip_limit: int = 120
    game_ip_window_seconds: int = 60
    game_user_limit: int = 180
    game_user_window_seconds: int = 60

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict | None) -> RateLimitPolicy:
        base = cls.from_settings()
        if not data:
            return base
        allowed = {f.name for f in fields(cls)}
        updates = {k: v for k, v in data.items() if k in allowed}
        merged = {**base.to_dict(), **updates}
        return cls(**merged)

    @classmethod
    def from_settings(cls) -> RateLimitPolicy:
        return cls(
            enabled=settings.rate_limit_enabled,
            auth_ip_limit=settings.rate_limit_auth_ip,
            auth_ip_window_seconds=settings.rate_limit_auth_ip_window,
            auth_user_limit=settings.rate_limit_auth_user,
            auth_user_window_seconds=settings.rate_limit_auth_user_window,
            game_ip_limit=settings.rate_limit_game_ip,
            game_ip_window_seconds=settings.rate_limit_game_ip_window,
            game_user_limit=settings.rate_limit_game_user,
            game_user_window_seconds=settings.rate_limit_game_user_window,
        )
