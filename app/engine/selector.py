"""Dynamic question selection via candidate-focused information gain.

IG(Q) = H(current) − E[H | Q] is scored on the current high-mass candidate set
(not a static global ranking). Already-asked questions are never repeated.
Once top confidence exceeds 20%, category-aligned questions (from imported
question.category mappings) are preferred. Near-tied top questions are sampled
for cross-game diversity. Bayesian update itself is unchanged.
"""

from __future__ import annotations

import math
import random
from uuid import UUID

from app.engine.bayesian import bayesian_update, initialize_uniform_priors
from app.engine.cold_start import get_likelihood, is_question_eligible, likelihood_match
from app.engine.confidence import confidence_score, evaluate_confidence
from app.engine.constants import (
    ALL_ANSWERS,
    CHARACTER_CATEGORY_QUESTION_PREFERENCES,
    DEFAULT_CANDIDATE_MASS_FOCUS,
    DEFAULT_CATEGORY_CONFIDENCE_GATE,
    DEFAULT_CATEGORY_IG_BONUS,
    DEFAULT_CONSECUTIVE_DONT_KNOW_CAP,
    DEFAULT_DIVERSITY_MARGIN,
    DEFAULT_DIVERSITY_TOP_K,
    DEFAULT_IG_TIE_THRESHOLD,
    DEFAULT_NEW_QUESTION_MIN_SAMPLES,
    Answer,
)
from app.engine.elimination import eliminate_candidates, entropy
from app.engine.models import ConfidenceResult, GameEngineState, LikelihoodEntry, QuestionRef

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


def focus_candidate_state(
    state: GameEngineState,
    mass_threshold: float = DEFAULT_CANDIDATE_MASS_FOCUS,
    min_keep: int = 2,
) -> GameEngineState:
    """
    Restrict IG scoring to the current high-probability candidate frontier.

    Keeps characters until cumulative posterior mass reaches ``mass_threshold``
    (always at least ``min_keep`` when that many remain). Does not mutate
    ``state`` and does not change Bayesian updates.
    """
    active = [
        (cid, state.probabilities[cid])
        for cid in state.active_character_ids()
        if state.probabilities[cid] > 0
    ]
    if len(active) <= min_keep:
        return state

    active.sort(key=lambda item: item[1], reverse=True)
    kept: dict[UUID, float] = {}
    mass = 0.0
    for cid, p in active:
        kept[cid] = p
        mass += p
        if mass >= mass_threshold and len(kept) >= min_keep:
            break

    if len(kept) >= len(active):
        return state

    total = sum(kept.values())
    if total <= 0:
        return state

    renormalized = {cid: p / total for cid, p in kept.items()}
    return GameEngineState(
        character_ids=list(renormalized.keys()),
        probabilities=renormalized,
        likelihoods=state.likelihoods,
        used_question_ids=set(state.used_question_ids),
        questions_asked=state.questions_asked,
        consecutive_dont_know=state.consecutive_dont_know,
        pre_elimination_top=state.pre_elimination_top,
    )


def inferred_character_category(
    state: GameEngineState,
    character_categories: dict[UUID, str] | None,
) -> str | None:
    """Dominant category by posterior mass among active candidates."""
    if not character_categories:
        return None
    masses: dict[str, float] = {}
    for cid, p in state.probabilities.items():
        cat = character_categories.get(cid)
        if not cat:
            continue
        masses[cat] = masses.get(cat, 0.0) + p
    if not masses:
        return None
    return max(masses, key=masses.get)


def preferred_question_categories(character_category: str | None) -> frozenset[str]:
    if not character_category:
        return frozenset()
    return CHARACTER_CATEGORY_QUESTION_PREFERENCES.get(character_category, frozenset())


def _category_aligned(
    question_id: UUID,
    question_refs: dict[UUID, QuestionRef] | None,
    preferred_cats: frozenset[str],
) -> bool:
    if not preferred_cats or not question_refs:
        return False
    ref = question_refs.get(question_id)
    if ref is None or not ref.category:
        return False
    return ref.category in preferred_cats


