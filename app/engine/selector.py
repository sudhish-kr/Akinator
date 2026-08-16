"""Hierarchical question selection via candidate-focused information gain.

Stage A (broad identity) → Stage B (domain) → Stage C (specific).
IG(Q) is scored only among questions allowed for the current stage.
Bayesian update itself is unchanged.
"""

from __future__ import annotations

import logging
import math
import random
from dataclasses import dataclass
from uuid import UUID

from app.engine.bayesian import bayesian_update, initialize_priors, initialize_uniform_priors
from app.engine.cold_start import get_likelihood, is_question_eligible, likelihood_match
from app.engine.confidence import evaluate_confidence
from app.engine.constraints import apply_answer_constraints
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
    DEFAULT_EARLY_PRIORITY_LOCK_QUESTIONS,
    DEFAULT_IG_TIE_THRESHOLD,
    DEFAULT_LOW_PRIORITY_AGE_IG_MARGIN,
    DEFAULT_LOW_PRIORITY_AGE_MIN_IG,
    DEFAULT_MAX_NATIONALITY_QUESTIONS,
    DEFAULT_MAX_UNKNOWN_FRACTION,
    DEFAULT_MIN_USEFUL_IG,
    DEFAULT_MIN_USEFUL_SPREAD,
    DEFAULT_NEAR_DUPLICATE_PENALTY,
    DEFAULT_NEW_QUESTION_MIN_SAMPLES,
    DEFAULT_SEPARATION_CLOSE_MARGIN,
    DEFAULT_SEPARATION_DOMINANT_TOP,
    DEFAULT_SEPARATION_MAX_EFFECTIVE_N,
    DEFAULT_SEPARATION_MIN_DUEL_MASS,
    DEFAULT_SEPARATION_MIN_LIKELIHOOD_GAP,
    DEFAULT_SEPARATION_MIN_RUNNER_P,
    DEFAULT_SEPARATION_WEIGHT,
    DEFAULT_SPECIFICITY_ALIGN_WEIGHT,
    DEFAULT_SPECIFICITY_NARROW_EFFECTIVE_N,
    DEFAULT_CONTEXT_WEIGHT,
    DEFAULT_USELESS_IG_PENALTY,
    DEFAULT_SATURATED_LIKELIHOOD_SPREAD,
    DEFAULT_SATURATED_QUESTION_PENALTY,
    DEFAULT_SPECIFICITY_PENALTY,
    DEFAULT_STAGE_A_EXIT_MARGIN,
    DEFAULT_STAGE_A_EXIT_THRESHOLD,
    DEFAULT_STAGE_C_ENTER_THRESHOLD,
    DEFAULT_STAGE_ORIGIN_EXIT_MARGIN,
    DEFAULT_STAGE_ORIGIN_EXIT_THRESHOLD,
    DOMAIN_QUESTION_CATEGORY_REQUIREMENTS,
    AKINATOR_FILLER_KEYWORDS,
    ALIVE_STATUS_KEYWORDS,
    EARLY_PRIORITY_KEYWORD_GROUPS,
    GENDER_KEYWORDS,
    INDIAN_REGION_KEYWORDS,
    REALITY_KEYWORDS,
    FICTIONAL_CHARACTER_CATEGORIES,
    FORBIDDEN_EARLY_KEYWORDS,
    LOW_PRIORITY_AGE_KEYWORDS,
    MAJOR_CATEGORY_KEYWORDS,
    NATIONALITY_PLACE_KEYWORDS,
    NICHE_TOPIC_REQUIRED_CATEGORIES,
    PROFESSION_SPECIFIC_KEYWORDS,
    DEFAULT_SPLIT_NO_LIKELIHOOD,
    DEFAULT_SPLIT_YES_LIKELIHOOD,
    SPORT_SPECIFIC_KEYWORDS,
    SPORT_SUBTYPE_KEYWORDS,
    STAGE_1_IDENTITY_KEYWORDS,
    STAGE_2_ORIGIN_CATEGORIES,
    STAGE_2_ORIGIN_KEYWORDS,
    STAGE_A_QUESTION_CATEGORIES,
    STAGE_B_QUESTION_CATEGORIES,
    STAGE_C_KEYWORDS,
    STAGE_C_QUESTION_CATEGORIES,
    Answer,
)
from app.engine.elimination import eliminate_candidates, entropy, top_two
from app.engine.models import ConfidenceResult, GameEngineState, LikelihoodEntry, QuestionRef
from app.engine.question_consistency import (
    infer_established_facts,
    india_relevant_score_bonus,
    is_logically_valid_question,
)

# Outcomes used when estimating E[H | Q]. Includes yes / no / unknown (dont_know).
_IG_ANSWERS: tuple[Answer, ...] = ALL_ANSWERS
# Natural gameplay stages: 1 Identity → 2 Origin → 3 Category → 4 Subcategory
# Legacy aliases A/B/C still accepted by allow-list helpers.
SelectionStage = str  # "1" | "2" | "3" | "4" | "A" | "B" | "C"

logger = logging.getLogger(__name__)


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


def _text_matches_any(text: str, keywords: frozenset[str] | set[str]) -> bool:
    return any(kw in text for kw in keywords)


def niche_topic_keys(question_ref: QuestionRef | None) -> frozenset[str]:
    """Return niche topic keys present in the question text."""
    if question_ref is None:
        return frozenset()
    text = (question_ref.text or "").casefold()
    return frozenset(key for key in NICHE_TOPIC_REQUIRED_CATEGORIES if key in text)


def is_hard_gated_niche(question_ref: QuestionRef | None) -> bool:
    """True for franchise / occupation / niche topics that must wait for Stage 4."""
    if question_ref is None:
        return False
    text = (question_ref.text or "").casefold()
    if is_major_category_question(question_ref):
        return False
    if _text_matches_any(text, FORBIDDEN_EARLY_KEYWORDS):
        return True
    if is_sport_subtype_question(question_ref) or is_sport_specific_question(question_ref):
        return True
    if is_low_priority_age_question(question_ref):
        return True
    if is_akinator_filler_question(question_ref) or is_regional_state_question(question_ref):
        return True
    return bool(niche_topic_keys(question_ref))


def is_major_category_question(question_ref: QuestionRef | None) -> bool:
    """Level-2 broad domain questions (athlete / anime / scientist / …)."""
    if question_ref is None:
        return False
    if is_sport_subtype_question(question_ref) or is_sport_specific_question(question_ref):
        return False
    if is_low_priority_age_question(question_ref):
        return False
    text = (question_ref.text or "").casefold()
    if _text_matches_any(text, FORBIDDEN_EARLY_KEYWORDS) and "famous for" not in text:
        if not _text_matches_any(text, MAJOR_CATEGORY_KEYWORDS):
            return False
    if _text_matches_any(text, MAJOR_CATEGORY_KEYWORDS):
        return True
    # Short broad domain probes (legacy tests use "Athlete?" / "Scientist?").
    if text.rstrip("?") in {"athlete", "scientist", "musician", "politician"}:
        return True
    return False


def is_sport_subtype_question(question_ref: QuestionRef | None) -> bool:
    """Level-3 sport questions (cricket / boxing / skating / …)."""
    if question_ref is None:
        return False
    # Role questions often mention the sport ("wickets in cricket") — those are
    # specifics, not a second sport-subtype to chain after cricket/football.
    if is_sport_specific_question(question_ref):
        return False
    text = (question_ref.text or "").casefold()
    if "famous for" in text and (question_ref.category or "") == "Sports":
        return True
    return _text_matches_any(text, SPORT_SUBTYPE_KEYWORDS)


def is_sport_specific_question(question_ref: QuestionRef | None) -> bool:
    """Level-4 ultra-specific sports details (batsman / play for India / …)."""
    if question_ref is None:
        return False
    text = (question_ref.text or "").casefold()
    return _text_matches_any(text, SPORT_SPECIFIC_KEYWORDS)


