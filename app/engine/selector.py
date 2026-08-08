"""Hierarchical question selection via candidate-focused information gain.

Stage A (broad identity) → Stage B (domain) → Stage C (specific).
IG(Q) is scored only among questions allowed for the current stage.
Bayesian update itself is unchanged.
"""

from __future__ import annotations

import math
import random
from uuid import UUID

from app.engine.bayesian import bayesian_update, initialize_uniform_priors
from app.engine.cold_start import get_likelihood, is_question_eligible, likelihood_match
from app.engine.confidence import evaluate_confidence
from app.engine.constants import (
    ALL_ANSWERS,
    CHARACTER_CATEGORY_QUESTION_PREFERENCES,
    DEFAULT_BROAD_QUESTION_BONUS,
    DEFAULT_CANDIDATE_MASS_FOCUS,
    DEFAULT_CATEGORY_IG_BONUS,
    DEFAULT_CATEGORY_PREFERENCE_THRESHOLD,
    DEFAULT_CATEGORY_REMAIN_MASS,
    DEFAULT_CATEGORY_UNLOCK_THRESHOLD,
    DEFAULT_CONSECUTIVE_DONT_KNOW_CAP,
    DEFAULT_DIVERSITY_MARGIN,
    DEFAULT_DIVERSITY_TOP_K,
    DEFAULT_IG_TIE_THRESHOLD,
    DEFAULT_NEW_QUESTION_MIN_SAMPLES,
    DEFAULT_STAGE_A_EXIT_MARGIN,
    DEFAULT_STAGE_A_EXIT_THRESHOLD,
    DEFAULT_STAGE_C_ENTER_THRESHOLD,
    DEFAULT_STAGE_ORIGIN_EXIT_MARGIN,
    DEFAULT_STAGE_ORIGIN_EXIT_THRESHOLD,
    DOMAIN_QUESTION_CATEGORY_REQUIREMENTS,
    FICTIONAL_CHARACTER_CATEGORIES,
    FORBIDDEN_EARLY_KEYWORDS,
    PROFESSION_SPECIFIC_KEYWORDS,
    STAGE_1_IDENTITY_KEYWORDS,
    STAGE_2_ORIGIN_CATEGORIES,
    STAGE_2_ORIGIN_KEYWORDS,
    STAGE_A_QUESTION_CATEGORIES,
    STAGE_B_QUESTION_CATEGORIES,
    STAGE_C_KEYWORDS,
    STAGE_C_QUESTION_CATEGORIES,
    Answer,
)
from app.engine.elimination import eliminate_candidates, entropy
from app.engine.models import ConfidenceResult, GameEngineState, LikelihoodEntry, QuestionRef

# Outcomes used when estimating E[H | Q]. Includes yes / no / unknown (dont_know).
_IG_ANSWERS: tuple[Answer, ...] = ALL_ANSWERS
# Natural gameplay stages: 1 Identity → 2 Origin → 3 Category → 4 Subcategory
# Legacy aliases A/B/C still accepted by allow-list helpers.
SelectionStage = str  # "1" | "2" | "3" | "4" | "A" | "B" | "C"


def _normalize_stage(stage: SelectionStage) -> SelectionStage:
    if stage in {"A", "1"}:
        return "1"
    if stage in {"O", "2"}:
        return "2"
    if stage in {"B", "3"}:
        return "3"
    if stage in {"C", "4"}:
        return "4"
    return stage


def _text_matches_any(text: str, keywords: frozenset[str]) -> bool:
    return any(kw in text for kw in keywords)


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


def category_probability_mass(
    state: GameEngineState,
    character_categories: dict[UUID, str] | None,
    category: str,
) -> float:
    """Posterior mass for a single character category among active candidates."""
    if not character_categories:
        return 0.0
    return sum(
        p
        for cid, p in state.probabilities.items()
        if character_categories.get(cid) == category
    )


def remaining_character_categories(
    state: GameEngineState,
    character_categories: dict[UUID, str] | None,
    *,
    min_mass: float = DEFAULT_CATEGORY_REMAIN_MASS,
) -> frozenset[str]:
    """Character categories still present in the active candidate pool."""
    if not character_categories:
        return frozenset()
    present: set[str] = set()
    for cid, p in state.probabilities.items():
        if p < min_mass:
            continue
        cat = character_categories.get(cid)
        if cat:
            present.add(cat)
    return frozenset(present)


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


