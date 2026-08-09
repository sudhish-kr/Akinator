from dataclasses import dataclass, field
from uuid import UUID

from app.engine.constants import Answer


@dataclass(frozen=True)
class CharacterRef:
    id: UUID
    name: str


@dataclass(frozen=True)
class QuestionRef:
    id: UUID
    text: str
    category: str | None = None


@dataclass
class LikelihoodEntry:
    """Stored L(C, Q) with sample size for cold-start smoothing."""

    likelihood: float
    sample_size: int = 0


@dataclass
class ConfidenceResult:
    should_guess: bool
    confidence: float
    margin: float
    top_character_id: UUID | None
    second_character_id: UUID | None
    reason: str | None = None


@dataclass
class GameEngineState:
    """In-memory session state for the guessing engine."""

    character_ids: list[UUID]
    probabilities: dict[UUID, float]
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry]
    used_question_ids: set[UUID] = field(default_factory=set)
    asked_question_order: list[UUID] = field(default_factory=list)
    questions_asked: int = 0
    consecutive_dont_know: int = 0
    pre_elimination_top: UUID | None = None

    def active_character_ids(self) -> list[UUID]:
        return [cid for cid in self.character_ids if cid in self.probabilities]

    def copy_probabilities(self) -> dict[UUID, float]:
        return dict(self.probabilities)


def answer_from_str(value: str) -> Answer:
    try:
        return Answer(value)
    except ValueError as exc:
        raise ValueError(
            f"Invalid answer '{value}'. Must be one of: "
            + ", ".join(a.value for a in Answer)
        ) from exc
