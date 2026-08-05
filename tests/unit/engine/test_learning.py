"""Tests for post-game learning (TDD Section 4)."""

from uuid import uuid4

import pytest

from app.engine.bayesian import apply_learning_update
from app.engine.constants import ANSWER_WEIGHTS


class TestLearningUpdate:
    def test_nudges_toward_yes(self):
        result = apply_learning_update(0.5, ANSWER_WEIGHTS["yes"], learning_rate=0.1)
        assert result == pytest.approx(0.55)

    def test_nudges_toward_no(self):
        result = apply_learning_update(0.5, ANSWER_WEIGHTS["no"], learning_rate=0.1)
        assert result == pytest.approx(0.45)

    def test_clamped_to_unit_interval(self):
        assert apply_learning_update(0.99, 1.0, learning_rate=1.0) == pytest.approx(1.0)
        assert apply_learning_update(0.01, 0.0, learning_rate=1.0) == pytest.approx(0.0)

    def test_no_change_when_answer_matches_likelihood(self):
        result = apply_learning_update(0.75, 0.75, learning_rate=0.1)
        assert result == pytest.approx(0.75)
