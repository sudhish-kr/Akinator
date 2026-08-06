from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "MindGuess AI"
    debug: bool = False
    environment: str = "development"
    log_level: str = "INFO"

    database_url: str = "postgresql+asyncpg://mindguess:mindguess@localhost:5432/mindguess"

    # Required via JWT_SECRET — no default; startup fails if missing/empty
    jwt_secret: str = Field(min_length=1)
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 7

    # Engine thresholds (TDD v1.1)
    elimination_floor: float = 0.0005
    elimination_magnitude: float = 1000.0
    confidence_high: float = 0.85
    confidence_separation: float = 0.6
    confidence_margin: float = 0.4
    max_questions: int = 25
    learning_rate: float = 0.07
    consecutive_dont_know_cap: int = 5
    ig_tie_threshold: float = 0.001
    session_abandon_minutes: int = 30
    new_question_min_samples: int = 5


settings = Settings()