def has_asked_major_sports_category(
    used_question_ids: set[UUID] | frozenset[UUID],
    question_refs: dict[UUID, QuestionRef] | None,
) -> bool:
    if not question_refs:
        return False
    for qid in used_question_ids:
        ref = question_refs.get(qid)
        if ref is None:
            continue
        text = (ref.text or "").casefold()
        if is_sport_subtype_question(ref) or is_sport_specific_question(ref):
            continue
        if "sports player" in text or "athlete" in text or "sportsperson" in text:
            return True
        if ref.category == "Sports" and is_major_category_question(ref):
            return True
    return False


def should_delay_guess_for_sport_split(
    state: GameEngineState,
    question_refs: dict[UUID, QuestionRef] | None,
    character_categories: dict[UUID, str] | None,
) -> bool:
    """Keep asking when several athletes remain indistinguishable.

    Generic athlete/India/man answers must not guess Dhoni (or Kohli)
    until a sport subtype — and for cricket, a role — has been asked.
    """
    if not question_refs or not character_categories:
        return False
    sports = [
        cid
        for cid, p in state.probabilities.items()
        if p > 0 and character_categories.get(cid) == "Sports"
    ]
    if len(sports) < 2:
        return False
    used = state.used_question_ids
    subtype_asked = any(
        is_sport_subtype_question(question_refs.get(qid)) for qid in used
    )
    if not subtype_asked:
        return True
    cricket_yes = False
    for qid, ans in state.answer_log.items():
        ref = question_refs.get(qid)
        if ref is None:
            continue
        text = (ref.text or "").casefold()
        if "cricket" in text and ans in {"yes", "probably_yes"}:
            cricket_yes = True
            break
    if cricket_yes and not any(
        is_sport_specific_question(question_refs.get(qid)) for qid in used
    ):
        return True
    return False


def has_asked_major_for_dominant(
    dominant_category: str | None,
    used_question_ids: set[UUID] | frozenset[UUID],
    question_refs: dict[UUID, QuestionRef] | None,
) -> bool:
    """True once a Level-2 major question for the dominant domain was asked."""
    if not dominant_category or not question_refs:
        return False
    if dominant_category == "Sports":
        return has_asked_major_sports_category(used_question_ids, question_refs)
    for qid in used_question_ids:
        ref = question_refs.get(qid)
        if ref is None or not is_major_category_question(ref):
            continue
        if is_sport_subtype_question(ref) or is_sport_specific_question(ref):
            continue
        if _domain_matches_dominant(ref.category, dominant_category):
            return True
        text = (ref.text or "").casefold()
        if dominant_category == "Anime" and "anime" in text:
            return True
        if dominant_category == "Movies" and (
            "movie" in text or "superhero" in text or "actor" in text
        ):
            return True
    return False


def last_asked_ref(
    used_question_ids: set[UUID] | frozenset[UUID] | list[UUID],
    question_refs: dict[UUID, QuestionRef] | None,
    *,
    asked_order: list[UUID] | None = None,
) -> QuestionRef | None:
    if not question_refs:
        return None
    order = list(asked_order) if asked_order else list(used_question_ids)
    if not order:
        return None
    for qid in reversed(order):
        ref = question_refs.get(qid)
        if ref is not None:
            return ref
    return None


def flow_level(question_ref: QuestionRef | None) -> int:
    """
    Player-facing hierarchy level:
      1 identity/origin → 2 major category → 3 subcategory → 4 specific
    """
    if question_ref is None:
        return 1
    if is_sport_specific_question(question_ref):
        return 4
    if is_sport_subtype_question(question_ref):
        return 3
    stage = _normalize_stage(question_hierarchy_stage(question_ref))
    if is_hard_gated_niche(question_ref) or stage == "4":
        return 3
    if is_major_category_question(question_ref) or stage == "3":
        return 2
    return 1


def deepest_flow_reached(
    used_question_ids: set[UUID] | frozenset[UUID] | None,
    question_refs: dict[UUID, QuestionRef] | None,
) -> int:
    """Highest player-facing hierarchy level already visited this game."""
    if not used_question_ids or not question_refs:
        return 1
    deepest = 1
    for qid in used_question_ids:
        ref = question_refs.get(qid)
        if ref is not None:
            deepest = max(deepest, flow_level(ref))
    return deepest


def respects_one_level_step(
    question_ref: QuestionRef | None,
    *,
    previous_ref: QuestionRef | None,
    resolve_stage: SelectionStage,
    used_question_ids: set[UUID] | frozenset[UUID] | None = None,
    question_refs: dict[UUID, QuestionRef] | None = None,
) -> bool:
    """Never descend more than one hierarchy level beyond the deepest reached."""
    del resolve_stage  # resolve stage gates eligibility separately
    if question_ref is None:
        return False
    if previous_ref is None and not used_question_ids:
        return True
    ceiling = deepest_flow_reached(used_question_ids, question_refs)
    if previous_ref is not None:
        ceiling = max(ceiling, flow_level(previous_ref))
    return flow_level(question_ref) <= ceiling + 1


def niche_topic_is_relevant(
    question_ref: QuestionRef | None,
    dominant_category: str | None,
) -> bool:
    """Niche Stage-4 topics require a matching dominant character category."""
    keys = niche_topic_keys(question_ref)
    if not keys:
        # Forbidden-early without explicit niche map: allow only with a dominant cat.
        return dominant_category is not None
    if dominant_category is None:
        return False
    for key in keys:
        allowed = NICHE_TOPIC_REQUIRED_CATEGORIES.get(key)
        if allowed is not None and dominant_category not in allowed:
            return False
    return True


def is_low_priority_age_question(question_ref: QuestionRef | None) -> bool:
    """True for baby/toddler/teen/elderly-style age questions."""
    if question_ref is None:
        return False
    text = (question_ref.text or "").casefold()
    return _text_matches_any(text, LOW_PRIORITY_AGE_KEYWORDS)


def is_alive_status_question(question_ref: QuestionRef | None) -> bool:
    """True for alive / dead status questions."""
    if question_ref is None:
        return False
    text = (question_ref.text or "").casefold()
    return _text_matches_any(text, ALIVE_STATUS_KEYWORDS)


def is_reality_question(question_ref: QuestionRef | None) -> bool:
    """True for real-person vs made-up (not 'made-up guild')."""
    if question_ref is None:
        return False
    text = (question_ref.text or "").casefold()
    if "guild" in text:
        return False
    return _text_matches_any(text, REALITY_KEYWORDS)


def is_gender_question(question_ref: QuestionRef | None) -> bool:
    """True for man / woman identity questions."""
    if question_ref is None:
        return False
    text = (question_ref.text or "").casefold()
    return _text_matches_any(text, GENDER_KEYWORDS)


def is_akinator_filler_question(question_ref: QuestionRef | None) -> bool:
    """Vague catalog questions Akinator would skip (ball/jersey/'about sports')."""
    if question_ref is None:
        return False
    text = (question_ref.text or "").casefold()
    return _text_matches_any(text, AKINATOR_FILLER_KEYWORDS)


def is_regional_state_question(question_ref: QuestionRef | None) -> bool:
    """Indian state/city probes — too specific for the opening/country tree."""
    if question_ref is None:
        return False
    text = (question_ref.text or "").casefold()
    if "movie" in text or "cinema" in text or "film" in text:
        return False
    return _text_matches_any(text, INDIAN_REGION_KEYWORDS)


def is_origin_question(question_ref: QuestionRef | None) -> bool:
    """True for nationality / era origin questions (Stage 2)."""
    return question_hierarchy_stage(question_ref) == "2"


def is_nationality_place_question(question_ref: QuestionRef | None) -> bool:
    """True for country / region place questions (India, Japan, Europe, …)."""
    if question_ref is None:
        return False
    if is_regional_state_question(question_ref):
        return False
    category = (question_ref.category or "").strip()
    if category == "Nationality":
        return True
    text = (question_ref.text or "").casefold()
    return _text_matches_any(text, NATIONALITY_PLACE_KEYWORDS)


