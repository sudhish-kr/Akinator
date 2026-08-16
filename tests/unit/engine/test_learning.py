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


    def test_does_not_inflate_already_strong_yes(self):
        knowledge = {(CHAR, Q1): KnowledgeEntry(0.97, 80)}
        updates = learn_from_completed_game(
            CHAR,
            [AnswerObservation(Q1, "yes")],
            knowledge,
            learning_rate=0.07,
        )
        assert updates[0].likelihood == pytest.approx(0.97)
        assert updates[0].sample_size == 81

    def test_still_corrects_strong_yes_after_no(self):
        knowledge = {(CHAR, Q1): KnowledgeEntry(0.97, 80)}
        updates = learn_from_completed_game(
            CHAR,
            [AnswerObservation(Q1, "no")],
            knowledge,
            learning_rate=0.07,
        )
        assert updates[0].likelihood == pytest.approx(0.97 + 0.07 * (0.0 - 0.97))


class TestSamplePosterior:
    def test_yes_observation_raises_likelihood(self):
        from app.engine.learning import sample_posterior_likelihood

        # (0.5*10 + 1 + 1) / (10 + 1 + 2) = 7/13
        assert sample_posterior_likelihood(0.5, 10, 1.0, alpha=1.0) == pytest.approx(7 / 13)

    def test_no_observation_lowers_likelihood(self):
        from app.engine.learning import sample_posterior_likelihood

        # (0.5*10 + 0 + 1) / (10 + 1 + 2) = 6/13
        assert sample_posterior_likelihood(0.5, 10, 0.0, alpha=1.0) == pytest.approx(6 / 13)

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
        by_q = {u.question_id: u for u in updates if u.character_id == CHAR}
        assert by_q[Q1].sample_size == 3
        assert by_q[Q2].sample_size == 1

    def test_wrong_guess_updates_distinguishing_pair_from_session_evidence(self):
        from app.engine.learning import sample_posterior_likelihood

        guessed = UUID("00000000-0000-0000-0000-000000000011")
        actual = CHAR
        q_cricket = Q1
        q_politics = Q2
        knowledge = {
            (guessed, q_cricket): KnowledgeEntry(0.20, 40),
            (actual, q_cricket): KnowledgeEntry(0.95, 40),
            (guessed, q_politics): KnowledgeEntry(0.70, 40),
            (actual, q_politics): KnowledgeEntry(0.10, 40),
        }
        updates = learn_from_wrong_guess(
            actual,
            [AnswerObservation(q_cricket, "yes"), AnswerObservation(q_politics, "no")],
            knowledge,
            learning_rate=DEFAULT_LEARNING_RATE,
            guessed_character_id=guessed,
        )
        by_key = {(u.character_id, u.question_id): u for u in updates}
        assert by_key[(actual, q_cricket)].sample_size == 41
        guessed_cricket = by_key[(guessed, q_cricket)]
        # User said YES (about actual); guessed character is nudged toward NO.
        assert guessed_cricket.likelihood == pytest.approx(
            sample_posterior_likelihood(0.20, 40, 0.0)
        )
        assert guessed_cricket.sample_size == 41
        guessed_politics = by_key[(guessed, q_politics)]
        assert guessed_politics.likelihood == pytest.approx(
            sample_posterior_likelihood(0.70, 40, 1.0)
        )

    def test_wrong_guess_does_not_inflate_already_aligned_guess(self):
        guessed = UUID("00000000-0000-0000-0000-000000000013")
        actual = CHAR
        knowledge = {
            (guessed, Q1): KnowledgeEntry(0.08, 40),
            (actual, Q1): KnowledgeEntry(0.95, 40),
        }
        updates = learn_from_wrong_guess(
            actual,
            [AnswerObservation(Q1, "yes")],
            knowledge,
            guessed_character_id=guessed,
        )
        by_key = {(u.character_id, u.question_id): u for u in updates}
        assert by_key[(guessed, Q1)].likelihood == pytest.approx(0.08)
        assert by_key[(guessed, Q1)].sample_size == 41

    def test_wrong_guess_does_not_create_unsampled_guessed_mapping(self):
        guessed = UUID("00000000-0000-0000-0000-000000000012")
        actual = CHAR
        knowledge = {
            (actual, Q1): KnowledgeEntry(0.95, 20),
        }
        updates = learn_from_wrong_guess(
            actual,
            [AnswerObservation(Q1, "yes")],
            knowledge,
            guessed_character_id=guessed,
        )
        guessed_keys = [u for u in updates if u.character_id == guessed]
        assert guessed_keys == []
