import re

from pydantic_settings import BaseSettings, SettingsConfigDict

# Vite starts at 5173 and increments when the port is busy. Development only.
# Never used in production — production reads CORS_ORIGINS exclusively.
DEV_VITE_ORIGIN_REGEX = r"^https?://(localhost|127\.0\.0\.1):(517[3-9]|51[89]\d)$"
_DEV_ENVIRONMENTS = frozenset({"development", "dev", "local", "test"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MindGuess AI"
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://mindguess:mindguess@localhost:5432/mindguess"

    # Required via JWT_SECRET — no default; startup fails if missing
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # Explicit CORS origins (comma-separated). Production uses this list only.
    # Development also allows localhost Vite ports 5173–5199 via regex
    # (see cors_allow_origin_regex) so Vite can bump ports without a code change.
    cors_origins: str = "http://127.0.0.1:5173,http://localhost:5173,https://mindguess.netlify.app"

    # Engine thresholds (TDD v1.1)
    elimination_floor: float = 0.0005
    elimination_magnitude: float = 1000.0
    confidence_high: float = 0.88
    confidence_separation: float = 0.72
    confidence_margin: float = 0.28
    max_questions: int = 20
    learning_rate: float = 0.07
    consecutive_dont_know_cap: int = 5
    ig_tie_threshold: float = 0.001
    session_abandon_minutes: int = 30
    new_question_min_samples: int = 5

    # Live session cache — Redis shared across workers; "memory" for local-only
    session_cache_backend: str = "redis"
    redis_url: str = "redis://localhost:6379/0"
    redis_key_prefix: str = "mindguess:"

    # Celery background workers (broker defaults to redis_url)
    celery_broker_url: str | None = None
    celery_result_backend: str | None = None
    celery_task_always_eager: bool = False
    celery_task_max_retries: int = 5
    celery_retry_delay_seconds: int = 5
    celery_result_expires_seconds: int = 86400
    celery_cleanup_interval_seconds: int = 300

    # Rate limiting (auth + game). Admins can override at runtime via API.
    rate_limit_enabled: bool = True
    rate_limit_auth_ip: int = 20
    rate_limit_auth_ip_window: int = 60
    rate_limit_auth_user: int = 40
    rate_limit_auth_user_window: int = 60
    rate_limit_game_ip: int = 120
    rate_limit_game_ip_window: int = 60
    rate_limit_game_user: int = 180
    rate_limit_game_user_window: int = 60

    @property
    def is_development(self) -> bool:
        return self.environment.strip().lower() in _DEV_ENVIRONMENTS

    @property
    def cors_origin_list(self) -> list[str]:
        """Explicit allowed origins from CORS_ORIGINS. Never includes '*'."""
        origins: list[str] = []
        for origin in self.cors_origins.split(","):
            value = origin.strip()
            if not value or value == "*":
                continue
            if value not in origins:
                origins.append(value)
        return origins

    @property
    def cors_allow_origin_regex(self) -> str | None:
        """Local Vite origins in development only. None in production."""
        if not self.is_development:
            return None
        return DEV_VITE_ORIGIN_REGEX

    def is_cors_origin_allowed(self, origin: str) -> bool:
        """True when Starlette CORSMiddleware would accept this Origin."""
        if origin in self.cors_origin_list:
            return True
        pattern = self.cors_allow_origin_regex
        if pattern and re.fullmatch(pattern, origin):
            return True
        return False


settings = Settings()