def _has_asked_matching(
    used_question_ids: set[UUID] | frozenset[UUID],
    question_refs: dict[UUID, QuestionRef] | None,
    predicate,
) -> bool:
    if not question_refs:
        return False
    return any(predicate(question_refs.get(qid)) for qid in used_question_ids)


def _india_affirmed(
    state: GameEngineState,
    question_refs: dict[UUID, QuestionRef] | None,
) -> bool:
    """True when the player said yes/probably to an India place question."""
    if not question_refs:
        return False
    for qid, ans in state.answer_log.items():
        if ans not in {"yes", "probably_yes"}:
            continue
        ref = question_refs.get(qid)
        text = (ref.text or "").casefold() if ref else ""
        if "from india" in text:
            return True
    return False


def _place_affirmed(
    state: GameEngineState,
    question_refs: dict[UUID, QuestionRef] | None,
) -> bool:
    """True when any nationality/place question was affirmed (locks geography tree)."""
    if not question_refs:
        return False
    for qid, ans in state.answer_log.items():
        if ans not in {"yes", "probably_yes"}:
            continue
        if is_nationality_place_question(question_refs.get(qid)):
            return True
    return False


def _nationality_question_count(
    state: GameEngineState,
    question_refs: dict[UUID, QuestionRef] | None,
) -> int:
    if not question_refs:
        return 0
    return sum(
        1
        for qid in state.used_question_ids
        if is_nationality_place_question(question_refs.get(qid))
    )


def _last_nationality_answer(
    state: GameEngineState,
    question_refs: dict[UUID, QuestionRef] | None,
) -> str | None:
    """Most recent nationality answer from asked order (or answer_log fallback)."""
    if not question_refs:
        return None
    order = list(state.asked_question_order or ())
    for qid in reversed(order):
        if is_nationality_place_question(question_refs.get(qid)):
            return state.answer_log.get(qid)
    # Fallback when order missing: arbitrary last from log.
    last: str | None = None
    for qid, ans in state.answer_log.items():
        if is_nationality_place_question(question_refs.get(qid)):
            last = ans
    return last


def _wants_another_nationality(
    state: GameEngineState,
    question_refs: dict[UUID, QuestionRef] | None,
    *,
    max_nationality: int = DEFAULT_MAX_NATIONALITY_QUESTIONS,
) -> bool:
    """Allow follow-up country Qs after NO/don't-know; never after a place YES."""
    if not question_refs:
        return False
    if _place_affirmed(state, question_refs):
        return False
    count = _nationality_question_count(state, question_refs)
    if count >= max_nationality:
        return False
    if count == 0:
        return True
    last = _last_nationality_answer(state, question_refs)
    return last in {"no", "probably_no", "dont_know"}


def early_question_priority_bonus(question_ref: QuestionRef | None) -> float:
    """Weighted bonus for natural early-game questions (highest match wins)."""
    if question_ref is None:
        return 0.0
    if is_hard_gated_niche(question_ref):
        return 0.0
    text = (question_ref.text or "").casefold()
    for patterns, bonus in EARLY_PRIORITY_KEYWORD_GROUPS:
        if any(pat in text for pat in patterns):
            return float(bonus)
    return 0.0


def specificity_penalty(question_ref: QuestionRef | None, stage: SelectionStage) -> float:
    """Penalize overly specific questions relative to the current phase."""
    stage_n = _normalize_stage(stage)
    q_stage = _normalize_stage(question_hierarchy_stage(question_ref))
    if is_hard_gated_niche(question_ref):
        return DEFAULT_SPECIFICITY_PENALTY * (1.5 if stage_n != "4" else 1.0)
    if q_stage == "4" and stage_n in {"1", "2", "3"}:
        return DEFAULT_SPECIFICITY_PENALTY
    if q_stage == "3" and stage_n in {"1", "2"}:
        return DEFAULT_SPECIFICITY_PENALTY * 0.5
    return 0.0


def near_duplicate_penalty(
    question_ref: QuestionRef | None,
    previous_ref: QuestionRef | None,
) -> float:
    """Penalize questions that largely repeat the previous question's topic."""
    if question_ref is None or previous_ref is None:
        return 0.0
    cur = (question_ref.text or "").casefold()
    prev = (previous_ref.text or "").casefold()
    if not cur or not prev:
        return 0.0
    # Shared content words longer than 3 chars (ignore boilerplate).
    stop = {
        "this",
        "that",
        "they",
        "them",
        "their",
        "from",
        "with",
        "have",
        "does",
        "are",
        "is",
        "the",
        "a",
        "an",
        "or",
        "and",
        "for",
        "person",
        "character",
        "your",
    }
    cur_words = {w for w in cur.replace("?", " ").split() if len(w) > 3 and w not in stop}
    prev_words = {w for w in prev.replace("?", " ").split() if len(w) > 3 and w not in stop}
    if not cur_words or not prev_words:
        return 0.0
    overlap = cur_words & prev_words
    if len(overlap) >= 2 or (len(overlap) == 1 and overlap & cur_words and len(cur_words) <= 3):
        return DEFAULT_NEAR_DUPLICATE_PENALTY
    return 0.0


