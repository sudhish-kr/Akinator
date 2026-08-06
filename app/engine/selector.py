"""Question selection via information gain (TDD v1.1 Section 2.3).

IG(Q) = H(current) − E[H | Q]
where the expectation averages simulated Bayesian updates over answer outcomes
(yes / no / unknown(=dont_know), plus probably_yes / probably_no per TDD).
Already-answered questions are excluded; the single best unused question is returned.
"""

from uuid import UUID

from app.engine.bayesian import bayesian_update, initialize_uniform_priors
from app.engine.cold_start import get_likelihood, is_question_eligible, likelihood_match
from app.engine.confidence import evaluate_confidence
from app.engine.constants import (
    ALL_ANSWERS,
    DEFAULT_CONSECUTIVE_DONT_KNOW_CAP,
    DEFAULT_IG_TIE_THRESHOLD,
    DEFAULT_NEW_QUESTION_MIN_SAMPLES,
    Answer,
)
from app.engine.elimination import eliminate_candidates, entropy
from app.engine.models import ConfidenceResult, GameEngineState, LikelihoodEntry

# Outcomes used when estimating E[H | Q]. Includes yes / no / unknown (dont_know).
_IG_ANSWERS: tuple[Answer, ...] = ALL_ANSWERS


def expected_entropy_after_question(
    state: GameEngineState,
    question_id: UUID,
) -> float:
    """
    Expected posterior entropy after asking Q (TDD Section 2.3).

    For each answer a in {yes, no, unknown, ...}:
      P(a) ∝ Σ_C P(C) · (1 − |L(C,Q) − w_a|)
      H(a)  = entropy(bayesian_update(state, Q, a))
    Returns Σ_a P(a) · H(a) with P(a) renormalized to sum to 1.
    """
    active = state.active_character_ids()
    weighted: list[tuple[float, float]] = []

    for answer in _IG_ANSWERS:
        p_answer = 0.0
        for cid in active:
            l_cq = get_likelihood(state.likelihoods, cid, question_id)
            p_answer += state.probabilities[cid] * likelihood_match(l_cq, answer.weight)

        if p_answer <= 0:
            continue

        sim_state = GameEngineState(
            character_ids=state.character_ids,
            probabilities=state.copy_probabilities(),
            likelihoods=state.likelihoods,
        )
        sim_probs = bayesian_update(sim_state, question_id, answer)
        weighted.append((p_answer, entropy(sim_probs)))

    total_p = sum(weight for weight, _ in weighted)
    if total_p <= 0:
        probs = {cid: state.probabilities[cid] for cid in active}
        return entropy(probs)

    return sum((weight / total_p) * h for weight, h in weighted)


def information_gain(state: GameEngineState, question_id: UUID) -> float:
    """IG(Q) = H(current) − expected entropy after asking Q."""
    active = state.active_character_ids()
    probs = {cid: state.probabilities[cid] for cid in active}
    return entropy(probs) - expected_entropy_after_question(state, question_id)


def total_sample_size_for_question(
    state: GameEngineState,
    question_id: UUID,
) -> int:
    total = 0
    for cid in state.character_ids:
        entry = state.likelihoods.get((cid, question_id))
        if entry:
            total += entry.sample_size
    return total


def select_next_question(
    state: GameEngineState,
    all_question_ids: list[UUID],
    tie_threshold: float = DEFAULT_IG_TIE_THRESHOLD,
    min_samples: int = DEFAULT_NEW_QUESTION_MIN_SAMPLES,
    consecutive_dont_know_cap: int = DEFAULT_CONSECUTIVE_DONT_KNOW_CAP,
) -> UUID | None:
    """
    Return the single unused question with maximum information gain.

    - Skips questions in state.used_question_ids
    - Ties (ΔIG ≤ tie_threshold) broken by higher total sample_size
    - Returns None when no unanswered questions remain
    """
    del consecutive_dont_know_cap  # reserved for future dont_know streak policy

    unused = [
        qid
        for qid in all_question_ids
        if qid not in state.used_question_ids
        and is_question_eligible(qid, state.likelihoods, state.character_ids, min_samples)
    ]

    if not unused:
        # Relax cold-start gate if every unused question is still gated
        unused = [qid for qid in all_question_ids if qid not in state.used_question_ids]

    if not unused:
        return None

    best_qid: UUID | None = None
    best_ig = float("-inf")
    best_samples = -1

    for qid in unused:
        ig = information_gain(state, qid)
        samples = total_sample_size_for_question(state, qid)

        if ig > best_ig + tie_threshold:
            best_ig = ig
            best_qid = qid
            best_samples = samples
        elif abs(ig - best_ig) <= tie_threshold and samples > best_samples:
            best_qid = qid
            best_samples = samples

    return best_qid


def process_answer(
    state: GameEngineState,
    question_id: UUID,
    answer: Answer | str,
) -> tuple[GameEngineState, float]:
    """
    Full turn: update probabilities, eliminate, track dont_know streak.
    Returns (updated_state, entropy_before).
    """
    if isinstance(answer, str):
        answer = Answer(answer)

    active = state.active_character_ids()
    entropy_before = entropy({cid: state.probabilities[cid] for cid in active})

    new_probs = bayesian_update(state, question_id, answer)
    state.probabilities = new_probs

    remaining, pre_top = eliminate_candidates(state)
    state.probabilities = remaining
    state.pre_elimination_top = pre_top

    state.used_question_ids.add(question_id)
    state.questions_asked += 1

    if answer == Answer.DONT_KNOW:
        state.consecutive_dont_know += 1
    else:
        state.consecutive_dont_know = 0

    return state, entropy_before


def create_initial_state(
    character_ids: list[UUID],
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry] | None = None,
) -> GameEngineState:
    return GameEngineState(
        character_ids=list(character_ids),
        probabilities=initialize_uniform_priors(character_ids),
        likelihoods=likelihoods or {},
    )


def decide_after_answer(
    state: GameEngineState,
    all_question_ids: list[UUID],
    **confidence_kwargs,
) -> tuple[ConfidenceResult, UUID | None]:
    """After processing an answer, return confidence check and optional next question."""
    confidence = evaluate_confidence(state, **confidence_kwargs)
    if confidence.should_guess:
        return confidence, None
    next_q = select_next_question(state, all_question_ids)
    return confidence, next_q
