"""Confidence engine (TDD v1.1 Section 2.5).

After every answer, score the top posterior probability in [0.0, 1.0] and
decide whether to guess or keep asking.

Guess when:
  - confidence >= configured high threshold, or
  - clear separation (confidence + margin), or
  - question budget exhausted, or
  - ≤ 1 candidate left, or
  - no useful questions remain (best available guess).
"""

from __future__ import annotations

from uuid import UUID

from app.engine.constants import (
    DEFAULT_CONFIDENCE_HIGH,
    DEFAULT_CONFIDENCE_MARGIN,
    DEFAULT_CONFIDENCE_SEPARATION,
    DEFAULT_MAX_QUESTIONS,
    DEFAULT_MIN_GUESS_CONFIDENCE,
)
from app.engine.elimination import top_two
from app.engine.models import ConfidenceResult, GameEngineState


def confidence_score(state: GameEngineState) -> float:
    """Top character posterior probability, clamped to [0.0, 1.0]."""
    probs = [p for p in state.probabilities.values() if p > 0]
    if not probs:
        return 0.0
    top = max(probs)
    return max(0.0, min(1.0, float(top)))


def normalize_probabilities(probabilities: dict[UUID, float]) -> dict[UUID, float]:
    """Safely renormalize posterior mass to sum to 1.0 (no-op if empty)."""
    if not probabilities:
        return {}
    total = sum(max(0.0, float(p)) for p in probabilities.values())
    if total <= 0:
        n = len(probabilities)
        if n == 0:
            return {}
        uniform = 1.0 / n
        return {cid: uniform for cid in probabilities}
    return {cid: max(0.0, float(p)) / total for cid, p in probabilities.items()}


def evaluate_confidence(
    state: GameEngineState,
    confidence_high: float = DEFAULT_CONFIDENCE_HIGH,
    confidence_separation: float = DEFAULT_CONFIDENCE_SEPARATION,
    confidence_margin: float = DEFAULT_CONFIDENCE_MARGIN,
    max_questions: int = DEFAULT_MAX_QUESTIONS,
) -> ConfidenceResult:
    """
    Calculate confidence after an answer and decide whether to trigger a guess.

    Returns ConfidenceResult with confidence in [0.0, 1.0].
    should_guess=False means continue asking questions.
    """
    probs = state.probabilities
    if not probs:
        return ConfidenceResult(
            should_guess=True,
            confidence=0.0,
            margin=0.0,
            top_character_id=None,
            second_character_id=None,
            reason="no_candidates",
        )

    top, second = top_two(probs)
    assert top is not None

    top_id, top_p = top
    second_id = second[0] if second else None
    second_p = second[1] if second else 0.0
    margin = top_p - second_p
    score = max(0.0, min(1.0, float(top_p)))
    active_count = len(probs)

    if score >= confidence_high:
        return ConfidenceResult(
            should_guess=True,
            confidence=score,
            margin=margin,
            top_character_id=top_id,
            second_character_id=second_id,
            reason="high_confidence",
        )

    if score >= confidence_separation and margin >= confidence_margin:
        return ConfidenceResult(
            should_guess=True,
            confidence=score,
            margin=margin,
            top_character_id=top_id,
            second_character_id=second_id,
            reason="clear_separation",
        )

    if state.questions_asked >= max_questions:
        return ConfidenceResult(
            should_guess=True,
            confidence=score,
            margin=margin,
            top_character_id=top_id,
            second_character_id=second_id,
            reason="question_budget",
        )

    if active_count <= 1:
        return ConfidenceResult(
            should_guess=True,
            confidence=score,
            margin=margin,
            top_character_id=top_id,
            second_character_id=second_id,
            reason="candidates_exhausted",
        )

    return ConfidenceResult(
        should_guess=False,
        confidence=score,
        margin=margin,
        top_character_id=top_id,
        second_character_id=second_id,
        reason=None,
    )


def best_available_guess(state: GameEngineState) -> ConfidenceResult:
    """
    Force a guess using the current best candidate (e.g. no useful questions left).
    Confidence remains the top posterior in [0.0, 1.0].
    """
    probs = state.probabilities
    if not probs:
        return ConfidenceResult(
            should_guess=True,
            confidence=0.0,
            margin=0.0,
            top_character_id=None,
            second_character_id=None,
            reason="no_candidates",
        )

    top, second = top_two(probs)
    assert top is not None
    top_id, top_p = top
    second_id = second[0] if second else None
    second_p = second[1] if second else 0.0
    score = max(0.0, min(1.0, float(top_p)))
    return ConfidenceResult(
        should_guess=True,
        confidence=score,
        margin=top_p - second_p,
        top_character_id=top_id,
        second_character_id=second_id,
        reason="no_questions_remain",
    )


def resolve_turn(
    state: GameEngineState,
    next_question_id: UUID | None,
    *,
    confidence_high: float = DEFAULT_CONFIDENCE_HIGH,
    confidence_separation: float = DEFAULT_CONFIDENCE_SEPARATION,
    confidence_margin: float = DEFAULT_CONFIDENCE_MARGIN,
    max_questions: int = DEFAULT_MAX_QUESTIONS,
    min_guess_confidence: float = DEFAULT_MIN_GUESS_CONFIDENCE,
) -> ConfidenceResult:
    """
    Session-manager turn resolution after an answer.

    - High confidence / stop rules → guess
    - Low confidence + a next question → keep asking
    - No next question + enough confidence (or budget spent) → best available guess
    - No next question + tiny confidence + budget left → keep asking (do not guess at 1%)
    """
    result = evaluate_confidence(
        state,
        confidence_high=confidence_high,
        confidence_separation=confidence_separation,
        confidence_margin=confidence_margin,
        max_questions=max_questions,
    )
    if result.should_guess:
        return result
    if next_question_id is not None:
        return result

    budget_spent = state.questions_asked >= max_questions
    if budget_spent or result.confidence >= min_guess_confidence:
        return best_available_guess(state)

    # Selector went dry while still very unsure — refuse a random 1% guess.
    return ConfidenceResult(
        should_guess=False,
        confidence=result.confidence,
        margin=result.margin,
        top_character_id=result.top_character_id,
        second_character_id=result.second_character_id,
        reason="awaiting_questions",
    )
