"""Unit tests for Bayesian probability update only (TDD Section 2.2)."""

from uuid import UUID

import pytest

from app.engine.bayesian import (
    bayesian_update,
    initialize_uniform_priors,
    update_probabilities,
)
from app.engine.constants import Answer
from app.engine.models import GameEngineState, LikelihoodEntry

EINSTEIN = UUID("00000000-0000-0000-0000-000000000001")
MESSI = UUID("00000000-0000-0000-0000-000000000002")
MUSK = UUID("00000000-0000-0000-0000-000000000003")
RONALDO = UUID("00000000-0000-0000-0000-000000000004")
SCIENTIST_Q = UUID("00000000-0000-0000-0000-000000000010")

CHARACTER_IDS = [EINSTEIN, MESSI, MUSK, RONALDO]

# L(C, Q) from TDD worked example Section 2.6
LIKELIHOODS_BY_CHAR = {
    EINSTEIN: 0.95,
    MESSI: 0.02,
    MUSK: 0.55,
    RONALDO: 0.02,
}


class TestInitializeUniformPriors:
    def test_equal_share(self):
        priors = initialize_uniform_priors(CHARACTER_IDS)
        assert all(p == pytest.approx(0.25) for p in priors.values())
        assert sum(priors.values()) == pytest.approx(1.0)

    def test_empty(self):
        assert initialize_uniform_priors([]) == {}


class TestUpdateProbabilities:
    """Pure API: previous probs + likelihoods + answer → posterior."""

    def test_yes_matches_tdd_worked_example(self):
        previous = initialize_uniform_priors(CHARACTER_IDS)
        updated = update_probabilities(previous, LIKELIHOODS_BY_CHAR, Answer.YES)

        assert updated[EINSTEIN] == pytest.approx(0.617, abs=0.001)
        assert updated[MUSK] == pytest.approx(0.357, abs=0.001)
        assert updated[MESSI] == pytest.approx(0.013, abs=0.001)
        assert updated[RONALDO] == pytest.approx(0.013, abs=0.001)
        assert sum(updated.values()) == pytest.approx(1.0)

    def test_accepts_string_yes(self):
        previous = initialize_uniform_priors(CHARACTER_IDS)
        updated = update_probabilities(previous, LIKELIHOODS_BY_CHAR, "yes")
        assert updated[EINSTEIN] == pytest.approx(0.617, abs=0.001)

    def test_no_boosts_non_scientists(self):
        previous = initialize_uniform_priors(CHARACTER_IDS)
        updated = update_probabilities(previous, LIKELIHOODS_BY_CHAR, Answer.NO)

        # No (w=0): match = 1 - |L - 0| = 1 - L → Messi/Ronaldo rise, Einstein falls
        assert updated[MESSI] > updated[EINSTEIN]
        assert updated[RONALDO] > updated[EINSTEIN]
        assert sum(updated.values()) == pytest.approx(1.0)

    def test_unknown_alias_equals_dont_know(self):
        previous = initialize_uniform_priors(CHARACTER_IDS)
        via_alias = update_probabilities(previous, LIKELIHOODS_BY_CHAR, "unknown")
        via_enum = update_probabilities(previous, LIKELIHOODS_BY_CHAR, Answer.DONT_KNOW)
        assert via_alias == via_enum
        assert sum(via_alias.values()) == pytest.approx(1.0)

    def test_unknown_is_less_discriminative_than_yes(self):
        previous = initialize_uniform_priors(CHARACTER_IDS)
        after_yes = update_probabilities(previous, LIKELIHOODS_BY_CHAR, "yes")
        after_unknown = update_probabilities(previous, LIKELIHOODS_BY_CHAR, "unknown")

        # Unknown (w=0.5) should not concentrate mass on Einstein as strongly as Yes
        assert after_unknown[EINSTEIN] < after_yes[EINSTEIN]

    def test_uses_previous_non_uniform_priors(self):
        previous = {
            EINSTEIN: 0.7,
            MESSI: 0.1,
            MUSK: 0.1,
            RONALDO: 0.1,
        }
        updated = update_probabilities(previous, LIKELIHOODS_BY_CHAR, Answer.YES)
        assert updated[EINSTEIN] > 0.7  # already high prior + strong Yes match
        assert sum(updated.values()) == pytest.approx(1.0)

    def test_missing_likelihood_defaults_to_half(self):
        previous = {EINSTEIN: 0.5, MESSI: 0.5}
        # Only Einstein has a stored likelihood; Messi uses default 0.5
        updated = update_probabilities(previous, {EINSTEIN: 1.0}, Answer.YES)
        assert updated[EINSTEIN] > updated[MESSI]
        assert sum(updated.values()) == pytest.approx(1.0)

    def test_degenerate_all_zero_mass_falls_back_to_uniform(self):
        # Yes with L=0 for everyone → match=0 → total 0 → uniform restore
        previous = {EINSTEIN: 0.5, MESSI: 0.5}
        updated = update_probabilities(previous, {EINSTEIN: 0.0, MESSI: 0.0}, Answer.YES)
        assert updated[EINSTEIN] == pytest.approx(0.5)
        assert updated[MESSI] == pytest.approx(0.5)

    def test_empty_previous(self):
        assert update_probabilities({}, {}, Answer.YES) == {}

    def test_invalid_answer_raises(self):
        with pytest.raises(ValueError, match="Invalid answer"):
            update_probabilities(
                initialize_uniform_priors(CHARACTER_IDS),
                LIKELIHOODS_BY_CHAR,
                "maybe",
            )


class TestBayesianUpdateStateWrapper:
    """Existing GameEngineState wrapper stays compatible with callers."""

    def test_worked_example_via_state(self):
        state = GameEngineState(
            character_ids=CHARACTER_IDS,
            probabilities=initialize_uniform_priors(CHARACTER_IDS),
            likelihoods={
                (cid, SCIENTIST_Q): LikelihoodEntry(likelihood=L, sample_size=100)
                for cid, L in LIKELIHOODS_BY_CHAR.items()
            },
        )
        updated = bayesian_update(state, SCIENTIST_Q, Answer.YES)
        assert updated[EINSTEIN] == pytest.approx(0.617, abs=0.001)
        assert sum(updated.values()) == pytest.approx(1.0)
