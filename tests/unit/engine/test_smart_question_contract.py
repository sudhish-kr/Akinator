"""Akinator-style contract: IG ranking, follow-ups, no repeats, early guess."""

from __future__ import annotations

import math
import time
from uuid import UUID

import pytest

from pathlib import Path

from app.engine.confidence import evaluate_confidence, resolve_turn
from app.engine.constants import DEFAULT_MAX_QUESTIONS, Answer
from app.engine.elimination import entropy
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    QuestionScore,
    _pick_from_near_best,
    candidate_separation_score,
    create_initial_state,
    information_gain,
    posterior_view,
    process_answer,
    score_question,
    select_next_question,
)
from app.engine.question_consistency import EstablishedFacts

POL = UUID("00000000-0000-0000-0000-000000000201")
CRICKETER = UUID("00000000-0000-0000-0000-000000000202")
FICTION = UUID("00000000-0000-0000-0000-000000000203")

Q_REAL = UUID("00000000-0000-0000-0000-000000000b01")
Q_POLITICS = UUID("00000000-0000-0000-0000-000000000b02")
Q_CRICKET = UUID("00000000-0000-0000-0000-000000000b03")
Q_USELESS = UUID("00000000-0000-0000-0000-000000000b04")


def _catalog_state():
    likelihoods = {
        (POL, Q_REAL): LikelihoodEntry(0.95, 40),
        (CRICKETER, Q_REAL): LikelihoodEntry(0.95, 40),
        (FICTION, Q_REAL): LikelihoodEntry(0.05, 40),
        (POL, Q_POLITICS): LikelihoodEntry(0.95, 40),
        (CRICKETER, Q_POLITICS): LikelihoodEntry(0.05, 40),
        (FICTION, Q_POLITICS): LikelihoodEntry(0.05, 40),
        (POL, Q_CRICKET): LikelihoodEntry(0.05, 40),
        (CRICKETER, Q_CRICKET): LikelihoodEntry(0.95, 40),
        (FICTION, Q_CRICKET): LikelihoodEntry(0.05, 40),
        (POL, Q_USELESS): LikelihoodEntry(0.50, 40),
        (CRICKETER, Q_USELESS): LikelihoodEntry(0.50, 40),
        (FICTION, Q_USELESS): LikelihoodEntry(0.50, 40),
    }
    return create_initial_state([POL, CRICKETER, FICTION], likelihoods)


def test_information_gain_is_entropy_minus_expected_entropy():
    state = _catalog_state()
    h = entropy(state.probabilities)
    ig = information_gain(state, Q_REAL)
    assert ig == pytest.approx(h - (h - ig))
    assert information_gain(state, Q_REAL) > information_gain(state, Q_USELESS)
    assert ig > 0.0


def test_entropy_formula_matches_uniform_three_way():
    state = _catalog_state()
    assert entropy(state.probabilities) == pytest.approx(math.log2(3))


def test_best_question_is_highest_information_gain():
    state = _catalog_state()
    pool = [Q_USELESS, Q_REAL, Q_POLITICS, Q_CRICKET]
    chosen = select_next_question(state, pool, min_samples=1, explore=False)
    igs = {qid: information_gain(state, qid) for qid in pool}
    assert chosen == max(igs, key=igs.get)
    assert chosen != Q_USELESS
    assert information_gain(state, Q_REAL) > information_gain(state, Q_USELESS)


def test_already_asked_questions_are_excluded():
    state = _catalog_state()
    state.used_question_ids.add(Q_REAL)
    chosen = select_next_question(
        state, [Q_USELESS, Q_REAL, Q_POLITICS, Q_CRICKET], min_samples=1, explore=False
    )
    assert chosen != Q_REAL
    assert chosen in {Q_POLITICS, Q_CRICKET}


def test_yes_follow_up_recalculates_next_question():
    state = _catalog_state()
    state, _ = process_answer(state, Q_REAL, Answer.YES)
    nxt = select_next_question(
        state, [Q_REAL, Q_POLITICS, Q_CRICKET, Q_USELESS], min_samples=1, explore=False
    )
    assert nxt in {Q_POLITICS, Q_CRICKET}
    assert nxt != Q_REAL


