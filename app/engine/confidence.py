from uuid import UUID

from app.engine.constants import (
    DEFAULT_CONFIDENCE_HIGH,
    DEFAULT_CONFIDENCE_MARGIN,
    DEFAULT_CONFIDENCE_SEPARATION,
    DEFAULT_MAX_QUESTIONS,
)
from app.engine.elimination import top_two
from app.engine.models import ConfidenceResult, GameEngineState


def evaluate_confidence(
    state: GameEngineState,
    confidence_high: float = DEFAULT_CONFIDENCE_HIGH,
    confidence_separation: float = DEFAULT_CONFIDENCE_SEPARATION,
    confidence_margin: float = DEFAULT_CONFIDENCE_MARGIN,
    max_questions: int = DEFAULT_MAX_QUESTIONS,
) -> ConfidenceResult:
    """Decide whether to guess or ask another question (TDD Section 2.5)."""
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
    active_count = len(probs)

    if top_p >= confidence_high:
        return ConfidenceResult(
            should_guess=True,
            confidence=top_p,
            margin=margin,
            top_character_id=top_id,
            second_character_id=second_id,
            reason="high_confidence",
        )

    if top_p >= confidence_separation and margin >= confidence_margin:
        return ConfidenceResult(
            should_guess=True,
            confidence=top_p,
            margin=margin,
            top_character_id=top_id,
            second_character_id=second_id,
            reason="clear_separation",
        )

    if state.questions_asked >= max_questions:
        return ConfidenceResult(
            should_guess=True,
            confidence=top_p,
            margin=margin,
            top_character_id=top_id,
            second_character_id=second_id,
            reason="question_budget",
        )

    if active_count <= 1:
        return ConfidenceResult(
            should_guess=True,
            confidence=top_p,
            margin=margin,
            top_character_id=top_id,
            second_character_id=second_id,
            reason="candidates_exhausted",
        )

    return ConfidenceResult(
        should_guess=False,
        confidence=top_p,
        margin=margin,
        top_character_id=top_id,
        second_character_id=second_id,
        reason=None,
    )
