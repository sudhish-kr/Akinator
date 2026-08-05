"""
Golden test fixture from TDD v1.1 Section 2.6.

Characters: Einstein, Messi, Elon Musk, Cristiano Ronaldo — each P = 0.25.
Question: 'Is this person a scientist?'
User answers: Yes (w=1.0)
"""

from uuid import UUID, uuid4

import pytest

from app.engine.bayesian import bayesian_update, initialize_uniform_priors
from app.engine.cold_start import likelihood_match
from app.engine.confidence import evaluate_confidence
from app.engine.constants import Answer
from app.engine.models import GameEngineState, LikelihoodEntry
from app.engine.selector import create_initial_state, process_answer

# Fixed UUIDs for reproducibility
EINSTEIN = UUID("00000000-0000-0000-0000-000000000001")
MESSI = UUID("00000000-0000-0000-0000-000000000002")
MUSK = UUID("00000000-0000-0000-0000-000000000003")
RONALDO = UUID("00000000-0000-0000-0000-000000000004")
SCIENTIST_Q = UUID("00000000-0000-0000-0000-000000000010")

CHARACTER_IDS = [EINSTEIN, MESSI, MUSK, RONALDO]

# Stored likelihoods L(C, Q) from TDD Section 2.6
LIKELIHOODS = {
    (EINSTEIN, SCIENTIST_Q): LikelihoodEntry(likelihood=0.95, sample_size=100),
    (MESSI, SCIENTIST_Q): LikelihoodEntry(likelihood=0.02, sample_size=100),
    (MUSK, SCIENTIST_Q): LikelihoodEntry(likelihood=0.55, sample_size=100),
    (RONALDO, SCIENTIST_Q): LikelihoodEntry(likelihood=0.02, sample_size=100),
}


class TestLikelihoodMatch:
    def test_perfect_match(self):
        assert likelihood_match(0.95, 1.0) == pytest.approx(0.95)

    def test_no_match(self):
        assert likelihood_match(0.02, 1.0) == pytest.approx(0.02)


class TestBayesianUpdateWorkedExample:
    def test_uniform_priors(self):
        priors = initialize_uniform_priors(CHARACTER_IDS)
        assert len(priors) == 4
        for p in priors.values():
            assert p == pytest.approx(0.25)

    def test_p_new_before_normalization(self):
        """Verify P_new values from TDD table before renormalization."""
        state = create_initial_state(CHARACTER_IDS, LIKELIHOODS)
        answer_weight = Answer.YES.weight

        expected_p_new = {
            EINSTEIN: 0.25 * likelihood_match(0.95, answer_weight),  # 0.2375
            MESSI: 0.25 * likelihood_match(0.02, answer_weight),  # 0.0050
            MUSK: 0.25 * likelihood_match(0.55, answer_weight),  # 0.1375
            RONALDO: 0.25 * likelihood_match(0.02, answer_weight),  # 0.0050
        }

        for cid, expected in expected_p_new.items():
            assert expected == pytest.approx(
                {EINSTEIN: 0.2375, MESSI: 0.0050, MUSK: 0.1375, RONALDO: 0.0050}[cid]
            )

    def test_after_normalization(self):
        """After renormalizing: Einstein ≈ 0.617, Musk ≈ 0.357, others ≈ 0.013."""
        state = create_initial_state(CHARACTER_IDS, LIKELIHOODS)
        updated = bayesian_update(state, SCIENTIST_Q, Answer.YES)

        assert updated[EINSTEIN] == pytest.approx(0.617, abs=0.001)
        assert updated[MUSK] == pytest.approx(0.357, abs=0.001)
        assert updated[MESSI] == pytest.approx(0.013, abs=0.001)
        assert updated[RONALDO] == pytest.approx(0.013, abs=0.001)
        assert sum(updated.values()) == pytest.approx(1.0)

    def test_confidence_below_threshold_after_one_question(self):
        """confidence (0.617) and margin (0.26) both below threshold — keep asking."""
        state = create_initial_state(CHARACTER_IDS, LIKELIHOODS)
        state.probabilities = bayesian_update(state, SCIENTIST_Q, Answer.YES)

        result = evaluate_confidence(state)
        assert result.should_guess is False
        assert result.confidence == pytest.approx(0.617, abs=0.001)
        assert result.margin == pytest.approx(0.26, abs=0.01)


class TestProbabilitiesSumToOne:
    def test_after_update(self):
        state = create_initial_state(CHARACTER_IDS, LIKELIHOODS)
        updated = bayesian_update(state, SCIENTIST_Q, Answer.YES)
        assert sum(updated.values()) == pytest.approx(1.0)

    def test_after_process_answer_with_elimination(self):
        state = create_initial_state(CHARACTER_IDS, LIKELIHOODS)
        state, _ = process_answer(state, SCIENTIST_Q, Answer.YES)
        assert sum(state.probabilities.values()) == pytest.approx(1.0)
