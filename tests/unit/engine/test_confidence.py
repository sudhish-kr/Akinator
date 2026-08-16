"""Essential unit tests for the confidence engine."""

from uuid import UUID, uuid4

import pytest

from app.engine.bayesian import initialize_uniform_priors
from app.engine.confidence import (
    best_available_guess,
    confidence_score,
    evaluate_confidence,
    resolve_turn,
)
from app.engine.models import GameEngineState

C1 = UUID("00000000-0000-0000-0000-000000000001")
C2 = UUID("00000000-0000-0000-0000-000000000002")
C3 = UUID("00000000-0000-0000-0000-000000000003")


def _state(probs: dict[UUID, float], questions_asked: int = 0) -> GameEngineState:
    return GameEngineState(
        character_ids=list(probs.keys()),
        probabilities=dict(probs),
        likelihoods={},
        questions_asked=questions_asked,
    )


class TestConfidenceScore:
    def test_returns_top_probability_clamped(self):
        state = _state({C1: 0.7, C2: 0.3})
        assert confidence_score(state) == pytest.approx(0.7)

    def test_empty_is_zero(self):
        state = _state({})
        assert confidence_score(state) == 0.0


class TestEvaluateConfidence:
    def test_high_threshold_triggers_guess(self):
        state = _state({C1: 0.9, C2: 0.1})
        result = evaluate_confidence(state, confidence_high=0.85)
        assert result.should_guess is True
        assert 0.0 <= result.confidence <= 1.0
        assert result.confidence == pytest.approx(0.9)
        assert result.reason == "high_confidence"
        assert result.top_character_id == C1

    def test_low_confidence_close_seconds_continue_asking(self):
        state = _state({C1: 0.42, C2: 0.39, C3: 0.19})
        result = evaluate_confidence(state)
        assert result.should_guess is False
        assert result.confidence == pytest.approx(0.42)

    def test_high_confidence_and_separation_guesses_early(self):
        state = _state({C1: 0.93, C2: 0.03, C3: 0.04}, questions_asked=7)
        result = evaluate_confidence(state)
        assert result.should_guess is True
        assert result.reason in {"high_confidence", "clear_separation"}
        assert result.top_character_id == C1

    def test_clear_separation_triggers_guess(self):
        state = _state({C1: 0.7, C2: 0.2, C3: 0.1})
        result = evaluate_confidence(
            state,
            confidence_high=0.95,
            confidence_separation=0.6,
            confidence_margin=0.4,
        )
        assert result.should_guess is True
        assert result.reason == "clear_separation"

    def test_question_budget_always_guesses(self):
        """Safety limit: never keep asking once the budget is spent."""
        state = _state({C1: 0.36, C2: 0.34, C3: 0.30}, questions_asked=20)
        result = evaluate_confidence(state, confidence_high=0.85, max_questions=20)
        assert result.should_guess is True
        assert result.reason == "question_budget"

    def test_question_budget_guesses_when_separated(self):
        state = _state({C1: 0.70, C2: 0.30}, questions_asked=25)
        result = evaluate_confidence(
            state,
            confidence_high=0.95,
            confidence_separation=0.72,
            confidence_margin=0.28,
            max_questions=25,
        )
        assert result.should_guess is True
        assert result.reason == "question_budget"


class TestResolveTurn:
    def test_no_questions_remain_returns_best_guess(self):
        state = _state({C1: 0.55, C2: 0.45})
        result = resolve_turn(state, next_question_id=None, confidence_high=0.85)
        assert result.should_guess is True
        assert result.reason == "no_questions_remain"
        assert result.top_character_id == C1
        assert result.confidence == pytest.approx(0.55)

    def test_no_next_question_guesses_even_at_tiny_confidence(self):
        """No useful remaining split → best available guess, not more trivia."""
        state = _state({C1: 0.012, C2: 0.011, C3: 0.010}, questions_asked=8)
        result = resolve_turn(
            state,
            next_question_id=None,
            confidence_high=0.85,
            max_questions=20,
            min_guess_confidence=0.35,
        )
        assert result.should_guess is True
        assert result.reason == "no_questions_remain"

    def test_tiny_confidence_guesses_only_when_budget_spent(self):
        state = _state({C1: 0.02, C2: 0.01}, questions_asked=20)
        result = resolve_turn(
            state,
            next_question_id=None,
            confidence_high=0.85,
            max_questions=20,
            min_guess_confidence=0.35,
        )
        assert result.should_guess is True
        assert result.reason in {"no_questions_remain", "question_budget"}

    def test_low_confidence_with_next_question_keeps_asking(self):
        state = _state({C1: 0.5, C2: 0.5})
        qid = uuid4()
        result = resolve_turn(state, next_question_id=qid, confidence_high=0.85)
        assert result.should_guess is False
        assert result.confidence == pytest.approx(0.5)

    def test_best_available_guess_helper(self):
        state = _state(initialize_uniform_priors([C1, C2, C3]))
        result = best_available_guess(state)
        assert result.should_guess is True
        assert abs(result.confidence - (1 / 3)) < 1e-9