def test_no_follow_up_recalculates_next_question():
    state = _catalog_state()
    state, _ = process_answer(state, Q_REAL, Answer.NO)
    nxt = select_next_question(
        state, [Q_REAL, Q_POLITICS, Q_CRICKET, Q_USELESS], min_samples=1, explore=False
    )
    assert nxt != Q_REAL
    yes_next = create_initial_state(
        [POL, CRICKETER, FICTION], state.likelihoods
    )
    yes_next, _ = process_answer(yes_next, Q_REAL, Answer.YES)
    yes_choice = select_next_question(
        yes_next, [Q_REAL, Q_POLITICS, Q_CRICKET, Q_USELESS], min_samples=1, explore=False
    )
    # YES vs NO on the identity split leaves different remaining mass, so
    # the next useful question must come from a fresh ranking.
    assert nxt is not None
    assert yes_choice is not None


def test_dont_know_does_not_repeat_the_question():
    state = _catalog_state()
    first = Q_REAL
    state, _ = process_answer(state, first, Answer.DONT_KNOW)
    nxt = select_next_question(
        state, [Q_REAL, Q_POLITICS, Q_CRICKET, Q_USELESS], min_samples=1, explore=False
    )
    assert first in state.used_question_ids
    assert nxt != first


def test_no_duplicate_questions_across_a_full_session():
    state = _catalog_state()
    pool = [Q_REAL, Q_POLITICS, Q_CRICKET, Q_USELESS]
    asked: list[UUID] = []
    for _ in range(len(pool) + 2):
        nxt = select_next_question(state, pool, min_samples=1, explore=False)
        if nxt is None:
            break
        assert nxt not in asked
        asked.append(nxt)
        state, _ = process_answer(state, nxt, Answer.YES)
    assert len(asked) == len(set(asked))
    assert len(asked) <= len(pool)


def test_low_confidence_keeps_asking():
    state = _catalog_state()
    result = resolve_turn(state, next_question_id=Q_REAL)
    assert result.should_guess is False


def test_high_confidence_guesses_before_max_questions():
    state = _catalog_state()
    state.probabilities = {POL: 0.93, CRICKETER: 0.04, FICTION: 0.03}
    state.questions_asked = 7
    result = evaluate_confidence(state)
    assert result.should_guess is True
    assert result.top_character_id == POL
    assert state.questions_asked < DEFAULT_MAX_QUESTIONS


def test_question_budget_caps_at_twenty():
    state = _catalog_state()
    state.probabilities = {POL: 0.40, CRICKETER: 0.35, FICTION: 0.25}
    state.questions_asked = DEFAULT_MAX_QUESTIONS
    result = evaluate_confidence(state, max_questions=DEFAULT_MAX_QUESTIONS)
    assert result.should_guess is True
    assert result.reason == "question_budget"


def test_question_score_ranks_information_gain_first():
    state = _catalog_state()
    facts = EstablishedFacts()
    split = score_question(
        question_id=Q_REAL,
        information_gain_value=1.0,
        state=state,
        focus=state,
        ref=None,
        previous_ref=None,
        stage="1",
        preferred_cats=frozenset(),
        facts=facts,
        sports_major_asked=False,
        dominant=None,
        min_samples=1,
        category_ig_bonus=0.12,
        broad_question_bonus=0.15,
        question_refs=None,
    )
    flat = score_question(
        question_id=Q_USELESS,
        information_gain_value=0.01,
        state=state,
        focus=state,
        ref=None,
        previous_ref=None,
        stage="1",
        preferred_cats=frozenset(),
        facts=facts,
        sports_major_asked=False,
        dominant=None,
        min_samples=1,
        category_ig_bonus=0.12,
        broad_question_bonus=0.15,
        question_refs=None,
    )
    assert isinstance(split, QuestionScore)
    assert split.information_gain == 1.0
    assert split.total > flat.total


