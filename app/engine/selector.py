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


def expected_entropy_after_question(
    state: GameEngineState,
    question_id: UUID,
) -> float:
    """
    Expected entropy after asking Q, averaging over 5 possible answers (TDD Section 2.3).
    """
    active = state.active_character_ids()
    probs = {cid: state.probabilities[cid] for cid in active}
    current_h = entropy(probs)

    expected_h = 0.0
    for answer in ALL_ANSWERS:
        # P(answer) = sum over C of P(C) * likelihood_match(C, Q, a)
        p_answer = 0.0
        for cid in active:
            l_cq = get_likelihood(state.likelihoods, cid, question_id)
            p_answer += state.probabilities[cid] * likelihood_match(l_cq, answer.weight)

        if p_answer <= 0:
            continue

        # Simulate update with this answer
        sim_state = GameEngineState(
            character_ids=state.character_ids,
            probabilities=state.copy_probabilities(),
            likelihoods=state.likelihoods,
        )
        sim_probs = bayesian_update(sim_state, question_id, answer)
        h_after = entropy(sim_probs)
        expected_h += p_answer * h_after

    return expected_h


def information_gain(state: GameEngineState, question_id: UUID) -> float:
    active = state.active_character_ids()
    probs = {cid: state.probabilities[cid] for cid in active}
    current_h = entropy(probs)
    expected_h = expected_entropy_after_question(state, question_id)
    return current_h - expected_h


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
    Pick unused question with max information gain (TDD Section 2.3).
    Tie-break by total sample_size (TDD Section 7).
    """
    unused = [
        qid
        for qid in all_question_ids
        if qid not in state.used_question_ids
        and is_question_eligible(qid, state.likelihoods, state.character_ids, min_samples)
    ]

    if not unused:
        # Relax eligibility if all questions are gated
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
