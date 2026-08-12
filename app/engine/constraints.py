"""Strong categorical answer constraints on the candidate pool.

Uses existing CharacterAnswer likelihoods as the attribute evidence.
Does not invent nationality/gender columns — unknown L stays eligible.

YES / NO with reliable, clearly contradicting L → eliminate.
PROBABLY / PROBABLY NOT → strong soft penalty, keep candidate.
DON'T KNOW → no constraint change.
Missing / low-sample / near-neutral L → treat as unknown (keep).
"""

from __future__ import annotations

from uuid import UUID

from app.engine.bayesian import _resolve_answer, initialize_uniform_priors
from app.engine.constants import (
    DEFAULT_CONSTRAINT_AFFIRM_MAX,
    DEFAULT_CONSTRAINT_MIN_SAMPLES,
    DEFAULT_CONSTRAINT_NEGATE_MIN,
    DEFAULT_CONSTRAINT_SOFT_FACTOR,
    Answer,
)
from app.engine.models import LikelihoodEntry


def _reliable_likelihood(
    entry: LikelihoodEntry | None,
    *,
    min_samples: int,
) -> float | None:
    """Return raw L when evidence is reliable; None means unknown/keep."""
    if entry is None:
        return None
    if int(entry.sample_size) < min_samples:
        return None
    return float(entry.likelihood)


def apply_answer_constraints(
    probabilities: dict[UUID, float],
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry],
    question_id: UUID,
    answer: Answer | str,
    *,
    affirm_max: float = DEFAULT_CONSTRAINT_AFFIRM_MAX,
    negate_min: float = DEFAULT_CONSTRAINT_NEGATE_MIN,
    min_samples: int = DEFAULT_CONSTRAINT_MIN_SAMPLES,
    soft_factor: float = DEFAULT_CONSTRAINT_SOFT_FACTOR,
) -> dict[UUID, float]:
    """
    Narrow the candidate population after a Bayesian update.

    Generic for any question that has reliable per-character likelihoods
    (country, real/fictional, alive, gender, athlete, cricket, anime, …).
    """
    if not probabilities:
        return {}

    resolved = _resolve_answer(answer)
    if resolved == Answer.DONT_KNOW:
        return dict(probabilities)

    hard: dict[UUID, float] = {}
    soft: dict[UUID, float] = {}
    for cid, p in probabilities.items():
        entry = likelihoods.get((cid, question_id))
        lik = _reliable_likelihood(entry, min_samples=min_samples)
        if lik is None:
            hard[cid] = p
            soft[cid] = p
            continue

        clearly_no = lik <= affirm_max
        clearly_yes = lik >= negate_min

        if resolved == Answer.YES:
            soft[cid] = p * (soft_factor if clearly_no else 1.0)
            if not clearly_no:
                hard[cid] = p
        elif resolved == Answer.NO:
            soft[cid] = p * (soft_factor if clearly_yes else 1.0)
            if not clearly_yes:
                hard[cid] = p
        elif resolved == Answer.PROBABLY_YES:
            soft[cid] = p * (soft_factor if clearly_no else 1.0)
            hard[cid] = soft[cid]
        elif resolved == Answer.PROBABLY_NO:
            soft[cid] = p * (soft_factor if clearly_yes else 1.0)
            hard[cid] = soft[cid]
        else:
            hard[cid] = p
            soft[cid] = p

    # Prefer hard elimination when at least one non-contradicting candidate remains.
    updated = hard if hard else soft
    total = sum(updated.values())
    if total <= 0:
        return initialize_uniform_priors(list(probabilities.keys()))
    return {cid: value / total for cid, value in updated.items()}
