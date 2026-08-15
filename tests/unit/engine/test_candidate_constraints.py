"""Strong categorical answer constraints on the candidate pool."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.engine.constraints import apply_answer_constraints
from app.engine.models import LikelihoodEntry
from app.engine.selector import create_initial_state, process_answer

KOHLI = uuid4()
MESSI = uuid4()
DHONI = uuid4()
SRK = uuid4()
NARUTO = uuid4()
BATMAN = uuid4()
UNKNOWN = uuid4()  # no reliable India mapping

Q_INDIA = uuid4()
Q_REAL = uuid4()
Q_SPORTS = uuid4()
Q_CRICKET = uuid4()
Q_FOOTBALL = uuid4()
Q_ANIME = uuid4()
Q_MOVIE = uuid4()
Q_SUPERHERO = uuid4()
Q_ALIVE = uuid4()
Q_WOMAN = uuid4()


def _L(v: float, n: int = 80) -> LikelihoodEntry:
    return LikelihoodEntry(v, n)


def _base_likelihoods():
    return {
        (KOHLI, Q_INDIA): _L(0.96),
        (MESSI, Q_INDIA): _L(0.08),
        (DHONI, Q_INDIA): _L(0.96),
        (SRK, Q_INDIA): _L(0.96),
        (NARUTO, Q_INDIA): _L(0.08),
        (BATMAN, Q_INDIA): _L(0.08),
        # UNKNOWN has no India entry → must stay eligible
        (KOHLI, Q_REAL): _L(0.96),
        (MESSI, Q_REAL): _L(0.96),
        (DHONI, Q_REAL): _L(0.96),
        (SRK, Q_REAL): _L(0.96),
        (NARUTO, Q_REAL): _L(0.08),
        (BATMAN, Q_REAL): _L(0.08),
        (UNKNOWN, Q_REAL): _L(0.5, 5),  # low samples → unknown for constraints
        (KOHLI, Q_SPORTS): _L(0.97),
        (MESSI, Q_SPORTS): _L(0.97),
        (DHONI, Q_SPORTS): _L(0.97),
        (SRK, Q_SPORTS): _L(0.08),
        (NARUTO, Q_SPORTS): _L(0.08),
        (BATMAN, Q_SPORTS): _L(0.08),
        (KOHLI, Q_CRICKET): _L(0.96),
        (MESSI, Q_CRICKET): _L(0.10),
        (DHONI, Q_CRICKET): _L(0.96),
        (SRK, Q_CRICKET): _L(0.08),
        (NARUTO, Q_CRICKET): _L(0.08),
        (BATMAN, Q_CRICKET): _L(0.08),
        (KOHLI, Q_FOOTBALL): _L(0.10),
        (MESSI, Q_FOOTBALL): _L(0.96),
        (DHONI, Q_FOOTBALL): _L(0.10),
        (NARUTO, Q_ANIME): _L(0.97),
        (BATMAN, Q_ANIME): _L(0.08),
        (KOHLI, Q_ANIME): _L(0.05),
        (MESSI, Q_ANIME): _L(0.05),
        (BATMAN, Q_MOVIE): _L(0.94),
        (BATMAN, Q_SUPERHERO): _L(0.95),
        (NARUTO, Q_MOVIE): _L(0.25),
        (NARUTO, Q_SUPERHERO): _L(0.2),
        (KOHLI, Q_MOVIE): _L(0.15),
        (KOHLI, Q_SUPERHERO): _L(0.05),
        (MESSI, Q_MOVIE): _L(0.15),
        (MESSI, Q_SUPERHERO): _L(0.05),
        (KOHLI, Q_ALIVE): _L(0.92),
        (MESSI, Q_ALIVE): _L(0.92),
        (NARUTO, Q_ALIVE): _L(0.7),
        (BATMAN, Q_ALIVE): _L(0.7),
        (KOHLI, Q_WOMAN): _L(0.06),
        (MESSI, Q_WOMAN): _L(0.06),
        (NARUTO, Q_WOMAN): _L(0.06),
        (BATMAN, Q_WOMAN): _L(0.06),
    }


CHARS = [KOHLI, MESSI, DHONI, SRK, NARUTO, BATMAN, UNKNOWN]


def test_india_yes_removes_clearly_non_indian():
    state = create_initial_state(CHARS, _base_likelihoods())
    state, _ = process_answer(state, Q_INDIA, "yes")
    assert KOHLI in state.probabilities
    assert DHONI in state.probabilities
    assert SRK in state.probabilities
    assert MESSI not in state.probabilities
    assert NARUTO not in state.probabilities
    assert BATMAN not in state.probabilities


def test_india_no_removes_clearly_indian():
    state = create_initial_state(CHARS, _base_likelihoods())
    state, _ = process_answer(state, Q_INDIA, "no")
    assert MESSI in state.probabilities
    assert NARUTO in state.probabilities
    assert KOHLI not in state.probabilities
    assert DHONI not in state.probabilities
    assert SRK not in state.probabilities


def test_dont_know_does_not_eliminate():
    state = create_initial_state(CHARS, _base_likelihoods())
    before = set(state.probabilities)
    state, _ = process_answer(state, Q_INDIA, "dont_know")
    assert set(state.probabilities) == before


def test_unknown_country_not_treated_as_non_indian():
    state = create_initial_state(CHARS, _base_likelihoods())
    state, _ = process_answer(state, Q_INDIA, "yes")
    assert UNKNOWN in state.probabilities


def test_real_yes_removes_fictional():
    state = create_initial_state(CHARS, _base_likelihoods())
    state, _ = process_answer(state, Q_REAL, "yes")
    assert KOHLI in state.probabilities
    assert MESSI in state.probabilities
    assert NARUTO not in state.probabilities
    assert BATMAN not in state.probabilities


def test_real_no_removes_real_people():
    state = create_initial_state(CHARS, _base_likelihoods())
    state, _ = process_answer(state, Q_REAL, "no")
    assert NARUTO in state.probabilities
    assert BATMAN in state.probabilities
    assert KOHLI not in state.probabilities
    assert MESSI not in state.probabilities


def test_athlete_yes_removes_non_athletes():
    state = create_initial_state(CHARS, _base_likelihoods())
    state, _ = process_answer(state, Q_SPORTS, "yes")
    assert KOHLI in state.probabilities
    assert MESSI in state.probabilities
    assert SRK not in state.probabilities
    assert NARUTO not in state.probabilities
    assert BATMAN not in state.probabilities


def test_cricket_yes_favors_cricket_after_athlete():
    state = create_initial_state(CHARS, _base_likelihoods())
    state, _ = process_answer(state, Q_SPORTS, "yes")
    state, _ = process_answer(state, Q_CRICKET, "yes")
    assert KOHLI in state.probabilities
    assert DHONI in state.probabilities
    assert MESSI not in state.probabilities
    assert state.probabilities[KOHLI] > 0.2


def test_probably_yes_soft_penalty_not_eliminate():
    probs = {MESSI: 0.5, KOHLI: 0.5}
    L = {(MESSI, Q_INDIA): _L(0.08), (KOHLI, Q_INDIA): _L(0.96)}
    out = apply_answer_constraints(probs, L, Q_INDIA, "probably_yes")
    assert MESSI in out
    assert KOHLI in out
    assert out[MESSI] < out[KOHLI]


def test_virat_top_after_matching_path():
    state = create_initial_state(
        CHARS,
        _base_likelihoods(),
        popularity={KOHLI: 100, DHONI: 98, MESSI: 100, SRK: 90},
    )
    for qid, ans in [
        (Q_REAL, "yes"),
        (Q_ALIVE, "yes"),
        (Q_WOMAN, "no"),
        (Q_INDIA, "yes"),
        (Q_SPORTS, "yes"),
        (Q_CRICKET, "yes"),
    ]:
        state, _ = process_answer(state, qid, ans)
    top = max(state.probabilities, key=state.probabilities.get)
    assert top == KOHLI
    assert MESSI not in state.probabilities


def test_messi_top_on_football_path():
    state = create_initial_state(
        CHARS,
        _base_likelihoods(),
        popularity={MESSI: 100, KOHLI: 100},
    )
    for qid, ans in [
        (Q_REAL, "yes"),
        (Q_INDIA, "no"),
        (Q_SPORTS, "yes"),
        (Q_FOOTBALL, "yes"),
    ]:
        state, _ = process_answer(state, qid, ans)
    assert max(state.probabilities, key=state.probabilities.get) == MESSI
    assert KOHLI not in state.probabilities


def test_naruto_top_on_anime_path():
    state = create_initial_state(CHARS, _base_likelihoods(), popularity={NARUTO: 96})
    for qid, ans in [(Q_REAL, "no"), (Q_ANIME, "yes"), (Q_SPORTS, "no")]:
        state, _ = process_answer(state, qid, ans)
    assert max(state.probabilities, key=state.probabilities.get) == NARUTO


def test_batman_top_on_superhero_path():
    state = create_initial_state(CHARS, _base_likelihoods(), popularity={BATMAN: 97})
    for qid, ans in [
        (Q_REAL, "no"),
        (Q_MOVIE, "yes"),
        (Q_SUPERHERO, "yes"),
        (Q_SPORTS, "no"),
    ]:
        state, _ = process_answer(state, qid, ans)
    assert max(state.probabilities, key=state.probabilities.get) == BATMAN
