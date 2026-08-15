"""Bayesian probability update (TDD v1.1 Section 2.2).

Pure update: P'(C) ∝ P(C) × (1 − |L(C,Q) − w|), then renormalize.
Answer weights: yes=1.0, no=0.0, dont_know/unknown=0.5
(also probably_yes=0.75, probably_no=0.25 per TDD).
"""

from __future__ import annotations

import math
from uuid import UUID

from app.engine.cold_start import get_likelihood, likelihood_match
from app.engine.constants import Answer
from app.engine.models import GameEngineState, answer_from_str

# User-facing aliases for the three primary answers
_ANSWER_ALIASES: dict[str, str] = {
    "unknown": "dont_know",
    "dontknow": "dont_know",
    "don't_know": "dont_know",
}

# Mild popularity tilt: famous characters start slightly ahead of obscure ones.
# Does not invent confidence — mass still sums to 1.0.
DEFAULT_POPULARITY_PRIOR_STRENGTH = 0.35


def initialize_uniform_priors(character_ids: list[UUID]) -> dict[UUID, float]:
    """P(C) = 1/N for all characters (TDD Section 2.1)."""
    if not character_ids:
        return {}
    p = 1.0 / len(character_ids)
    return {cid: p for cid in character_ids}


def initialize_priors(
    character_ids: list[UUID],
    popularity: dict[UUID, int] | None = None,
    *,
    strength: float = DEFAULT_POPULARITY_PRIOR_STRENGTH,
) -> dict[UUID, float]:
    """
    Prior P(C). Uniform when popularity is absent; otherwise
    P(C) ∝ 1 + strength * log1p(popularity_score), then normalized.
    """
    if not character_ids:
        return {}
    if not popularity or strength <= 0:
        return initialize_uniform_priors(character_ids)

    weights = {
        cid: 1.0 + float(strength) * math.log1p(max(0, int(popularity.get(cid, 0))))
        for cid in character_ids
    }
    total = sum(weights.values())
    if total <= 0:
        return initialize_uniform_priors(character_ids)
    return {cid: w / total for cid, w in weights.items()}


def _resolve_answer(answer: Answer | str) -> Answer:
    if isinstance(answer, Answer):
        return answer
    key = answer.strip().lower().replace(" ", "_")
    key = _ANSWER_ALIASES.get(key, key)
    return answer_from_str(key)


def update_probabilities(
    previous: dict[UUID, float],
    character_likelihoods: dict[UUID, float],
    answer: Answer | str,
    *,
    default_likelihood: float = 0.5,
) -> dict[UUID, float]:
    """
    Update character probabilities from a user answer (Bayesian formula).

    Args:
        previous: Prior P(C) for each active character.
        character_likelihoods: Stored L(C, Q) per character (missing → default_likelihood).
        answer: Yes / No / Unknown (dont_know), or the full TDD five-way set.

    Returns:
        Renormalized posterior P(C | answer). Sums to 1.0 when previous is non-empty.
    """
    if not previous:
        return {}

    resolved = _resolve_answer(answer)
    weight = resolved.weight
    updated: dict[UUID, float] = {}

    for cid, p_old in previous.items():
        l_cq = character_likelihoods.get(cid, default_likelihood)
        updated[cid] = p_old * likelihood_match(l_cq, weight)

    total = sum(updated.values())
    if total <= 0:
        return initialize_uniform_priors(list(previous.keys()))

    return {cid: value / total for cid, value in updated.items()}


def bayesian_update(
    state: GameEngineState,
    question_id: UUID,
    answer: Answer | str,
) -> dict[UUID, float]:
    """
    Apply Bayes' rule using session likelihood table, then renormalize.
    Thin wrapper over update_probabilities for GameEngineState callers.
    """
    active = state.active_character_ids()
    previous = {cid: state.probabilities[cid] for cid in active}
    character_likelihoods = {
        cid: get_likelihood(state.likelihoods, cid, question_id) for cid in active
    }
    return update_probabilities(previous, character_likelihoods, answer)


def apply_learning_update(
    old_likelihood: float,
    user_answer_weight: float,
    learning_rate: float,
) -> float:
    """Post-game nudge (TDD Section 4.1). Kept here for existing learning callers."""
    new_val = old_likelihood + learning_rate * (user_answer_weight - old_likelihood)
    return max(0.0, min(1.0, new_val))