def category_masses(
    state: GameEngineState,
    character_categories: dict[UUID, str] | None,
) -> dict[str, float]:
    if not character_categories:
        return {}
    masses: dict[str, float] = {}
    for cid, p in state.probabilities.items():
        cat = character_categories.get(cid)
        if not cat:
            continue
        masses[cat] = masses.get(cat, 0.0) + p
    return masses


def top_category_masses(
    state: GameEngineState,
    character_categories: dict[UUID, str] | None,
) -> tuple[str | None, float, float]:
    """Return (dominant_category, top_mass, second_mass)."""
    masses = category_masses(state, character_categories)
    if not masses:
        return None, 0.0, 0.0
    ordered = sorted(masses.values(), reverse=True)
    dominant = max(masses, key=masses.get)
    top = ordered[0]
    second = ordered[1] if len(ordered) > 1 else 0.0
    return dominant, top, second


def question_hierarchy_stage(question_ref: QuestionRef | None) -> SelectionStage:
    """Classify a question into natural Stage 1–4 (Identity → Subcategory)."""
    if question_ref is None or not question_ref.category:
        return "4"
    category = question_ref.category
    text = (question_ref.text or "").casefold()

    if _text_matches_any(text, FORBIDDEN_EARLY_KEYWORDS):
        return "4"
    if _text_matches_any(text, STAGE_1_IDENTITY_KEYWORDS):
        return "1"
    if _text_matches_any(text, STAGE_2_ORIGIN_KEYWORDS) or (
        category in STAGE_2_ORIGIN_CATEGORIES
        and not _text_matches_any(text, STAGE_C_KEYWORDS)
        and not _text_matches_any(text, PROFESSION_SPECIFIC_KEYWORDS)
    ):
        # Pure origin / nationality / era — Stage 2
        if category in STAGE_2_ORIGIN_CATEGORIES or _text_matches_any(
            text, STAGE_2_ORIGIN_KEYWORDS
        ):
            return "2"

    if category in STAGE_C_QUESTION_CATEGORIES:
        return "4"
    if category in STAGE_B_QUESTION_CATEGORIES:
        if _text_matches_any(text, STAGE_C_KEYWORDS) or _text_matches_any(
            text, PROFESSION_SPECIFIC_KEYWORDS
        ):
            return "4"
        return "3"
    if category in STAGE_A_QUESTION_CATEGORIES:
        # Non-identity Stage-A metadata (e.g. hair color) waits for later stages.
        return "4"
    return "4"


def resolve_selection_stage(
    state: GameEngineState,
    character_categories: dict[UUID, str] | None,
    *,
    stage_a_exit_threshold: float = DEFAULT_STAGE_A_EXIT_THRESHOLD,
    stage_a_exit_margin: float = DEFAULT_STAGE_A_EXIT_MARGIN,
    stage_origin_exit_threshold: float = DEFAULT_STAGE_ORIGIN_EXIT_THRESHOLD,
    stage_origin_exit_margin: float = DEFAULT_STAGE_ORIGIN_EXIT_MARGIN,
    stage_c_enter_threshold: float = DEFAULT_STAGE_C_ENTER_THRESHOLD,
) -> tuple[SelectionStage, str | None]:
    """
    Determine natural questioning stage from category posterior mass.

    Missing category mappings → Stage 1 only (fail safe).
    """
    if not character_categories:
        return "1", None

    dominant, top, second = top_category_masses(state, character_categories)
    if dominant is None or top < stage_a_exit_threshold or (top - second) < stage_a_exit_margin:
        return "1", dominant

    # Stage 2 Origin until the dominant category is clearer.
    if top < stage_origin_exit_threshold or (top - second) < stage_origin_exit_margin:
        return "2", dominant

    if top >= stage_c_enter_threshold:
        return "4", dominant
    return "3", dominant


def is_question_relevant_to_candidates(
    question_id: UUID,
    question_refs: dict[UUID, QuestionRef] | None,
    remaining_categories: frozenset[str],
) -> bool:
    """
    Return False for domain questions whose required character categories
    are absent from the current candidate set.
    """
    if not question_refs:
        return False  # fail closed without metadata
    ref = question_refs.get(question_id)
    if ref is None or not ref.category:
        return False
    required = DOMAIN_QUESTION_CATEGORY_REQUIREMENTS.get(ref.category)
    if required is None:
        return True
    if not remaining_categories:
        return False
    return bool(required & remaining_categories)


