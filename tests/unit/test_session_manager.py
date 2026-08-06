"""Essential tests for the game session manager."""

from uuid import UUID, uuid4

import pytest

from app.engine.models import LikelihoodEntry, QuestionRef
from app.services.session_manager import ConfidenceThresholds, GameSessionManager

C1 = UUID("00000000-0000-0000-0000-000000000001")
C2 = UUID("00000000-0000-0000-0000-000000000002")
Q1 = UUID("00000000-0000-0000-0000-0000000000a1")
Q2 = UUID("00000000-0000-0000-0000-0000000000a2")


def _manager(**kwargs) -> GameSessionManager:
    return GameSessionManager(
        thresholds=ConfidenceThresholds(high=0.85, separation=0.6, margin=0.4, max_questions=25),
        min_samples=1,
        **kwargs,
    )


def _start(mgr: GameSessionManager):
    likelihoods = {
        (C1, Q1): LikelihoodEntry(0.95, 50),
        (C2, Q1): LikelihoodEntry(0.05, 50),
        (C1, Q2): LikelihoodEntry(0.9, 50),
        (C2, Q2): LikelihoodEntry(0.1, 50),
    }
    refs = {
        Q1: QuestionRef(id=Q1, text="Scientist?"),
        Q2: QuestionRef(id=Q2, text="Alive?"),
    }
    return mgr.start(
        session_id=uuid4(),
        character_ids=[C1, C2],
        likelihoods=likelihoods,
        question_ids=[Q1, Q2],
        question_refs=refs,
        character_names={C1: "Einstein", C2: "Messi"},
    )


def test_start_selects_first_question():
    live = _start(_manager())
    assert live.pending_question_id in {Q1, Q2}
    assert live.engine.questions_asked == 0
    assert live.answers == []


def test_submit_answer_tracks_and_updates_bayesian_state():
    mgr = _manager()
    live = _start(mgr)
    qid = live.pending_question_id
    turn = mgr.submit_answer(live, qid, "yes")

    assert len(live.answers) == 1
    assert live.answers[0].question_id == qid
    assert live.answers[0].answer == "yes"
    assert qid in mgr.asked_question_ids(live)
    assert turn.questions_asked == 1
    assert sum(live.engine.probabilities.values()) == pytest.approx(1.0)


def test_ends_when_no_questions_remain_and_returns_best_guess():
    mgr = _manager()
    live = _start(mgr)

    for _ in range(5):
        if live.awaiting_guess:
            break
        turn = mgr.submit_answer(live, live.pending_question_id, "dont_know")
    else:
        turn = None

    assert live.awaiting_guess is True
    assert turn is None or turn.status == "ready_to_guess"
    guess = mgr.best_guess(live)
    assert guess is not None
    char_id, confidence = guess
    assert char_id in {C1, C2}
    assert 0.0 <= confidence <= 1.0


def test_ends_when_confidence_threshold_reached():
    mgr = GameSessionManager(
        thresholds=ConfidenceThresholds(high=0.5, separation=0.99, margin=0.99, max_questions=25),
        min_samples=1,
    )
    live = _start(mgr)
    # Strong yes on scientist-like likelihoods should push C1 above 0.5 quickly
    turn = mgr.submit_answer(live, live.pending_question_id, "yes")
    if turn.status != "ready_to_guess":
        turn = mgr.submit_answer(live, live.pending_question_id, "yes")

    assert turn.status == "ready_to_guess"
    assert turn.best_guess_id is not None
    assert turn.top_confidence >= 0.5
