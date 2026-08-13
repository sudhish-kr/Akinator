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


def compute_question_sample_totals(
    likelihoods: dict,
    character_ids: list,
) -> dict:
    """Sum sample_size per question over the given character set (one pass)."""
    wanted = set(character_ids)
    totals: dict = {}
    for (cid, qid), entry in likelihoods.items():
        if cid in wanted:
            totals[qid] = totals.get(qid, 0) + int(entry.sample_size)
    return totals


def is_question_eligible(
    question_id,
    likelihoods: dict,
    character_ids: list,
    min_samples: int = DEFAULT_NEW_QUESTION_MIN_SAMPLES,
    sample_totals: dict | None = None,
) -> bool:
    """A question is eligible for IG selection once it has minimum data (TDD Section 3)."""
    if sample_totals:
        cached = sample_totals.get(question_id)
        if cached is not None:
            return int(cached) >= min_samples
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
