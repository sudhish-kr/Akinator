"""Essential tests for explainable guess attribution (leave-one-out)."""

import uuid

from app.engine.explain import (
    AnswerObservation,
    build_guess_explanation,
    influential_questions,
    remaining_candidates,
    top_candidates,
)
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import create_initial_state, process_answer


def _ids(n: int) -> list[uuid.UUID]:
    return [uuid.uuid4() for _ in range(n)]


def test_top_candidates_sorted_and_capped():
    c1, c2, c3, c4, c5, c6 = _ids(6)
    probs = {c1: 0.4, c2: 0.25, c3: 0.15, c4: 0.1, c5: 0.07, c6: 0.03}
    names = {c: f"C{i}" for i, c in enumerate(probs, start=1)}
    rows = top_candidates(probs, names, limit=5)
    assert len(rows) == 5
    assert rows[0]["id"] == str(c1)
    assert rows[0]["probability"] == 0.4
    assert [r["probability"] for r in rows] == sorted(
        (r["probability"] for r in rows), reverse=True
    )


def test_influential_question_ranks_discriminative_answer_highest():
    einstein, messi = uuid.uuid4(), uuid.uuid4()
    q_alive, q_scientist = uuid.uuid4(), uuid.uuid4()
    likelihoods = {
        (einstein, q_alive): LikelihoodEntry(0.05, 50),
        (messi, q_alive): LikelihoodEntry(0.95, 50),
        (einstein, q_scientist): LikelihoodEntry(0.95, 50),
        (messi, q_scientist): LikelihoodEntry(0.05, 50),
    }
    refs = {
        q_alive: QuestionRef(q_alive, "Is this person alive today?", None),
        q_scientist: QuestionRef(q_scientist, "Is this person a scientist?", None),
    }
    answers = [
        AnswerObservation(q_alive, "no"),
        AnswerObservation(q_scientist, "yes"),
    ]
    full = create_initial_state([einstein, messi], likelihoods)
    for obs in answers:
        full, _ = process_answer(full, obs.question_id, obs.answer)

    assert max(full.probabilities, key=full.probabilities.get) == einstein
    ranked = influential_questions(
        guessed_id=einstein,
        full_probability=full.probabilities[einstein],
        character_ids=[einstein, messi],
        likelihoods=likelihoods,
        answers=answers,
        question_refs=refs,
        limit=5,
    )
    assert len(ranked) == 2
    assert ranked[0]["influence"] >= ranked[1]["influence"]
    assert all(row["influence"] >= 0 for row in ranked)


def test_build_guess_explanation_shape_and_empty_answers():
    cid = uuid.uuid4()
    payload = build_guess_explanation(
        guessed_id=cid,
        guessed_name="Solo",
        confidence=1.0,
        probabilities={cid: 1.0},
        character_ids=[cid],
        character_names={cid: "Solo"},
        likelihoods={},
        answers=[],
        question_refs={},
    )
    assert payload["confidence_percent"] == 100.0
    assert payload["top_candidates"][0]["name"] == "Solo"
    assert payload["influential_questions"] == []
    assert "Solo" in payload["summary"]


def test_remaining_candidates_use_current_pool_not_generic_popularity():
    smriti, nadia, messi = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    probs = {smriti: 0.62, nadia: 0.21, messi: 0.17}
    names = {smriti: "Smriti Mandhana", nadia: "Nadia Comăneci", messi: "Lionel Messi"}
    cats = {smriti: "Sports", nadia: "Sports", messi: "Sports"}

    rows = remaining_candidates(probs, names, cats, category="Sports", exclude_ids={nadia})
    assert [r["name"] for r in rows] == ["Smriti Mandhana", "Lionel Messi"]

    searched = remaining_candidates(probs, names, cats, category="Sports", q="Mandhana")
    assert [r["name"] for r in searched] == ["Smriti Mandhana"]

    empty_cat = remaining_candidates(probs, names, cats, category="Movies")
    assert empty_cat == []