def should_defer_low_priority_age(
    *,
    questions_asked: int,
    stage: SelectionStage,
    ig: float,
    best_non_low_ig: float | None,
    lock_questions: int = DEFAULT_EARLY_PRIORITY_LOCK_QUESTIONS,
    min_ig: float = DEFAULT_LOW_PRIORITY_AGE_MIN_IG,
    ig_margin: float = DEFAULT_LOW_PRIORITY_AGE_IG_MARGIN,
) -> bool:
    """
    Defer niche age questions until after the first broad turns and category
    detection, and only keep them when IG is meaningfully competitive.
    """
    stage_n = _normalize_stage(stage)
    if questions_asked < lock_questions:
        return True
    if stage_n in {"1", "2", "3"}:
        return True
    if ig < min_ig:
        return True
    if best_non_low_ig is not None and ig + ig_margin < best_non_low_ig:
        return True
    return False



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

    Algebraically identical to simulating bayesian_update per answer; avoids
    copying GameEngineState on every candidate question.
    """
    active = state.active_character_ids()
    if not active:
        return 0.0

    priors = [state.probabilities[cid] for cid in active]
    likes = [get_likelihood(state.likelihoods, cid, question_id) for cid in active]

    weighted: list[tuple[float, float]] = []
    for answer in _IG_ANSWERS:
        weight = answer.weight
        p_answer = 0.0
        masses: list[float] = []
        masses_append = masses.append
        for prior, lik in zip(priors, likes, strict=True):
            mass = prior * likelihood_match(lik, weight)
            p_answer += mass
            masses_append(mass)

        if p_answer <= 0:
            continue

        inv = 1.0 / p_answer
        h = 0.0
        for mass in masses:
            p = mass * inv
            if p > 0:
                h -= p * math.log2(p)
        weighted.append((p_answer, h))

    total_p = sum(weight for weight, _ in weighted)
    if total_p <= 0:
        return entropy({cid: state.probabilities[cid] for cid in active})

    return sum((weight / total_p) * h for weight, h in weighted)


def information_gain(
    state: GameEngineState,
    question_id: UUID,
    *,
    current_entropy: float | None = None,
) -> float:
    """IG(Q) = H(current) − expected entropy after asking Q."""
    if current_entropy is None:
        active = state.active_character_ids()
        current_entropy = entropy({cid: state.probabilities[cid] for cid in active})
    return current_entropy - expected_entropy_after_question(state, question_id)


def remaining_likelihood_spread(state: GameEngineState, question_id: UUID) -> float:
    """max L − min L among remaining (active) candidates. Unknown defaults to 0.5."""
    likes = [
        get_likelihood(state.likelihoods, cid, question_id)
        for cid in state.active_character_ids()
    ]
    if not likes:
        return 0.0
    return max(likes) - min(likes)


def candidate_split_counts(
    state: GameEngineState,
    question_id: UUID,
    *,
    yes_cutoff: float = DEFAULT_SPLIT_YES_LIKELIHOOD,
    no_cutoff: float = DEFAULT_SPLIT_NO_LIKELIHOOD,
    min_samples: int = 5,
) -> tuple[int, int, int]:
    """Known YES / known NO / UNKNOWN mapping counts on the CURRENT candidate pool.

    Missing rows and near-neutral L are UNKNOWN — never treated as YES or NO.
    """
    yes_n = no_n = unk_n = 0
    for cid in state.active_character_ids():
        entry = state.likelihoods.get((cid, question_id))
        if entry is None or int(entry.sample_size) < min_samples:
            unk_n += 1
            continue
        lik = float(entry.likelihood)
        if lik >= yes_cutoff:
            yes_n += 1
        elif lik <= no_cutoff:
            no_n += 1
        else:
            unk_n += 1
    return yes_n, no_n, unk_n


def is_useful_split_on_pool(
    state: GameEngineState,
    question_id: UUID,
    *,
    ig: float,
    min_ig: float = DEFAULT_MIN_USEFUL_IG,
    min_spread: float = DEFAULT_MIN_USEFUL_SPREAD,
    max_unknown: float = DEFAULT_MAX_UNKNOWN_FRACTION,
    min_samples: int = 5,
) -> bool:
    """True when Q actually divides CURRENT remaining candidates."""
    yes_n, no_n, unk_n = candidate_split_counts(
        state, question_id, min_samples=min_samples
    )
    total = yes_n + no_n + unk_n
    if total <= 0:
        return False
    if min(yes_n, no_n) == 0:
        return False
    mapped = yes_n + no_n
    spread = remaining_likelihood_spread(state, question_id)
    if spread < min_spread:
        return False
    # A mapped YES/NO split is useful even when most rows are UNKNOWN.
    # Unknown stays unknown in Bayes; it must not hide wicketkeeper/opener/etc.
    if mapped >= 3:
        return True
    if (unk_n / total) > max_unknown:
        return False
    if ig < min_ig:
        return False
    return True


def is_askable_on_pool(
    state: GameEngineState,
    question_id: UUID,
    *,
    ig: float,
    question_ref: QuestionRef | None,
    subtype_already_asked: bool,
    min_ig: float = DEFAULT_MIN_USEFUL_IG,
    min_samples: int = 5,
) -> bool:
    """Keep only questions that split the pool or complete the category tree.

    Filler / appearance / high-unknown trivia is never kept without a real split.
    A sport subtype that some remaining candidates match may still be asked once
    so cricket/football can unlock role questions.
    """
    if is_useful_split_on_pool(
        state, question_id, ig=ig, min_ig=min_ig, min_samples=min_samples
    ):
        return True
    if is_akinator_filler_question(question_ref):
        return False
    category = (question_ref.category or "") if question_ref else ""
    if category == "Physical appearance":
        return False
    yes_n, no_n, unk_n = candidate_split_counts(
        state, question_id, min_samples=min_samples
    )
    total = yes_n + no_n + unk_n
    if total <= 0 or (unk_n / total) > DEFAULT_MAX_UNKNOWN_FRACTION:
        return False
    if (
        is_sport_subtype_question(question_ref)
        and not subtype_already_asked
        and yes_n > 0
    ):
        return True
    del no_n
    return False


def total_sample_size_for_question(
    state: GameEngineState,
    question_id: UUID,
) -> int:
    if state.question_sample_totals:
        cached = state.question_sample_totals.get(question_id)
        if cached is not None:
            return int(cached)
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
            asked_question_order=list(state.asked_question_order),
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
    if question_ref is None:
        return "4"
    category = question_ref.category or ""
    text = (question_ref.text or "").casefold()

    # Sport subtypes / specifics and other hard niches are always Stage 4.
    if is_sport_subtype_question(question_ref) or is_sport_specific_question(question_ref):
        return "4"
    if is_hard_gated_niche(question_ref):
        return "4"
    if _text_matches_any(text, STAGE_C_KEYWORDS) or _text_matches_any(
        text, PROFESSION_SPECIFIC_KEYWORDS
    ):
        # Professions like chef; actor/singer stay Stage 4 unless major-category phrasing.
        if not is_major_category_question(question_ref):
            return "4"
    if _text_matches_any(text, STAGE_1_IDENTITY_KEYWORDS):
        return "1"
    if category in STAGE_2_ORIGIN_CATEGORIES or _text_matches_any(
        text, STAGE_2_ORIGIN_KEYWORDS
    ):
        return "2"
    if is_major_category_question(question_ref):
        return "3"

    if category in STAGE_C_QUESTION_CATEGORIES:
        return "4"
    if category in STAGE_B_QUESTION_CATEGORIES:
        return "3"
    if category in STAGE_A_QUESTION_CATEGORIES:
        # Broad Age/Gender/Personality without keyword match still counts as early.
        return "1" if category in {"Age", "Gender", "Personality"} else "4"
    # Text-only fallback for decks missing category metadata.
    if not category and text:
        if any(
            token in text
            for token in ("alive", "real", "male", "female", "woman", "man", "human", "famous")
        ):
            return "1"
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
    questions_asked: int = 0,
    question_refs: dict[UUID, QuestionRef] | None = None,
) -> tuple[SelectionStage, str | None]:
    """
    Determine natural questioning stage from category posterior mass.

    Stage 4 (subcategory) requires strong domain dominance — never open sport
    subtypes just because a few identity questions were asked.
    """
    if not character_categories:
        return "1", None

    dominant, top, second = top_category_masses(state, character_categories)
    if dominant is None:
        return "1", None

    margin = top - second
    asked = max(0, int(questions_asked))

    # Soft progression: advance to origin/category after broad turns, but do NOT
    # unlock Stage-4 subtypes without a major-domain question (or strong mass).
    if asked >= 5 and top >= 0.28:
        if has_asked_major_for_dominant(
            dominant, state.used_question_ids, question_refs
        ) and top >= stage_a_exit_threshold:
            return "4", dominant
        if (
            top >= stage_c_enter_threshold
            and margin >= stage_a_exit_margin
            and (
                dominant != "Sports"
                or has_asked_major_sports_category(state.used_question_ids, question_refs)
            )
        ):
            return "4", dominant
        if margin >= 0.04 or asked >= 6:
            return "3", dominant
        return "2", dominant

    if asked >= 3 and top >= 0.28 and margin < stage_a_exit_margin:
        return "2", dominant

    if top < stage_a_exit_threshold or margin < stage_a_exit_margin:
        return "1", dominant

    if top < stage_origin_exit_threshold or margin < stage_origin_exit_margin:
        return "2", dominant

    if top >= stage_c_enter_threshold and margin >= stage_a_exit_margin:
        if dominant == "Sports" and not has_asked_major_sports_category(
            state.used_question_ids, question_refs
        ):
            return "3", dominant
        return "4", dominant

    # After the major-domain question is answered, unlock subcategory questions
    # so cricket/football (etc.) can separate peers before one character hits 62%.
    if (
        has_asked_major_for_dominant(
            dominant, state.used_question_ids, question_refs
        )
        and top >= stage_a_exit_threshold
        and asked >= 2
    ):
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
    for key in niche_topic_keys(ref):
        allowed = NICHE_TOPIC_REQUIRED_CATEGORIES.get(key)
        if allowed is not None and not (allowed & remaining_categories):
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
    """Natural Akinator-style allow-list for Stage 1 / 2 / 3 / 4."""
    stage = _normalize_stage(stage)
    q_stage = _normalize_stage(question_hierarchy_stage(question_ref))
    category = question_ref.category if question_ref else None
    text = (question_ref.text or "").casefold() if question_ref else ""
    hard_niche = is_hard_gated_niche(question_ref)

    # Hard niche / forbidden: Stage 4 only, and only when the topic is relevant.
    if hard_niche:
        if stage != "4":
            return False
        return niche_topic_is_relevant(question_ref, dominant_category)

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
    if category in STAGE_B_QUESTION_CATEGORIES:
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


@dataclass(frozen=True)
class PosteriorView:
    """Current Bayesian frontier used by ranking (not a second candidate list)."""

    top_id: UUID | None
    top_p: float
    runner_id: UUID | None
    runner_p: float
    margin: float
    entropy: float
    effective_n: float
    candidate_count: int


def posterior_view(
    state: GameEngineState,
    current_entropy: float | None = None,
) -> PosteriorView:
    """Summarize the active posterior for scoring. Does not query a database."""
    active = {cid: state.probabilities[cid] for cid in state.active_character_ids()}
    h = current_entropy if current_entropy is not None else entropy(active)
    top, second = top_two(active)
    top_id = top[0] if top else None
    top_p = float(top[1]) if top else 0.0
    runner_id = second[0] if second else None
    runner_p = float(second[1]) if second else 0.0
    n = len(active)
    return PosteriorView(
        top_id=top_id,
        top_p=top_p,
        runner_id=runner_id,
        runner_p=runner_p,
        margin=max(0.0, top_p - runner_p),
        entropy=h,
        effective_n=float(2**h) if h > 0 else float(max(n, 1)),
        candidate_count=n,
    )


def candidate_separation_score(
    state: GameEngineState,
    question_id: UUID,
    view: PosteriorView | None = None,
    *,
    weight: float = DEFAULT_SEPARATION_WEIGHT,
    close_margin: float = DEFAULT_SEPARATION_CLOSE_MARGIN,
    dominant_top: float = DEFAULT_SEPARATION_DOMINANT_TOP,
    min_gap: float = DEFAULT_SEPARATION_MIN_LIKELIHOOD_GAP,
    max_effective_n: float = DEFAULT_SEPARATION_MAX_EFFECTIVE_N,
    min_duel_mass: float = DEFAULT_SEPARATION_MIN_DUEL_MASS,
    min_runner_p: float = DEFAULT_SEPARATION_MIN_RUNNER_P,
) -> float:
    """Bonus for questions that split the current top candidate vs runner-up.

    Zero when the leader is already dominant or the field is still broad, so
    ranking does not hunt extra questions that the confidence layer should
    turn into a guess.
    """
    snap = view or posterior_view(state)
    if snap.top_id is None or snap.runner_id is None:
        return 0.0
    if snap.top_p >= dominant_top:
        return 0.0
    if snap.runner_p < min_runner_p:
        return 0.0
    if (snap.top_p + snap.runner_p) < min_duel_mass:
        return 0.0
    if snap.effective_n > max_effective_n:
        return 0.0
    closeness = max(0.0, 1.0 - (snap.margin / max(close_margin, 1e-9)))
    if closeness <= 0.0:
        return 0.0
    gap = abs(
        get_likelihood(state.likelihoods, snap.top_id, question_id)
        - get_likelihood(state.likelihoods, snap.runner_id, question_id)
    )
    if gap < min_gap:
        return 0.0
    scaled = (gap - min_gap) / max(1.0 - min_gap, 1e-9)
    return weight * closeness * scaled


def context_relevance_score(
    *,
    question_id: UUID,
    ref: QuestionRef | None,
    view: PosteriorView,
    stage: SelectionStage,
    preferred_cats: frozenset[str],
    question_refs: dict[UUID, QuestionRef] | None,
    category_ig_bonus: float,
    broad_question_bonus: float,
) -> float:
    """Mild bonus when Q matches the current posterior domain / phase."""
    score = 0.0
    q_stage = question_hierarchy_stage(ref)
    if preferred_cats and _category_aligned(question_id, question_refs, preferred_cats):
        score += min(category_ig_bonus, DEFAULT_CONTEXT_WEIGHT)
    if stage in {"1", "2"} and q_stage in {"1", "2"} and view.effective_n >= 4:
        score += min(broad_question_bonus, DEFAULT_CONTEXT_WEIGHT)
    elif stage in {"3", "4"} and q_stage == "3":
        score += min(category_ig_bonus, DEFAULT_CONTEXT_WEIGHT) * 0.5
    if is_major_category_question(ref) and view.effective_n >= 3:
        score += min(category_ig_bonus, DEFAULT_CONTEXT_WEIGHT) * 0.35
    return score


def specificity_alignment_score(
    state: GameEngineState,
    question_id: UUID,
    view: PosteriorView,
    ref: QuestionRef | None,
    stage: SelectionStage,
) -> float:
    """Net specificity: boost tight discriminators when few remain; penalize early niches."""
    align = 0.0
    if view.effective_n <= DEFAULT_SPECIFICITY_NARROW_EFFECTIVE_N:
        spread = remaining_likelihood_spread(state, question_id)
        align = DEFAULT_SPECIFICITY_ALIGN_WEIGHT * min(1.0, spread)
    return align - specificity_penalty(ref, stage)


def useless_question_penalty_score(
    *,
    information_gain_value: float,
    unknown_fraction: float,
    likelihood_spread: float,
) -> float:
    """Penalize questions that cannot move the current posterior."""
    del likelihood_spread  # skip-filter handles saturated spread; keep IG primary
    penalty = unknown_fraction * 0.12
    if information_gain_value <= 1e-9:
        penalty += DEFAULT_USELESS_IG_PENALTY
    return penalty


@dataclass(frozen=True)
class QuestionScore:
    """Rank used by select_next_question.

    QuestionScore =
        InformationGain
        + CandidateSeparation
        + ContextRelevance
        + Specificity
        + QuestionQuality
        - RedundancyPenalty
        - UselessQuestionPenalty

    Information gain is the primary signal. Named constants keep the extras
    smaller than a typical useful split.
    """

    information_gain: float
    candidate_separation: float = 0.0
    context_relevance: float = 0.0
    specificity: float = 0.0
    question_quality: float = 0.0
    redundancy_penalty: float = 0.0
    useless_question_penalty: float = 0.0

    @property
    def total(self) -> float:
        return (
            self.information_gain
            + self.candidate_separation
            + self.context_relevance
            + self.specificity
            + self.question_quality
            - self.redundancy_penalty
            - self.useless_question_penalty
        )

    @property
    def separation_bonus(self) -> float:
        return self.candidate_separation

    @property
    def quality_bonus(self) -> float:
        return self.question_quality

    @property
    def repetition_penalty(self) -> float:
        return self.redundancy_penalty

    @property
    def specificity_penalty(self) -> float:
        return max(0.0, -self.specificity) if self.specificity < 0 else 0.0

    @property
    def confidence_utility(self) -> float:
        return 0.0

    @property
    def useful_candidate_weight(self) -> float:
        return 0.0



def score_question(
    *,
    question_id: UUID,
    information_gain_value: float,
    state: GameEngineState,
    focus: GameEngineState,
    ref: QuestionRef | None,
    previous_ref: QuestionRef | None,
    stage: SelectionStage,
    preferred_cats: frozenset[str],
    facts,
    sports_major_asked: bool,
    dominant: str | None,
    min_samples: int,
    category_ig_bonus: float,
    broad_question_bonus: float,
    question_refs: dict[UUID, QuestionRef] | None,
    posterior: PosteriorView | None = None,
) -> QuestionScore:
    """Composite score from in-memory likelihoods (no database access)."""
    view = posterior or posterior_view(focus)
    rank_state = focus if focus.active_character_ids() else state
    yes_n, no_n, unk_n = candidate_split_counts(
        rank_state, question_id, min_samples=min_samples
    )
    split_total = yes_n + no_n + unk_n
    unknown_fraction = (unk_n / split_total) if split_total else 0.0
    spread = remaining_likelihood_spread(rank_state, question_id)

    context = context_relevance_score(
        question_id=question_id,
        ref=ref,
        view=view,
        stage=stage,
        preferred_cats=preferred_cats,
        question_refs=question_refs,
        category_ig_bonus=category_ig_bonus,
        broad_question_bonus=broad_question_bonus,
    )
    quality = early_question_priority_bonus(ref)
    if facts is not None:
        quality += india_relevant_score_bonus(ref, facts)
    separation = candidate_separation_score(rank_state, question_id, view)
    extra_specificity = 0.0
    if is_sport_subtype_question(ref):
        if (
            _normalize_stage(stage) == "4"
            and dominant == "Sports"
            and sports_major_asked
        ):
            quality += category_ig_bonus * 0.45
            active = focus.active_character_ids()
            if active:
                mean_l = sum(
                    get_likelihood(focus.likelihoods, cid, question_id) for cid in active
                ) / len(active)
                separation += (mean_l - 0.5) * 0.4
        else:
            extra_specificity -= DEFAULT_SPECIFICITY_PENALTY * 0.5
    if is_sport_specific_question(ref):
        extra_specificity -= DEFAULT_SPECIFICITY_PENALTY
    if is_major_category_question(ref) and ref is not None and ref.category == "Movies":
        if "superhero" in (ref.text or "").casefold():
            quality += category_ig_bonus * 0.25

    specificity = (
        specificity_alignment_score(rank_state, question_id, view, ref, stage)
        + extra_specificity
    )
    return QuestionScore(
        information_gain=information_gain_value,
        candidate_separation=separation,
        context_relevance=context,
        specificity=specificity,
        question_quality=quality,
        redundancy_penalty=near_duplicate_penalty(ref, previous_ref),
        useless_question_penalty=useless_question_penalty_score(
            information_gain_value=information_gain_value,
            unknown_fraction=unknown_fraction,
            likelihood_spread=spread,
        ),
    )


def _is_category_diverse(
    question_id: UUID,
    previous_category: str | None,
    question_refs: dict[UUID, QuestionRef] | None,
) -> bool:
    if not previous_category or not question_refs:
        return False
    ref = question_refs.get(question_id)
    category = (ref.category or "") if ref else ""
    return bool(category) and category != previous_category


def _pick_from_near_best(
    scored: list[tuple[float, int, UUID]],
    *,
    tie_threshold: float,
    diversity_margin: float,
    diversity_top_k: int,
    rng: random.Random | None,
    explore: bool,
    previous_category: str | None = None,
    question_refs: dict[UUID, QuestionRef] | None = None,
) -> UUID:
    """Pick among near-best scores; explore when several questions are close.

    Category diversity is only a tie-breaker inside `tie_threshold`
    (typically ig_tie_threshold). Higher information-gain always wins.
    """
    scored = sorted(scored, key=lambda row: (row[0], row[1]), reverse=True)
    best_score, best_samples, best_qid = scored[0]

    if not explore or len(scored) == 1:
        chosen = best_qid
        chosen_samples = best_samples
        chosen_diverse = _is_category_diverse(
            best_qid, previous_category, question_refs
        )
        for score, samples, qid in scored[1:]:
            if abs(score - best_score) > tie_threshold:
                break
            diverse = _is_category_diverse(qid, previous_category, question_refs)
            if samples > chosen_samples or (
                samples == chosen_samples and diverse and not chosen_diverse
            ):
                chosen = qid
                chosen_samples = samples
                chosen_diverse = diverse
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


def _log_question_selected(
    *,
    chosen: UUID | None,
    scores_by_qid: dict[UUID, QuestionScore],
    view: PosteriorView,
    state: GameEngineState,
    question_refs: dict[UUID, QuestionRef] | None,
) -> None:
    if chosen is None or not logger.isEnabledFor(logging.DEBUG):
        return
    qs = scores_by_qid.get(chosen)
    ref = question_refs.get(chosen) if question_refs else None
    logger.debug(
        "question_selected question_id=%s ig=%.4f separation=%.4f specificity=%.4f "
        "quality=%.4f context=%.4f candidate_count=%s top_probability=%.4f "
        "runner_up_probability=%.4f text=%r",
        chosen,
        qs.information_gain if qs else 0.0,
        qs.candidate_separation if qs else 0.0,
        qs.specificity if qs else 0.0,
        qs.question_quality if qs else 0.0,
        qs.context_relevance if qs else 0.0,
        view.candidate_count,
        view.top_p,
        view.runner_p,
        (ref.text if ref else None),
    )


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
    early_priority_lock_questions: int = DEFAULT_EARLY_PRIORITY_LOCK_QUESTIONS,
    low_priority_age_min_ig: float = DEFAULT_LOW_PRIORITY_AGE_MIN_IG,
    low_priority_age_ig_margin: float = DEFAULT_LOW_PRIORITY_AGE_IG_MARGIN,
    candidate_mass_focus: float = DEFAULT_CANDIDATE_MASS_FOCUS,
    category_remain_mass: float = DEFAULT_CATEGORY_REMAIN_MASS,
    diversity_top_k: int = DEFAULT_DIVERSITY_TOP_K,
    diversity_margin: float = DEFAULT_DIVERSITY_MARGIN,
    rng: random.Random | None = None,
    explore: bool = False,
    character_names: dict[UUID, str] | None = None,
) -> UUID | None:
    """
    Select the next question using natural Stage 1 → 2 → 3 → 4 gating.

    Ranking is deterministic by default (explore=False): score by information
    gain + natural-flow bonuses − specificity / near-duplicate penalties.
    Niche questions stay hard-gated until Stage 4 and category relevance.
    """
    del consecutive_dont_know_cap  # reserved for future dont_know streak policy
    del character_names
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
        and is_question_eligible(
            qid,
            state.likelihoods,
            state.character_ids,
            min_samples,
            sample_totals=state.question_sample_totals,
        )
    ]

    if not unused:
        unused = [qid for qid in all_question_ids if qid not in state.used_question_ids]

    if not unused:
        return None

    focus = focus_candidate_state(state, mass_threshold=candidate_mass_focus)
    focus_entropy = entropy(
        {cid: focus.probabilities[cid] for cid in focus.active_character_ids()}
    )
    view = posterior_view(focus, focus_entropy)

    def _score_one(
        qid: UUID,
        *,
        ref: QuestionRef | None,
        previous_ref: QuestionRef | None,
        stage: SelectionStage,
        preferred_cats: frozenset[str],
        facts,
        sports_major_asked: bool,
        dominant: str | None,
    ) -> QuestionScore:
        return score_question(
            question_id=qid,
            information_gain_value=information_gain(
                focus, qid, current_entropy=focus_entropy
            ),
            state=state,
            focus=focus,
            ref=ref,
            previous_ref=previous_ref,
            stage=stage,
            preferred_cats=preferred_cats,
            facts=facts,
            sports_major_asked=sports_major_asked,
            dominant=dominant,
            min_samples=min_samples,
            category_ig_bonus=category_ig_bonus,
            broad_question_bonus=broad_question_bonus,
            question_refs=question_refs,
            posterior=view,
        )

    # Legacy callers (no hierarchy metadata) → IG + current-posterior ranking.
    if question_refs is None:
        scored_legacy: list[tuple[float, int, UUID]] = []
        scores_by_qid: dict[UUID, QuestionScore] = {}
        for qid in unused:
            qs = _score_one(
                qid,
                ref=None,
                previous_ref=None,
                stage="1",
                preferred_cats=frozenset(),
                facts=None,
                sports_major_asked=False,
                dominant=None,
            )
            scores_by_qid[qid] = qs
            scored_legacy.append(
                (qs.total, total_sample_size_for_question(state, qid), qid)
            )
        chosen_legacy = _pick_from_near_best(
            scored_legacy,
            tie_threshold=tie_threshold,
            diversity_margin=diversity_margin,
            diversity_top_k=diversity_top_k,
            rng=rng,
            explore=explore,
        )
        _log_question_selected(
            chosen=chosen_legacy,
            scores_by_qid=scores_by_qid,
            view=view,
            state=state,
            question_refs=None,
        )
        return chosen_legacy

    remaining_cats = remaining_character_categories(
        state,
        character_categories,
        min_mass=category_remain_mass,
    )
    facts = infer_established_facts(
        state,
        question_refs,
        remaining_categories=remaining_cats,
    )

    def _logically_ok(qid: UUID) -> bool:
        return is_logically_valid_question(
            question_refs.get(qid),
            facts,
            remaining_cats,
        )

    # Hierarchy engaged but category map missing → Stage 1 identity-only (fail safe).
    if not character_categories:
        broad_only = [
            qid
            for qid in unused
            if question_hierarchy_stage(question_refs.get(qid)) == "1"
            and not is_hard_gated_niche(question_refs.get(qid))
            and not is_low_priority_age_question(question_refs.get(qid))
            and _logically_ok(qid)
        ]
        if not broad_only:
            broad_only = [
                qid
                for qid in unused
                if question_hierarchy_stage(question_refs.get(qid)) == "1"
                and not is_hard_gated_niche(question_refs.get(qid))
                and _logically_ok(qid)
            ]
        if not broad_only:
            return None
        scored_safe: list[tuple[float, int, UUID]] = []
        for qid in broad_only:
            ref = question_refs.get(qid)
            scored_safe.append(
                (
                    information_gain(focus, qid, current_entropy=focus_entropy)
                    + broad_question_bonus
                    + early_question_priority_bonus(ref)
                    - specificity_penalty(ref, "1"),
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
            explore=False,
        )

    stage, dominant = resolve_selection_stage(
        focus,
        character_categories,
        stage_a_exit_threshold=a_exit,
        stage_a_exit_margin=stage_a_exit_margin,
        stage_origin_exit_threshold=stage_origin_exit_threshold,
        stage_origin_exit_margin=stage_origin_exit_margin,
        stage_c_enter_threshold=stage_c_enter_threshold,
        questions_asked=state.questions_asked,
        question_refs=question_refs,
    )

    # First turns stay on identity when broad questions remain — even if the
    # cast is sports-heavy and category mass would otherwise unlock Stage 3.
    if state.questions_asked < 3:
        identity_available = any(
            question_hierarchy_stage(question_refs.get(qid)) == "1"
            and not is_hard_gated_niche(question_refs.get(qid))
            and _logically_ok(qid)
            for qid in unused
        )
        if identity_available:
            stage = "1"

    # Akinator-like opening: real → gender → alive → country tree → domain.
    # Affirmed place locks geography; NO/don't-know may ask another country (≤3).
    opening_pool: list[UUID] | None = None
    asked_reality = _has_asked_matching(
        state.used_question_ids, question_refs, is_reality_question
    )
    asked_gender = _has_asked_matching(
        state.used_question_ids, question_refs, is_gender_question
    )
    asked_alive = _has_asked_matching(
        state.used_question_ids, question_refs, is_alive_status_question
    )
    asked_nationality = _has_asked_matching(
        state.used_question_ids, question_refs, is_nationality_place_question
    )
    place_locked = _place_affirmed(state, question_refs)
    wants_nationality = _wants_another_nationality(state, question_refs)
    asked_major = _has_asked_matching(
        state.used_question_ids, question_refs, is_major_category_question
    )

    def _unused_if(pred) -> list[UUID]:
        return [
            qid
            for qid in unused
            if pred(question_refs.get(qid))
            and not is_hard_gated_niche(question_refs.get(qid))
            and _logically_ok(qid)
        ]

    def _prefer_needles(pool: list[UUID], needles: tuple[str, ...]) -> list[UUID]:
        hits: list[UUID] = []
        for qid in pool:
            ref = question_refs.get(qid)
            text = (ref.text or "").casefold() if ref else ""
            if any(needle in text for needle in needles):
                hits.append(qid)
        return hits or pool

    unused_reality = _unused_if(is_reality_question)
    unused_gender = _unused_if(is_gender_question)
    unused_alive = _unused_if(is_alive_status_question)
    unused_nationality = _unused_if(is_nationality_place_question)
    unused_major = _unused_if(is_major_category_question)
    # Do not stall the game expecting another country question that does not exist.
    wants_nationality = wants_nationality and bool(unused_nationality)
    # Catch up identity only while still in the opening. Once a domain question
    # has been asked, do not jump back to "real person?" / leftover gender.
    if unused_reality and not asked_reality and not asked_major:
        stage = "1"
        opening_pool = _prefer_needles(unused_reality, ("real person",))
    elif unused_gender and not asked_gender and not asked_major:
        stage = "1"
        opening_pool = _prefer_needles(
            unused_gender, ("a man", "are they male", "male?")
        )
    elif unused_alive and not asked_alive and not asked_major:
        stage = "1"
        opening_pool = unused_alive
    elif unused_nationality and wants_nationality:
        stage = "2"
        opening_pool = unused_nationality
    elif unused_major and not wants_nationality and not asked_major:
        # After geography resolves (affirmed or exhausted), jump to domain.
        # India=yes → prefer athlete/sports (Kohli path); else any major.
        stage = "3"
        opening_pool = unused_major
        if facts.values.get("origin") == "india" or _india_affirmed(state, question_refs):
            sports_majors = []
            for qid in unused_major:
                ref = question_refs.get(qid)
                if ref is None:
                    continue
                text = (ref.text or "").casefold()
                if (
                    (ref.category or "") == "Sports"
                    or "athlete" in text
                    or "sports player" in text
                ):
                    sports_majors.append(qid)
            if sports_majors:
                opening_pool = sports_majors
    elif unused_major and asked_nationality and not wants_nationality and _normalize_stage(stage) in {"1", "2"}:
        stage = "3"

    previous_ref = last_asked_ref(
        state.used_question_ids,
        question_refs,
        asked_order=state.asked_question_order,
    )
    prev_was_sport_subtype = is_sport_subtype_question(previous_ref)
    sports_major_asked = has_asked_major_sports_category(
        state.used_question_ids, question_refs
    )

    def _collect_relevant(active_stage: SelectionStage) -> list[UUID]:
        picked: list[UUID] = []
        for qid in unused:
            ref = question_refs.get(qid)
            if ref is None:
                continue
            if not _logically_ok(qid):
                continue
            if is_akinator_filler_question(ref):
                if state.questions_asked < 12:
                    continue
                if remaining_likelihood_spread(state, qid) < 0.28:
                    continue
            if is_regional_state_question(ref) and dominant not in {
                "Politicians",
                "Movies",
                "Historical Figures",
            }:
                continue
            if not is_question_relevant_to_candidates(qid, question_refs, remaining_cats):
                if question_hierarchy_stage(ref) not in {"1", "2"}:
                    continue
            if not is_question_allowed_for_stage(
                ref, stage=active_stage, dominant_category=dominant
            ):
                continue
            # Geography lock: after a place YES, never ask another country.
            # After NO/don't-know, allow more until the nationality budget is spent.
            if is_nationality_place_question(ref) and not wants_nationality:
                continue
            # Prefer not re-asking the same place after any nationality answer.
            if is_nationality_place_question(ref) and place_locked:
                continue
            q_stage = question_hierarchy_stage(ref)
            if q_stage == "3" and ref.category in DOMAIN_QUESTION_CATEGORY_REQUIREMENTS:
                if not is_domain_category_unlocked(
                    ref.category,
                    focus,
                    character_categories,
                    unlock_threshold=category_unlock_threshold,
                ):
                    continue
            # Hard niche / rare roles wait until Stage 4. Sport subtypes must
            # NOT wait for a question-count delay once the sports domain is known:
            # remaining peers (e.g. Indian cricketers) need cricket/roles next.
            if is_hard_gated_niche(ref):
                if _normalize_stage(active_stage) != "4":
                    continue
                sport_family = is_sport_subtype_question(ref) or is_sport_specific_question(
                    ref
                )
                if not sport_family:
                    if state.questions_asked < 8:
                        continue
                    if dominant is None:
                        continue
            if is_sport_subtype_question(ref):
                if _normalize_stage(active_stage) != "4":
                    continue
                if dominant != "Sports":
                    continue
                if not sports_major_asked:
                    continue
                # Never chain skating → boxing → fencing.
                if prev_was_sport_subtype:
                    continue
            if is_sport_specific_question(ref):
                if _normalize_stage(active_stage) != "4":
                    continue
                if dominant != "Sports":
                    continue
                # Prefer subtype first, but do not deadlock when remaining
                # subtypes no longer split the pool (all remaining are cricket).
                subtype_asked = any(
                    is_sport_subtype_question(question_refs.get(u))
                    for u in state.used_question_ids
                )
                if not subtype_asked:
                    pending_subtypes = [
                        sid
                        for sid in unused
                        if is_sport_subtype_question(question_refs.get(sid))
                    ]
                    if any(
                        is_askable_on_pool(
                            state,
                            sid,
                            ig=0.0,
                            question_ref=question_refs.get(sid),
                            subtype_already_asked=False,
                            min_ig=0.0,
                            min_samples=min_samples,
                        )
                        for sid in pending_subtypes
                    ):
                        continue
            if not respects_one_level_step(
                ref,
                previous_ref=previous_ref,
                resolve_stage=active_stage,
                used_question_ids=state.used_question_ids,
                question_refs=question_refs,
            ):
                continue
            picked.append(qid)
        return picked

    if opening_pool is not None:
        relevant = list(opening_pool)
    else:
        relevant = _collect_relevant(stage)
    if not relevant:
        for promo in ("2", "3", "4"):
            if _normalize_stage(stage) == promo:
                continue
            # Do not skip past real / gender / alive / country milestones.
            if unused_reality and not asked_reality and not asked_major:
                break
            if unused_gender and not asked_gender and not asked_major:
                break
            if unused_alive and not asked_alive and not asked_major:
                break
            if unused_nationality and wants_nationality and promo in {"3", "4"}:
                continue
            if promo == "2" and state.questions_asked < 2:
                continue
            if promo == "3" and state.questions_asked < 3 and wants_nationality:
                continue
            if promo == "4" and state.questions_asked < 6:
                if wants_nationality or (unused_major and not asked_major):
                    continue
            relevant = _collect_relevant(promo)
            if relevant:
                stage = promo
                break
    if not relevant:
        relevant = [
            qid
            for qid in unused
            if question_hierarchy_stage(question_refs.get(qid)) == "1"
            and not is_hard_gated_niche(question_refs.get(qid))
            and _logically_ok(qid)
            and not (
                is_nationality_place_question(question_refs.get(qid)) and not wants_nationality
            )
        ]
    # Empty `relevant` means no gated candidate left — do not scrape trivia.

    preferred_cats = frozenset()
    if dominant is not None:
        mass = category_probability_mass(focus, character_categories, dominant)
        if mass > preference_threshold:
            preferred_cats = preferred_question_categories(dominant)

    ig_by_qid = {
        qid: information_gain(focus, qid, current_entropy=focus_entropy) for qid in relevant
    }
    non_low_igs = [
        ig_by_qid[qid]
        for qid in relevant
        if not is_low_priority_age_question(question_refs.get(qid))
        and not is_hard_gated_niche(question_refs.get(qid))
    ]
    best_non_low_ig = max(non_low_igs) if non_low_igs else None

    scored: list[tuple[float, int, UUID]] = []
    scores_by_qid: dict[UUID, QuestionScore] = {}
    for qid in relevant:
        ref = question_refs.get(qid)
        ig = ig_by_qid[qid]
        if is_low_priority_age_question(ref) and should_defer_low_priority_age(
            questions_asked=state.questions_asked,
            stage=stage,
            ig=ig,
            best_non_low_ig=best_non_low_ig,
            lock_questions=early_priority_lock_questions,
            min_ig=low_priority_age_min_ig,
            ig_margin=low_priority_age_ig_margin,
        ):
            continue
        if is_hard_gated_niche(ref) and _normalize_stage(stage) != "4":
            continue
        if opening_pool is None and remaining_likelihood_spread(state, qid) < DEFAULT_SATURATED_LIKELIHOOD_SPREAD:
            if not (
                is_sport_subtype_question(ref)
                and sports_major_asked
                and _normalize_stage(stage) == "4"
            ):
                continue
        qs = score_question(
            question_id=qid,
            information_gain_value=ig,
            state=state,
            focus=focus,
            ref=ref,
            previous_ref=previous_ref,
            stage=stage,
            preferred_cats=preferred_cats,
            facts=facts,
            sports_major_asked=sports_major_asked,
            dominant=dominant,
            min_samples=min_samples,
            category_ig_bonus=category_ig_bonus,
            broad_question_bonus=broad_question_bonus,
            question_refs=question_refs,
            posterior=view,
        )
        scores_by_qid[qid] = qs
        samples = total_sample_size_for_question(state, qid)
        scored.append((qs.total, samples, qid))

    if not scored:
        for qid in relevant:
            ref = question_refs.get(qid)
            if is_low_priority_age_question(ref) or is_hard_gated_niche(ref):
                continue
            scored.append(
                (
                    ig_by_qid[qid] + early_question_priority_bonus(ref),
                    total_sample_size_for_question(state, qid),
                    qid,
                )
            )
    if opening_pool is None and scored:
        useful: list[tuple[float, int, UUID]] = []
        min_ig = DEFAULT_MIN_USEFUL_IG
        if state.questions_asked < 4:
            min_ig = 0.008
        elif state.questions_asked < 10:
            min_ig = 0.02
        subtype_already_asked = any(
            is_sport_subtype_question(question_refs.get(qid))
            for qid in state.used_question_ids
        )
        for score, samples, qid in scored:
            if is_askable_on_pool(
                state,
                qid,
                ig=ig_by_qid.get(qid, 0.0),
                question_ref=question_refs.get(qid),
                subtype_already_asked=subtype_already_asked,
                min_ig=min_ig,
                min_samples=min_samples,
            ):
                useful.append((score, samples, qid))
        scored = useful
    if not scored:
        if logger.isEnabledFor(logging.DEBUG):
            pool = sorted(
                (
                    (
                        (character_names or {}).get(cid, str(cid)[:8]),
                        state.probabilities[cid],
                    )
                    for cid in state.active_character_ids()
                ),
                key=lambda row: -row[1],
            )[:8]
            logger.debug(
                "selection_exhausted asked=%s remaining=%s n=%s",
                state.questions_asked,
                pool,
                len(state.active_character_ids()),
            )
        return None

    chosen = _pick_from_near_best(
        scored,
        tie_threshold=tie_threshold,
        diversity_margin=diversity_margin,
        diversity_top_k=diversity_top_k,
        rng=rng,
        explore=explore if _normalize_stage(stage) == "4" else False,
        previous_category=(previous_ref.category if previous_ref else None),
        question_refs=question_refs,
    )
    _log_question_selected(
        chosen=chosen,
        scores_by_qid=scores_by_qid,
        view=view,
        state=state,
        question_refs=question_refs,
    )
    return chosen


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
    # Strong YES/NO with reliable L(C,Q) must drop clear contradictions
    # (e.g. India=YES removes Messi). Unknown L stays eligible.
    new_probs = apply_answer_constraints(
        new_probs, state.likelihoods, question_id, answer
    )
    state.probabilities = new_probs

    remaining, pre_top = eliminate_candidates(state)
    state.probabilities = remaining
    state.pre_elimination_top = pre_top

    state.used_question_ids.add(question_id)
    if question_id not in state.asked_question_order:
        state.asked_question_order.append(question_id)
    state.answer_log[question_id] = answer.value
    state.questions_asked += 1

    if answer == Answer.DONT_KNOW:
        state.consecutive_dont_know += 1
    else:
        state.consecutive_dont_know = 0

    return state, entropy_before


def create_initial_state(
    character_ids: list[UUID],
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry] | None = None,
    *,
    popularity: dict[UUID, int] | None = None,
    question_sample_totals: dict[UUID, int] | None = None,
) -> GameEngineState:
    return GameEngineState(
        character_ids=list(character_ids),
        probabilities=initialize_priors(character_ids, popularity),
        likelihoods=likelihoods or {},
        question_sample_totals=question_sample_totals,
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
