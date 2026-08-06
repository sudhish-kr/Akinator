"""Essential tests for the learning engine (TDD Section 4)."""

from uuid import UUID

import pytest

from app.engine.bayesian import apply_learning_update
from app.engine.constants import ANSWER_WEIGHTS, DEFAULT_LEARNING_RATE
from app.engine.learning import (
    AnswerObservation,
    KnowledgeEntry,
    learn_from_completed_game,
    learn_from_wrong_guess,
    store_distinguishing_fact,
)

CHAR = UUID("00000000-0000-0000-0000-000000000001")
Q1 = UUID("00000000-0000-0000-0000-0000000000a1")
Q2 = UUID("00000000-0000-0000-0000-0000000000a2")


class TestNudgeFormula:
    def test_nudges_toward_yes(self):
        result = apply_learning_update(0.5, ANSWER_WEIGHTS["yes"], learning_rate=0.1)
        assert result == pytest.approx(0.55)

    def test_clamped_to_unit_interval(self):
        assert apply_learning_update(0.99, 1.0, learning_rate=1.0) == pytest.approx(1.0)
        assert apply_learning_update(0.01, 0.0, learning_rate=1.0) == pytest.approx(0.0)


class TestLearnFromCompletedGame:
    def test_updates_likelihoods_for_session_answers(self):
        knowledge = {(CHAR, Q1): KnowledgeEntry(0.5, 10)}
        updates = learn_from_completed_game(
            CHAR,
            [AnswerObservation(Q1, "yes"), AnswerObservation(Q2, "no")],
            knowledge,
            learning_rate=0.1,
        )
        by_q = {u.question_id: u for u in updates}
        assert by_q[Q1].likelihood == pytest.approx(0.55)
        assert by_q[Q1].sample_size == 11
        assert by_q[Q2].likelihood == pytest.approx(0.45)  # from default 0.5 toward no
        assert by_q[Q2].sample_size == 1

    def test_no_duplicate_updates_for_repeated_question(self):
        updates = learn_from_completed_game(
            CHAR,
            [
                AnswerObservation(Q1, "yes"),
                AnswerObservation(Q1, "no"),  # last wins
            ],
            {},
            learning_rate=0.1,
        )
        assert len(updates) == 1
        assert updates[0].question_id == Q1
        assert updates[0].likelihood == pytest.approx(0.45)


class TestWrongGuessLearning:
    def test_stores_correct_object_with_distinguishing_fact(self):
        fact = store_distinguishing_fact(CHAR, Q1, "yes", {}, learning_rate=0.1)
        assert fact.character_id == CHAR
        assert fact.question_id == Q1
        assert fact.likelihood == pytest.approx(0.55)
        assert fact.sample_size == 1

    def test_wrong_guess_upserts_without_duplicates(self):
        knowledge = {(CHAR, Q1): KnowledgeEntry(0.5, 2)}
        updates = learn_from_wrong_guess(
            CHAR,
            [AnswerObservation(Q1, "yes"), AnswerObservation(Q2, "no")],
            knowledge,
            distinguishing_question_id=Q1,
            distinguishing_answer="yes",
            learning_rate=DEFAULT_LEARNING_RATE,
        )
        keys = {(u.character_id, u.question_id) for u in updates}
        assert keys == {(CHAR, Q1), (CHAR, Q2)}
        assert len(updates) == 2