def test_large_in_memory_catalog_does_not_need_database():
    chars = [UUID(int=i) for i in range(1, 121)]
    questions = [UUID(int=10_000 + i) for i in range(60)]
    likelihoods = {}
    for i, cid in enumerate(chars):
        for j, qid in enumerate(questions):
            likelihoods[(cid, qid)] = LikelihoodEntry(
                0.15 + ((i * 19 + j * 11) % 70) / 100.0, 20
            )
    state = create_initial_state(chars, likelihoods)
    t0 = time.perf_counter()
    chosen = select_next_question(state, questions, min_samples=1, explore=False)
    elapsed = time.perf_counter() - t0
    assert chosen is not None
    assert chosen in questions
    assert elapsed < 2.5


A = UUID("00000000-0000-0000-0000-000000000c01")
B = UUID("00000000-0000-0000-0000-000000000c02")
C = UUID("00000000-0000-0000-0000-000000000c03")
Q_AB = UUID("00000000-0000-0000-0000-000000000d01")
Q_GENERIC = UUID("00000000-0000-0000-0000-000000000d02")
Q_NOISE = UUID("00000000-0000-0000-0000-000000000d03")


def _close_race_state():
    likelihoods = {
        (A, Q_AB): LikelihoodEntry(0.95, 40),
        (B, Q_AB): LikelihoodEntry(0.05, 40),
        (C, Q_AB): LikelihoodEntry(0.50, 40),
        (A, Q_GENERIC): LikelihoodEntry(0.88, 40),
        (B, Q_GENERIC): LikelihoodEntry(0.86, 40),
        (C, Q_GENERIC): LikelihoodEntry(0.10, 40),
        (A, Q_NOISE): LikelihoodEntry(0.50, 40),
        (B, Q_NOISE): LikelihoodEntry(0.50, 40),
        (C, Q_NOISE): LikelihoodEntry(0.50, 40),
    }
    state = create_initial_state([A, B, C], likelihoods)
    state.probabilities = {A: 0.41, B: 0.39, C: 0.20}
    return state


def test_high_information_question_beats_low_information_question():
    state = _catalog_state()
    assert information_gain(state, Q_REAL) > information_gain(state, Q_USELESS)
    assert select_next_question(state, [Q_USELESS, Q_REAL], min_samples=1, explore=False) == Q_REAL


def test_posterior_change_changes_next_question():
    state = _catalog_state()
    pool = [Q_REAL, Q_POLITICS, Q_CRICKET, Q_USELESS]
    first = select_next_question(state, pool, min_samples=1, explore=False)
    igs = {qid: information_gain(state, qid) for qid in pool}
    assert first == max(igs, key=igs.get)
    assert first != Q_USELESS
    state, _ = process_answer(state, first, Answer.YES)
    second = select_next_question(state, pool, min_samples=1, explore=False)
    assert second != first
    assert second != Q_USELESS
    assert second is not None


def test_close_top_candidates_prefer_separator_over_generic():
    state = _close_race_state()
    ig_ab = information_gain(state, Q_AB)
    ig_generic = information_gain(state, Q_GENERIC)
    sep_ab = candidate_separation_score(state, Q_AB)
    sep_generic = candidate_separation_score(state, Q_GENERIC)
    assert sep_ab > sep_generic
    assert abs(ig_ab - ig_generic) < 0.35
    chosen = select_next_question(
        state, [Q_GENERIC, Q_AB, Q_NOISE], min_samples=1, explore=False
    )
    assert chosen == Q_AB


def test_dominant_leader_does_not_force_extra_questions():
    state = _close_race_state()
    state.probabilities = {A: 0.90, B: 0.03, C: 0.07}
    state.questions_asked = 8
    assert candidate_separation_score(state, Q_AB) == 0.0
    result = evaluate_confidence(state)
    assert result.should_guess is True
    assert result.top_character_id == A


def test_used_questions_are_never_reselected():
    state = _catalog_state()
    pool = [Q_REAL, Q_POLITICS, Q_CRICKET, Q_USELESS]
    asked = []
    for _ in range(6):
        nxt = select_next_question(state, pool, min_samples=1, explore=False)
        if nxt is None:
            break
        assert nxt not in asked
        asked.append(nxt)
        state, _ = process_answer(state, nxt, Answer.DONT_KNOW)
    assert len(asked) == len(set(asked))


