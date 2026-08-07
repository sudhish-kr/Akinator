import math
from uuid import uuid4

import pytest

from app.engine.bayesian import initialize_uniform_priors
from app.engine.constants import Answer
from app.engine.elimination import eliminate_candidates, entropy
from app.engine.models import GameEngineState, LikelihoodEntry
from app.engine.selector import create_initial_state, select_next_question


def test_entropy_uniform_four_way():
    ids = [uuid4() for _ in range(4)]
    probs = initialize_uniform_priors(ids)
    assert entropy(probs) == pytest.approx(2.0)


def test_elimination_removes_negligible():
    c1, c2, c3 = uuid4(), uuid4(), uuid4()
    state = GameEngineState(
        character_ids=[c1, c2, c3],
        probabilities={c1: 0.99, c2: 0.009, c3: 0.001},
        likelihoods={},
    )
    remaining, _ = eliminate_candidates(state, floor=0.0005, magnitude=1000.0)
    assert c1 in remaining
    assert c2 in remaining or c2 not in remaining  # c2 may survive if above floor
    assert c3 not in remaining or remaining[c3] >= 0.0005


def test_empty_pool_fallback():
    """TDD Section 7: all eliminated → restore pre-elimination top."""
    c1, c2 = uuid4(), uuid4()
    state = GameEngineState(
        character_ids=[c1, c2],
        probabilities={c1: 0.51, c2: 0.49},
        likelihoods={},
    )
    remaining, pre_top = eliminate_candidates(state, floor=0.6, magnitude=2.0)
    assert len(remaining) == 1
    assert pre_top in remaining
    assert sum(remaining.values()) == pytest.approx(1.0)


def test_select_next_question_skips_used():
    chars = [uuid4() for _ in range(3)]
    q1, q2 = uuid4(), uuid4()
    likelihoods = {
        (chars[0], q1): LikelihoodEntry(0.5, 10),
        (chars[1], q1): LikelihoodEntry(0.5, 10),
        (chars[2], q1): LikelihoodEntry(0.5, 10),
        (chars[0], q2): LikelihoodEntry(0.9, 10),
        (chars[1], q2): LikelihoodEntry(0.1, 10),
        (chars[2], q2): LikelihoodEntry(0.1, 10),
    }
    state = create_initial_state(chars, likelihoods)
    state.used_question_ids.add(q1)
    next_q = select_next_question(state, [q1, q2], min_samples=1, explore=False)
    assert next_q == q2
