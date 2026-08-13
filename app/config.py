from pydantic_settings import BaseSettings, SettingsConfigDict


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

    # Comma-separated browser origins allowed to call the API (CORS).
    # In development, vite may bump past 5173 — see cors_origin_list.
    cors_origins: str = (
        "http://127.0.0.1:5173,http://localhost:5173,"
        "http://127.0.0.1:5174,http://localhost:5174,"
        "http://127.0.0.1:5175,http://localhost:5175"
    )

    # Engine thresholds (TDD v1.1)
    elimination_floor: float = 0.0005
    elimination_magnitude: float = 1000.0
    confidence_high: float = 0.88
    confidence_separation: float = 0.72
    confidence_margin: float = 0.28
    max_questions: int = 25
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
    def cors_origin_list(self) -> list[str]:
        """Configured CORS origins.

        In local development Vite often moves to 5174/5175 when 5173 is busy.
        Expand localhost Vite ports automatically without using allow_origins=['*'].
        Production uses only the explicit CORS_ORIGINS list.
        """
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        if self.environment.lower() in {"development", "dev", "local", "test"}:
            for host in ("http://localhost", "http://127.0.0.1"):
                for port in range(5173, 5181):
                    candidate = f"{host}:{port}"
                    if candidate not in origins:
                        origins.append(candidate)
        return origins


settings = Settings()
