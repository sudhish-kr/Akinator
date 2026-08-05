from app.engine.constants import DEFAULT_NEW_QUESTION_MIN_SAMPLES
from app.engine.models import LikelihoodEntry

# Below this threshold, shrink extreme likelihoods toward 0.5 (TDD Section 3).
COLD_START_SAMPLE_THRESHOLD = 10


def smooth_likelihood(entry: LikelihoodEntry | None, default: float = 0.5) -> float:
    """
    Shrink extreme likelihoods toward 0.5 when sample size is very low.
    Well-sampled pairs use the stored value directly (matches TDD worked example).
    """
    if entry is None:
        return default

    raw = entry.likelihood
    n = entry.sample_size
    if n <= 0:
        return default
    if n >= COLD_START_SAMPLE_THRESHOLD:
        return raw

    shrink = 1.0 / (1.0 + n)
    return raw * (1.0 - shrink) + default * shrink


def is_question_eligible(
    question_id,
    likelihoods: dict,
    character_ids: list,
    min_samples: int = DEFAULT_NEW_QUESTION_MIN_SAMPLES,
) -> bool:
    """A question is eligible for IG selection once it has minimum data (TDD Section 3)."""
    total_samples = 0
    for cid in character_ids:
        entry = likelihoods.get((cid, question_id))
        if entry:
            total_samples += entry.sample_size
    return total_samples >= min_samples


def likelihood_match(stored_likelihood: float, answer_weight: float) -> float:
    """TDD Section 2.2: how well the user's answer matches stored L(C, Q)."""
    return 1.0 - abs(stored_likelihood - answer_weight)


def get_likelihood(
    likelihoods: dict,
    character_id,
    question_id,
    default: float = 0.5,
) -> float:
    entry = likelihoods.get((character_id, question_id))
    return smooth_likelihood(entry, default)