def is_domain_category_unlocked(
    question_category: str | None,
    state: GameEngineState,
    character_categories: dict[UUID, str] | None,
    *,
    unlock_threshold: float = DEFAULT_CATEGORY_UNLOCK_THRESHOLD,
) -> bool:
    """
    Domain questions unlock only after a matching character category's mass
    exceeds ``unlock_threshold``. Missing mappings fail closed.
    """
    if not question_category:
        return False
    required = DOMAIN_QUESTION_CATEGORY_REQUIREMENTS.get(question_category)
    if required is None:
        return True
    if not character_categories:
        return False
    return any(
        category_probability_mass(state, character_categories, cat) > unlock_threshold
        for cat in required
    )


def _domain_matches_dominant(
    question_category: str | None,
    dominant_category: str | None,
) -> bool:
    if not question_category or not dominant_category:
        return False
    required = DOMAIN_QUESTION_CATEGORY_REQUIREMENTS.get(question_category)
    if required is None:
        # Non-domain Stage 4 (Profession/Awards): allowed once a dominant exists.
        return True
    return dominant_category in required


def _anime_requires_fictional_dominant(dominant_category: str | None) -> bool:
    return dominant_category == "Anime" and dominant_category in FICTIONAL_CHARACTER_CATEGORIES


def _profession_or_award_allowed(dominant_category: str | None, question_category: str | None) -> bool:
    """Profession / Awards only after domain ID, and only for categories that prefer them."""
    if not dominant_category or not question_category:
        return False
    preferred = preferred_question_categories(dominant_category)
    return question_category in preferred


