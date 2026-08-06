"""Game session manager — orchestrates one playthrough.

Reuses Bayesian update (via process_answer), question selection, and
confidence evaluation. Persistence (DB) stays in GameService.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.engine.confidence import evaluate_confidence, resolve_turn
from app.engine.constants import (
    DEFAULT_CONFIDENCE_HIGH,
    DEFAULT_CONFIDENCE_MARGIN,
    DEFAULT_CONFIDENCE_SEPARATION,
    DEFAULT_MAX_QUESTIONS,
    DEFAULT_NEW_QUESTION_MIN_SAMPLES,
    Answer,
)
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import create_initial_state, process_answer, select_next_question
from app.services.session_store import LiveSession, StoredAnswer


@dataclass
class TurnResult:
    """Outcome of submitting one answer."""

    status: str  # "asking" | "ready_to_guess"
    next_question_id: UUID | None
    questions_asked: int
    top_confidence: float
    best_guess_id: UUID | None
    entropy_before: float | None = None
    confidence_reason: str | None = None


@dataclass
class ConfidenceThresholds:
    high: float = DEFAULT_CONFIDENCE_HIGH
    separation: float = DEFAULT_CONFIDENCE_SEPARATION
    margin: float = DEFAULT_CONFIDENCE_MARGIN
    max_questions: int = DEFAULT_MAX_QUESTIONS


class GameSessionManager:
    """In-memory game loop: start → answer → select next / end → best guess."""

    def __init__(
        self,
        thresholds: ConfidenceThresholds | None = None,
        min_samples: int = DEFAULT_NEW_QUESTION_MIN_SAMPLES,
    ):
        self.thresholds = thresholds or ConfidenceThresholds()
        self.min_samples = min_samples

    def start(
        self,
        session_id: UUID,
        character_ids: list[UUID],
        likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry],
        question_ids: list[UUID],
        question_refs: dict[UUID, QuestionRef],
        character_names: dict[UUID, str],
    ) -> LiveSession:
        """Start a new session and select the first question."""
        engine = create_initial_state(character_ids, likelihoods)
        first_q = select_next_question(
            engine, question_ids, min_samples=self.min_samples
        )
        if first_q is None:
            raise ValueError("No eligible questions to start game")

        return LiveSession(
            session_id=session_id,
            engine=engine,
            question_refs=question_refs,
            character_names=character_names,
            all_question_ids=list(question_ids),
            pending_question_id=first_q,
            answers=[],
        )

    def submit_answer(
        self,
        live: LiveSession,
        question_id: UUID,
        answer: str,
    ) -> TurnResult:
        """
        Store the answer, update Bayesian state, then either fetch the next
        question or end the game (confidence threshold / no questions left).
        """
        if live.awaiting_guess:
            raise ValueError("Session is ready to guess")
        if live.pending_question_id != question_id:
            raise ValueError("Question does not match the current pending question")

        try:
            Answer(answer)
        except ValueError as exc:
            raise ValueError(
                f"Invalid answer. Must be one of: {', '.join(a.value for a in Answer)}"
            ) from exc

        engine, entropy_before = process_answer(live.engine, question_id, answer)

        live.answers.append(StoredAnswer(question_id=question_id, answer=answer))
        live.engine = engine
        live.last_answered_question_id = question_id

        # Confidence after every answer (0.0–1.0). High → guess; low → ask next.
        confidence = evaluate_confidence(
            engine,
            confidence_high=self.thresholds.high,
            confidence_separation=self.thresholds.separation,
            confidence_margin=self.thresholds.margin,
            max_questions=self.thresholds.max_questions,
        )

        next_q_id: UUID | None = None
        if not confidence.should_guess:
            next_q_id = select_next_question(
                engine, live.all_question_ids, min_samples=self.min_samples
            )
            # No useful questions left → best available guess
            confidence = resolve_turn(
                engine,
                next_question_id=next_q_id,
                confidence_high=self.thresholds.high,
                confidence_separation=self.thresholds.separation,
                confidence_margin=self.thresholds.margin,
                max_questions=self.thresholds.max_questions,
            )

        must_end = confidence.should_guess
        live.pending_question_id = None if must_end else next_q_id
        live.awaiting_guess = must_end

        best_id = self.best_guess_id(live)
        return TurnResult(
            status="ready_to_guess" if must_end else "asking",
            next_question_id=live.pending_question_id,
            questions_asked=engine.questions_asked,
            top_confidence=confidence.confidence,
            best_guess_id=best_id if must_end else None,
            entropy_before=entropy_before,
            confidence_reason=confidence.reason,
        )

    @staticmethod
    def best_guess_id(live: LiveSession) -> UUID | None:
        """Return the character id with highest posterior probability."""
        if not live.engine.probabilities:
            return None
        return max(live.engine.probabilities, key=live.engine.probabilities.get)

    @staticmethod
    def best_guess(live: LiveSession) -> tuple[UUID, float] | None:
        """Return (character_id, confidence) for the current best guess."""
        top_id = GameSessionManager.best_guess_id(live)
        if top_id is None:
            return None
        return top_id, live.engine.probabilities[top_id]

    @staticmethod
    def asked_question_ids(live: LiveSession) -> list[UUID]:
        """Questions already asked (tracked on the engine + answer log)."""
        return list(live.engine.used_question_ids)
