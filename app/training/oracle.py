"""Oracle answers for virtual play — derived from stored likelihoods + noise."""

from __future__ import annotations

import random

from app.engine.cold_start import get_likelihood
from app.engine.constants import ALL_ANSWERS, Answer
from app.engine.models import LikelihoodEntry


def closest_answer(weight: float) -> Answer:
    """Map a continuous weight in [0, 1] to the nearest discrete Answer."""
    return min(ALL_ANSWERS, key=lambda a: abs(a.weight - weight))


def oracle_answer(
    likelihoods: dict[tuple, LikelihoodEntry],
    character_id,
    question_id,
    rng: random.Random,
    *,
    noise: float = 0.08,
) -> str:
    """
    Simulate a human answer for the true character.

    Starts from smoothed L(C, Q), adds Gaussian noise, snaps to Answer enum.
    """
    base = get_likelihood(likelihoods, character_id, question_id)
    noisy = base + rng.gauss(0.0, noise)
    noisy = max(0.0, min(1.0, noisy))
    return closest_answer(noisy).value
