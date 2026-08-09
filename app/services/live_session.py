"""Live game session dataclasses (shared by SessionStore and Redis codec)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from uuid import UUID

from app.engine.models import GameEngineState, QuestionRef


@dataclass(frozen=True)
class StoredAnswer:
    """One user answer recorded during the session."""

    question_id: UUID
    answer: str


@dataclass
class LiveSession:
    """Cached game session state. Source of truth remains the game_answers log;
    this object is rebuilt from it on cache miss (see docs/ARCHITECTURE.md)."""

    session_id: UUID
    engine: GameEngineState
    question_refs: dict[UUID, QuestionRef]
    character_names: dict[UUID, str]
    all_question_ids: list[UUID]
    character_categories: dict[UUID, str] = field(default_factory=dict)
    character_popularity: dict[UUID, int] = field(default_factory=dict)
    pending_question_id: UUID | None = None
    last_answered_question_id: UUID | None = None
    awaiting_guess: bool = False
    answers: list[StoredAnswer] = field(default_factory=list)
    last_activity_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
