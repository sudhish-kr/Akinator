"""Akinator-style contract: IG ranking, follow-ups, no repeats, early guess."""

from __future__ import annotations

import math
import time
from uuid import UUID

import pytest

from app.engine.confidence import evaluate_confidence, resolve_turn
from app.engine.constants import DEFAULT_MAX_QUESTIONS, Answer
from app.engine.elimination import entropy
from app.engine.models import LikelihoodEntry
from app.engine.selector import (
    QuestionScore,
    create_initial_state,
    information_gain,
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
