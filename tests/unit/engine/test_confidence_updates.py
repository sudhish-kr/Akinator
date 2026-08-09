"""Regression: confidence must move when answers hit mapped likelihoods."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.engine.models import LikelihoodEntry, QuestionRef
from app.services.session_manager import ConfidenceThresholds, GameSessionManager

KOHLI = UUID("10000000-0000-0000-0000-000000000001")
MESSI = UUID("10000000-0000-0000-0000-000000000002")
SRK = UUID("10000000-0000-0000-0000-000000000003")
NARUTO = UUID("10000000-0000-0000-0000-000000000004")
BATMAN = UUID("10000000-0000-0000-0000-000000000005")

Q_SPORTS = UUID("20000000-0000-0000-0000-000000000001")
Q_ANIME = UUID("20000000-0000-0000-0000-000000000002")
Q_MOVIES = UUID("20000000-0000-0000-0000-000000000003")
Q_ALIVE = UUID("20000000-0000-0000-0000-000000000004")

ICONS = {
    KOHLI: "Virat Kohli",
    MESSI: "Lionel Messi",
    SRK: "Shah Rukh Khan",
    NARUTO: "Naruto Uzumaki",
    BATMAN: "Batman",
}


def _likelihoods() -> dict[tuple[UUID, UUID], LikelihoodEntry]:
    # Meaningful category-style mappings (non-neutral) for active questions.
    matrix = {
        (KOHLI, Q_SPORTS): 0.97,
        (MESSI, Q_SPORTS): 0.99,
        (SRK, Q_SPORTS): 0.08,
        (NARUTO, Q_SPORTS): 0.05,
        (BATMAN, Q_SPORTS): 0.06,
        (KOHLI, Q_ANIME): 0.05,
        (MESSI, Q_ANIME): 0.04,
        (SRK, Q_ANIME): 0.06,
        (NARUTO, Q_ANIME): 0.99,
        (BATMAN, Q_ANIME): 0.08,
        (KOHLI, Q_MOVIES): 0.12,
        (MESSI, Q_MOVIES): 0.10,
        (SRK, Q_MOVIES): 0.96,
        (NARUTO, Q_MOVIES): 0.15,
        (BATMAN, Q_MOVIES): 0.95,
        (KOHLI, Q_ALIVE): 0.95,
        (MESSI, Q_ALIVE): 0.95,
        (SRK, Q_ALIVE): 0.95,
        (NARUTO, Q_ALIVE): 0.08,
        (BATMAN, Q_ALIVE): 0.05,
    }
    return {k: LikelihoodEntry(v, 50) for k, v in matrix.items()}


def _manager() -> GameSessionManager:
    return GameSessionManager(
        thresholds=ConfidenceThresholds(
            high=0.99, separation=0.99, margin=0.99, max_questions=25
        ),
        min_samples=1,
    )


def _start(mgr: GameSessionManager):
    refs = {
        Q_SPORTS: QuestionRef(id=Q_SPORTS, text="Is this a sports player?", category="Sports"),
        Q_ANIME: QuestionRef(id=Q_ANIME, text="Is this from anime?", category="Anime"),
        Q_MOVIES: QuestionRef(id=Q_MOVIES, text="Is this from a movie?", category="Movies"),
        Q_ALIVE: QuestionRef(id=Q_ALIVE, text="Is this person still alive?", category="Age"),
    }
    return mgr.start(
        session_id=uuid4(),
        character_ids=list(ICONS),
        likelihoods=_likelihoods(),
        question_ids=list(refs),
        question_refs=refs,
        character_names=dict(ICONS),
        character_categories={
            KOHLI: "Sports",
            MESSI: "Sports",
            SRK: "Movies",
            NARUTO: "Anime",
            BATMAN: "Movies",
        },
    )


@pytest.mark.parametrize(
    ("target", "question_id", "yes_raises"),
    [
        (KOHLI, Q_SPORTS, True),
        (MESSI, Q_SPORTS, True),
        (SRK, Q_MOVIES, True),
        (NARUTO, Q_ANIME, True),
        (BATMAN, Q_MOVIES, True),
        (NARUTO, Q_SPORTS, False),
        (BATMAN, Q_ALIVE, False),
    ],
)
def test_icon_confidence_moves_with_aligned_answers(target, question_id, yes_raises):
    mgr = _manager()
    live = _start(mgr)
    live.pending_question_id = question_id
    before = live.engine.probabilities[target]
    turn = mgr.submit_answer(live, question_id, "yes")
    after = live.engine.probabilities[target]
    assert after != pytest.approx(before, abs=1e-9)
    if yes_raises:
        assert after > before
    else:
        assert after < before
    assert turn.top_confidence != pytest.approx(1 / len(ICONS), abs=1e-6)


def test_confidence_can_increase_and_decrease_for_same_character():
    mgr = _manager()
    live_up = _start(mgr)
    live_up.pending_question_id = Q_SPORTS
    p0 = live_up.engine.probabilities[MESSI]
    up = mgr.submit_answer(live_up, Q_SPORTS, "yes")
    assert live_up.engine.probabilities[MESSI] > p0
    assert up.top_confidence > 1 / len(ICONS)

    live_down = _start(mgr)
    live_down.pending_question_id = Q_ANIME
    p1 = live_down.engine.probabilities[MESSI]
    down = mgr.submit_answer(live_down, Q_ANIME, "yes")
    assert live_down.engine.probabilities[MESSI] < p1
    assert down.top_confidence != pytest.approx(up.top_confidence, abs=1e-6)