def _pick_from_near_best(
    scored: list[tuple[float, int, UUID]],
    *,
    tie_threshold: float,
    diversity_margin: float,
    diversity_top_k: int,
    rng: random.Random | None,
    explore: bool,
) -> UUID:
    """Pick among near-best scores; explore when several questions are close."""
    scored = sorted(scored, key=lambda row: (row[0], row[1]), reverse=True)
    best_score, best_samples, best_qid = scored[0]

    if not explore or len(scored) == 1:
        # Deterministic argmax with sample-size tie-break (legacy behavior).
        chosen = best_qid
        chosen_samples = best_samples
        for score, samples, qid in scored[1:]:
            if abs(score - best_score) <= tie_threshold and samples > chosen_samples:
                chosen = qid
                chosen_samples = samples
            elif score < best_score - tie_threshold:
                break
        return chosen

    pool = [
        (score, samples, qid)
        for score, samples, qid in scored
        if score >= best_score - diversity_margin
    ][: max(1, diversity_top_k)]

    if len(pool) == 1:
        return pool[0][2]

    picker = rng if rng is not None else random.Random()
    # Softmax over shifted scores so near-ties rotate across games.
    max_s = pool[0][0]
    weights = [math.exp((score - max_s) / max(diversity_margin, 1e-6)) for score, _, _ in pool]
    return picker.choices([qid for _, _, qid in pool], weights=weights, k=1)[0]


def select_next_question(
    state: GameEngineState,
    all_question_ids: list[UUID],
    tie_threshold: float = DEFAULT_IG_TIE_THRESHOLD,
    min_samples: int = DEFAULT_NEW_QUESTION_MIN_SAMPLES,
    consecutive_dont_know_cap: int = DEFAULT_CONSECUTIVE_DONT_KNOW_CAP,
    *,
    question_refs: dict[UUID, QuestionRef] | None = None,
    character_categories: dict[UUID, str] | None = None,
    category_confidence_gate: float = DEFAULT_CATEGORY_CONFIDENCE_GATE,
    category_ig_bonus: float = DEFAULT_CATEGORY_IG_BONUS,
    candidate_mass_focus: float = DEFAULT_CANDIDATE_MASS_FOCUS,
    diversity_top_k: int = DEFAULT_DIVERSITY_TOP_K,
    diversity_margin: float = DEFAULT_DIVERSITY_MARGIN,
    rng: random.Random | None = None,
    explore: bool = True,
) -> UUID | None:
    """
    Select the next question from the current candidate frontier.

    - Skips questions in ``state.used_question_ids`` (never repeats)
    - Scores IG on a focused high-mass candidate set (dynamic after each answer)
    - When confidence > ``category_confidence_gate``, boosts questions whose
      imported ``question.category`` matches the inferred character category
    - Among near-tied top scores, samples for cross-game diversity
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

    focus = focus_candidate_state(state, mass_threshold=candidate_mass_focus)
    conf = confidence_score(state)
    preferred_cats = frozenset()
    if conf > category_confidence_gate:
        preferred_cats = preferred_question_categories(
            inferred_character_category(state, character_categories)
        )

    scored: list[tuple[float, int, UUID]] = []
    for qid in unused:
        ig = information_gain(focus, qid)
        score = ig
        if preferred_cats and _category_aligned(qid, question_refs, preferred_cats):
            score += category_ig_bonus
        samples = total_sample_size_for_question(state, qid)
        scored.append((score, samples, qid))

    return _pick_from_near_best(
        scored,
        tie_threshold=tie_threshold,
        diversity_margin=diversity_margin,
        diversity_top_k=diversity_top_k,
        rng=rng,
        explore=explore,
    )


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
    *,
    question_refs: dict[UUID, QuestionRef] | None = None,
    character_categories: dict[UUID, str] | None = None,
    **confidence_kwargs,
) -> tuple[ConfidenceResult, UUID | None]:
    """After processing an answer, return confidence check and optional next question."""
    confidence = evaluate_confidence(state, **confidence_kwargs)
    if confidence.should_guess:
        return confidence, None
    next_q = select_next_question(
        state,
        all_question_ids,
        question_refs=question_refs,
        character_categories=character_categories,
    )
    return confidence, next_q