def is_question_allowed_for_stage(
    question_ref: QuestionRef | None,
    *,
    stage: SelectionStage,
    dominant_category: str | None,
) -> bool:
    """Natural gameplay allow-list for Stage 1 / 2 / 3 / 4."""
    stage = _normalize_stage(stage)
    q_stage = _normalize_stage(question_hierarchy_stage(question_ref))
    category = question_ref.category if question_ref else None
    text = (question_ref.text or "").casefold() if question_ref else ""

    if _text_matches_any(text, FORBIDDEN_EARLY_KEYWORDS) and stage != "4":
        return False

    if stage == "1":
        return q_stage == "1"

    if stage == "2":
        return q_stage in {"1", "2"}

    if stage == "3":
        if q_stage in {"1", "2"}:
            return True
        if q_stage != "3":
            return False
        if category == "Anime":
            return _anime_requires_fictional_dominant(dominant_category)
        return _domain_matches_dominant(category, dominant_category)

    # Stage 4 — subcategory / specific
    if any(kw in text for kw in PROFESSION_SPECIFIC_KEYWORDS):
        return _profession_or_award_allowed(dominant_category, "Profession")
    if category in {"Profession", "Awards", "Relationships", "Time period"}:
        return _profession_or_award_allowed(dominant_category, category)

    if q_stage in {"1", "2"}:
        return True
    if category == "Anime":
        return _anime_requires_fictional_dominant(dominant_category)
    if category in {"Sports", "Movies"}:
        return _domain_matches_dominant(category, dominant_category)
    return _domain_matches_dominant(category, dominant_category)


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
    category_confidence_gate: float = DEFAULT_CATEGORY_PREFERENCE_THRESHOLD,
    category_preference_threshold: float | None = None,
    category_unlock_threshold: float = DEFAULT_CATEGORY_UNLOCK_THRESHOLD,
    stage_a_exit_threshold: float | None = None,
    stage_a_exit_margin: float = DEFAULT_STAGE_A_EXIT_MARGIN,
    stage_c_enter_threshold: float = DEFAULT_STAGE_C_ENTER_THRESHOLD,
    stage_origin_exit_threshold: float = DEFAULT_STAGE_ORIGIN_EXIT_THRESHOLD,
    stage_origin_exit_margin: float = DEFAULT_STAGE_ORIGIN_EXIT_MARGIN,
    category_ig_bonus: float = DEFAULT_CATEGORY_IG_BONUS,
    broad_question_bonus: float = DEFAULT_BROAD_QUESTION_BONUS,
    candidate_mass_focus: float = DEFAULT_CANDIDATE_MASS_FOCUS,
    category_remain_mass: float = DEFAULT_CATEGORY_REMAIN_MASS,
    diversity_top_k: int = DEFAULT_DIVERSITY_TOP_K,
    diversity_margin: float = DEFAULT_DIVERSITY_MARGIN,
    rng: random.Random | None = None,
    explore: bool = True,
) -> UUID | None:
    """
    Select the next question using natural Stage 1 → 2 → 3 → 4 gating.

    - Stage 1: identity only
    - Stage 2: origin (place / era)
    - Stage 3: category / domain after enough confidence
    - Stage 4: subcategory / specific
    - Missing mappings → Stage 1 identity-only (fail safe)
    """
    del consecutive_dont_know_cap  # reserved for future dont_know streak policy
    preference_threshold = (
        category_confidence_gate
        if category_preference_threshold is None
        else category_preference_threshold
    )
    a_exit = (
        category_unlock_threshold
        if stage_a_exit_threshold is None
        else stage_a_exit_threshold
    )

    unused = [
        qid
        for qid in all_question_ids
        if qid not in state.used_question_ids
        and is_question_eligible(qid, state.likelihoods, state.character_ids, min_samples)
    ]

    if not unused:
        unused = [qid for qid in all_question_ids if qid not in state.used_question_ids]

    if not unused:
        return None

    focus = focus_candidate_state(state, mass_threshold=candidate_mass_focus)

    # Legacy callers (no hierarchy metadata) → pure information-gain selection.
    if question_refs is None:
        scored_legacy: list[tuple[float, int, UUID]] = [
            (
                information_gain(focus, qid),
                total_sample_size_for_question(state, qid),
                qid,
            )
            for qid in unused
        ]
        return _pick_from_near_best(
            scored_legacy,
            tie_threshold=tie_threshold,
            diversity_margin=diversity_margin,
            diversity_top_k=diversity_top_k,
            rng=rng,
            explore=explore,
        )

    remaining_cats = remaining_character_categories(
        focus if character_categories else state,
        character_categories,
        min_mass=category_remain_mass,
    )

    # Hierarchy engaged but category map missing → Stage 1 identity-only (fail safe).
    if not character_categories:
        broad_only = [
            qid
            for qid in unused
            if question_hierarchy_stage(question_refs.get(qid)) == "1"
        ]
        if not broad_only:
            return None
        scored_safe: list[tuple[float, int, UUID]] = []
        for qid in broad_only:
            scored_safe.append(
                (
                    information_gain(focus, qid) + broad_question_bonus,
                    total_sample_size_for_question(state, qid),
                    qid,
                )
            )
        return _pick_from_near_best(
            scored_safe,
            tie_threshold=tie_threshold,
            diversity_margin=diversity_margin,
            diversity_top_k=diversity_top_k,
            rng=rng,
            explore=explore,
        )

    stage, dominant = resolve_selection_stage(
        focus,
        character_categories,
        stage_a_exit_threshold=a_exit,
        stage_a_exit_margin=stage_a_exit_margin,
        stage_origin_exit_threshold=stage_origin_exit_threshold,
        stage_origin_exit_margin=stage_origin_exit_margin,
        stage_c_enter_threshold=stage_c_enter_threshold,
    )

    relevant: list[UUID] = []
    for qid in unused:
        ref = question_refs.get(qid)
        if ref is None:
            continue
        if not is_question_relevant_to_candidates(qid, question_refs, remaining_cats):
            # Stage 1–2 questions are never domain-gated by remaining_cats
            if question_hierarchy_stage(ref) not in {"1", "2"}:
                continue
        if not is_question_allowed_for_stage(
            ref, stage=stage, dominant_category=dominant
        ):
            continue
        relevant.append(qid)

    if not relevant:
        # Always fall back to Stage 1 identity — never open the floodgates.
        relevant = [
            qid
            for qid in unused
            if question_hierarchy_stage(question_refs.get(qid)) == "1"
        ]
    if not relevant:
        return None

    preferred_cats = frozenset()
    if dominant is not None:
        mass = category_probability_mass(focus, character_categories, dominant)
        if mass > preference_threshold:
            preferred_cats = preferred_question_categories(dominant)

    scored: list[tuple[float, int, UUID]] = []
    for qid in relevant:
        ig = information_gain(focus, qid)
        score = ig
        ref = question_refs.get(qid)
        q_stage = question_hierarchy_stage(ref)
        if preferred_cats and _category_aligned(qid, question_refs, preferred_cats):
            score += category_ig_bonus
        if stage in {"1", "2"} and q_stage in {"1", "2"}:
            score += broad_question_bonus
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
