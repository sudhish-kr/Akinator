"""Essential tests for information-gain question selection."""

from uuid import UUID

import pytest

from app.engine.models import LikelihoodEntry
from app.engine.selector import (
    create_initial_state,
    information_gain,
    select_next_question,
)

C1 = UUID("00000000-0000-0000-0000-000000000001")
C2 = UUID("00000000-0000-0000-0000-000000000002")
C3 = UUID("00000000-0000-0000-0000-000000000003")
Q_SPLIT = UUID("00000000-0000-0000-0000-0000000000a1")  # high IG
Q_FLAT = UUID("00000000-0000-0000-0000-0000000000a2")  # low IG


def _state_with_split_and_flat():
    """Q_SPLIT strongly partitions candidates; Q_FLAT does not."""
    likelihoods = {
        (C1, Q_SPLIT): LikelihoodEntry(0.95, 50),
        (C2, Q_SPLIT): LikelihoodEntry(0.05, 50),
        (C3, Q_SPLIT): LikelihoodEntry(0.05, 50),
        (C1, Q_FLAT): LikelihoodEntry(0.5, 50),
        (C2, Q_FLAT): LikelihoodEntry(0.5, 50),
        (C3, Q_FLAT): LikelihoodEntry(0.5, 50),
    }
    return create_initial_state([C1, C2, C3], likelihoods)


def test_selects_highest_information_gain_question():
    state = _state_with_split_and_flat()
    assert information_gain(state, Q_SPLIT) > information_gain(state, Q_FLAT)
    assert select_next_question(state, [Q_FLAT, Q_SPLIT], min_samples=1) == Q_SPLIT


def test_ignores_already_answered_questions():
    state = _state_with_split_and_flat()
    state.used_question_ids.add(Q_SPLIT)
    assert select_next_question(state, [Q_SPLIT, Q_FLAT], min_samples=1) == Q_FLAT


def test_returns_none_when_all_questions_answered():
    state = _state_with_split_and_flat()
    state.used_question_ids.update({Q_SPLIT, Q_FLAT})
    assert select_next_question(state, [Q_SPLIT, Q_FLAT], min_samples=1) is None


def test_information_gain_supports_yes_no_unknown_outcomes():
    """IG must be well-defined when averaging yes / no / unknown (dont_know)."""
    state = _state_with_split_and_flat()
    ig = information_gain(state, Q_SPLIT)
    assert ig > 0
    assert ig == pytest.approx(ig)  # finite, not NaN
