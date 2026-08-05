from uuid import UUID

from app.engine.cold_start import get_likelihood, likelihood_match
from app.engine.models import GameEngineState, LikelihoodEntry, answer_from_str
from app.engine.constants import Answer


def initialize_uniform_priors(character_ids: list[UUID]) -> dict[UUID, float]:
    """P(C) = 1/N for all active characters (TDD Section 2.1)."""
    if not character_ids:
        return {}
    p = 1.0 / len(character_ids)
    return {cid: p for cid in character_ids}


def bayesian_update(
    state: GameEngineState,
    question_id: UUID,
    answer: Answer | str,
) -> dict[UUID, float]:
    """
    Apply Bayes' rule and renormalize (TDD Section 2.2).
    Returns the updated probability distribution.
    """
    if isinstance(answer, str):
        answer = answer_from_str(answer)

    answer_weight = answer.weight
    active = state.active_character_ids()
    updated: dict[UUID, float] = {}

    for cid in active:
        p_old = state.probabilities[cid]
        l_cq = get_likelihood(state.likelihoods, cid, question_id)
        match = likelihood_match(l_cq, answer_weight)
        updated[cid] = p_old * match

    total = sum(updated.values())
    if total <= 0:
        # Degenerate case: restore uniform over active set
        return initialize_uniform_priors(active)

    return {cid: updated[cid] / total for cid in active}


def apply_learning_update(
    old_likelihood: float,
    user_answer_weight: float,
    learning_rate: float,
) -> float:
    """Post-game nudge (TDD Section 4.1)."""
    new_val = old_likelihood + learning_rate * (user_answer_weight - old_likelihood)
    return max(0.0, min(1.0, new_val))