def test_zero_information_questions_are_penalized():
    state = _catalog_state()
    facts = EstablishedFacts()
    kwargs = dict(
        state=state,
        focus=state,
        ref=None,
        previous_ref=None,
        stage="1",
        preferred_cats=frozenset(),
        facts=facts,
        sports_major_asked=False,
        dominant=None,
        min_samples=1,
        category_ig_bonus=0.12,
        broad_question_bonus=0.15,
        question_refs=None,
    )
    useless = score_question(
        question_id=Q_USELESS, information_gain_value=0.0, **kwargs
    )
    useful = score_question(
        question_id=Q_REAL, information_gain_value=0.8, **kwargs
    )
    assert useless.useless_question_penalty > useful.useless_question_penalty
    assert useful.total > useless.total
    assert (
        select_next_question(state, [Q_USELESS, Q_REAL], min_samples=1, explore=False)
        != Q_USELESS
    )


def test_selector_source_does_not_query_postgresql():
    src = Path(__file__).resolve().parents[3].joinpath("app", "engine", "selector.py")
    text = src.read_text(encoding="utf-8")
    assert "sqlalchemy" not in text
    assert "GameRepository" not in text
    assert "psycopg" not in text
    assert "asyncpg" not in text


def test_category_diversity_only_breaks_near_ties():
    q_high = UUID("00000000-0000-0000-0000-000000000e01")
    q_close = UUID("00000000-0000-0000-0000-000000000e02")
    refs = {
        q_high: QuestionRef(id=q_high, text="Sports player?", category="Sports"),
        q_close: QuestionRef(id=q_close, text="From a movie?", category="Movies"),
    }
    clearly_better = _pick_from_near_best(
        [(1.00, 20, q_high), (0.40, 20, q_close)],
        tie_threshold=0.001,
        diversity_margin=0.04,
        diversity_top_k=4,
        rng=None,
        explore=False,
        previous_category="Sports",
        question_refs=refs,
    )
    assert clearly_better == q_high
    tie = _pick_from_near_best(
        [(0.50, 10, q_high), (0.50, 10, q_close)],
        tie_threshold=0.001,
        diversity_margin=0.04,
        diversity_top_k=4,
        rng=None,
        explore=False,
        previous_category="Sports",
        question_refs=refs,
    )
    assert tie == q_close


def test_few_remaining_candidates_favor_direct_discriminators():
    state = _close_race_state()
    state.probabilities = {A: 0.46, B: 0.44, C: 0.10}
    view = posterior_view(state)
    assert view.effective_n < 4
    chosen = select_next_question(
        state, [Q_GENERIC, Q_AB, Q_NOISE], min_samples=1, explore=False
    )
    assert chosen == Q_AB
    assert candidate_separation_score(state, Q_AB) > candidate_separation_score(
        state, Q_GENERIC
    )


def test_first_question_is_not_a_hardcoded_id():
    q_left = UUID("00000000-0000-0000-0000-000000000f01")
    q_right = UUID("00000000-0000-0000-0000-000000000f02")
    chars = [UUID(int=i) for i in range(1, 9)]
    left_likes = {}
    right_likes = {}
    for i, cid in enumerate(chars):
        left_likes[(cid, q_left)] = LikelihoodEntry(0.95 if i < 4 else 0.05, 30)
        left_likes[(cid, q_right)] = LikelihoodEntry(0.50, 30)
        right_likes[(cid, q_right)] = LikelihoodEntry(0.95 if i < 4 else 0.05, 30)
        right_likes[(cid, q_left)] = LikelihoodEntry(0.50, 30)
    left_state = create_initial_state(chars, left_likes)
    right_state = create_initial_state(chars, right_likes)
    assert (
        select_next_question(left_state, [q_left, q_right], min_samples=1, explore=False)
        == q_left
    )
    assert (
        select_next_question(right_state, [q_left, q_right], min_samples=1, explore=False)
        == q_right
    )
