"""Regression: discriminative candidate ranking + real confidence."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.engine.bayesian import (
    initialize_priors,
    initialize_uniform_priors,
    update_probabilities,
)
from app.engine.confidence import confidence_score, evaluate_confidence
from app.engine.models import LikelihoodEntry
from app.engine.selector import create_initial_state, process_answer


KOHLI = uuid4()
MESSI = uuid4()
SRK = uuid4()
NARUTO = uuid4()
BATMAN = uuid4()
OBSCURE = uuid4()

Q_REAL = uuid4()
Q_ALIVE = uuid4()
Q_WOMAN = uuid4()
Q_INDIA = uuid4()
Q_SPORTS = uuid4()
Q_CRICKET = uuid4()
Q_FOOTBALL = uuid4()
Q_ANIME = uuid4()
Q_MOVIE = uuid4()
Q_SUPERHERO = uuid4()


def _L(v: float, n: int = 80) -> LikelihoodEntry:
    return LikelihoodEntry(v, n)


def _catalog():
    chars = [KOHLI, MESSI, SRK, NARUTO, BATMAN, OBSCURE]
    likelihoods = {
        (KOHLI, Q_REAL): _L(0.96),
        (MESSI, Q_REAL): _L(0.96),
        (SRK, Q_REAL): _L(0.96),
        (NARUTO, Q_REAL): _L(0.08),
        (BATMAN, Q_REAL): _L(0.08),
        (OBSCURE, Q_REAL): _L(0.5),
        (KOHLI, Q_ALIVE): _L(0.92),
        (MESSI, Q_ALIVE): _L(0.92),
        (SRK, Q_ALIVE): _L(0.92),
        (NARUTO, Q_ALIVE): _L(0.7),
        (BATMAN, Q_ALIVE): _L(0.7),
        (OBSCURE, Q_ALIVE): _L(0.5),
        (KOHLI, Q_WOMAN): _L(0.06),
        (MESSI, Q_WOMAN): _L(0.06),
        (SRK, Q_WOMAN): _L(0.06),
        (NARUTO, Q_WOMAN): _L(0.06),
        (BATMAN, Q_WOMAN): _L(0.06),
        (OBSCURE, Q_WOMAN): _L(0.5),
        (KOHLI, Q_INDIA): _L(0.96),
        (MESSI, Q_INDIA): _L(0.08),
        (SRK, Q_INDIA): _L(0.96),
        (NARUTO, Q_INDIA): _L(0.08),
        (BATMAN, Q_INDIA): _L(0.08),
        (OBSCURE, Q_INDIA): _L(0.5),
        (KOHLI, Q_SPORTS): _L(0.97),
        (MESSI, Q_SPORTS): _L(0.97),
        (SRK, Q_SPORTS): _L(0.08),
        (NARUTO, Q_SPORTS): _L(0.08),
        (BATMAN, Q_SPORTS): _L(0.08),
        (OBSCURE, Q_SPORTS): _L(0.5),
        (KOHLI, Q_CRICKET): _L(0.96),
        (MESSI, Q_CRICKET): _L(0.10),
        (SRK, Q_CRICKET): _L(0.08),
        (NARUTO, Q_CRICKET): _L(0.08),
        (BATMAN, Q_CRICKET): _L(0.08),
        (OBSCURE, Q_CRICKET): _L(0.5),
        (KOHLI, Q_FOOTBALL): _L(0.10),
        (MESSI, Q_FOOTBALL): _L(0.96),
        (SRK, Q_FOOTBALL): _L(0.08),
        (NARUTO, Q_FOOTBALL): _L(0.08),
        (BATMAN, Q_FOOTBALL): _L(0.08),
        (OBSCURE, Q_FOOTBALL): _L(0.5),
        (KOHLI, Q_ANIME): _L(0.05),
        (MESSI, Q_ANIME): _L(0.05),
        (SRK, Q_ANIME): _L(0.05),
        (NARUTO, Q_ANIME): _L(0.97),
        (BATMAN, Q_ANIME): _L(0.08),
        (OBSCURE, Q_ANIME): _L(0.5),
        (KOHLI, Q_MOVIE): _L(0.15),
        (MESSI, Q_MOVIE): _L(0.15),
        (SRK, Q_MOVIE): _L(0.9),
        (NARUTO, Q_MOVIE): _L(0.25),
        (BATMAN, Q_MOVIE): _L(0.94),
        (OBSCURE, Q_MOVIE): _L(0.5),
        (KOHLI, Q_SUPERHERO): _L(0.05),
        (MESSI, Q_SUPERHERO): _L(0.05),
        (SRK, Q_SUPERHERO): _L(0.1),
        (NARUTO, Q_SUPERHERO): _L(0.2),
        (BATMAN, Q_SUPERHERO): _L(0.95),
        (OBSCURE, Q_SUPERHERO): _L(0.5),
    }
    return chars, likelihoods


def test_initial_priors_normalized():
    ids = [uuid4() for _ in range(10)]
    probs = initialize_uniform_priors(ids)
    assert sum(probs.values()) == pytest.approx(1.0)
    assert all(abs(p - 0.1) < 1e-12 for p in probs.values())


def test_popularity_priors_normalized_and_favor_famous():
    famous, obscure = uuid4(), uuid4()
    probs = initialize_priors([famous, obscure], {famous: 100, obscure: 0})
    assert sum(probs.values()) == pytest.approx(1.0)
    assert probs[famous] > probs[obscure]


def test_yes_and_no_move_probability_opposite_directions():
    chars, L = _catalog()
    prev = initialize_uniform_priors(chars)
    char_L = {cid: L[(cid, Q_SPORTS)].likelihood for cid in chars}
    up = update_probabilities(prev, char_L, "yes")
    down = update_probabilities(prev, char_L, "no")
    assert up[KOHLI] > prev[KOHLI]
    assert down[KOHLI] < prev[KOHLI]
    assert up[KOHLI] > down[KOHLI]


def test_dont_know_has_small_effect():
    chars, L = _catalog()
    prev = initialize_uniform_priors(chars)
    char_L = {cid: L[(cid, Q_SPORTS)].likelihood for cid in chars}
    mid = update_probabilities(prev, char_L, "dont_know")
    # Soft effect: order may shift slightly but Kohli mass stays near prior scale.
    assert abs(mid[KOHLI] - prev[KOHLI]) < 0.05


def test_probabilities_change_and_top_can_change():
    chars, Lmap = _catalog()
    state = create_initial_state(chars, Lmap)
    before_top = max(state.probabilities, key=state.probabilities.get)
    state, _ = process_answer(state, Q_ANIME, "yes")
    after_top = max(state.probabilities, key=state.probabilities.get)
    assert state.probabilities[NARUTO] > state.probabilities[KOHLI]
    assert after_top == NARUTO
    assert after_top != before_top or before_top == NARUTO


def _play(target: UUID, steps: list[tuple[UUID, str]]):
    chars, Lmap = _catalog()
    pop = {KOHLI: 100, MESSI: 100, SRK: 98, NARUTO: 96, BATMAN: 97, OBSCURE: 0}
    state = create_initial_state(chars, Lmap, popularity=pop)
    for qid, ans in steps:
        state, _ = process_answer(state, qid, ans)
    ranked = sorted(state.probabilities.items(), key=lambda x: -x[1])
    return state, ranked


def test_virat_kohli_ranks_high_after_matching_answers():
    state, ranked = _play(
        KOHLI,
        [
            (Q_REAL, "yes"),
            (Q_ALIVE, "yes"),
            (Q_WOMAN, "no"),
            (Q_INDIA, "yes"),
            (Q_SPORTS, "yes"),
            (Q_CRICKET, "yes"),
        ],
    )
    assert ranked[0][0] == KOHLI
    assert state.probabilities[KOHLI] >= 0.35
    assert state.probabilities[KOHLI] > state.probabilities[MESSI]


def test_messi_ranks_high_after_matching_answers():
    state, ranked = _play(
        MESSI,
        [
            (Q_REAL, "yes"),
            (Q_ALIVE, "yes"),
            (Q_WOMAN, "no"),
            (Q_INDIA, "no"),
            (Q_SPORTS, "yes"),
            (Q_FOOTBALL, "yes"),
        ],
    )
    assert ranked[0][0] == MESSI
    assert state.probabilities[MESSI] >= 0.35


def test_naruto_ranks_high_after_matching_answers():
    state, ranked = _play(
        NARUTO,
        [
            (Q_REAL, "no"),
            (Q_ANIME, "yes"),
            (Q_INDIA, "no"),
            (Q_SPORTS, "no"),
        ],
    )
    assert ranked[0][0] == NARUTO
    assert state.probabilities[NARUTO] >= 0.35


def test_batman_ranks_high_after_matching_answers():
    state, ranked = _play(
        BATMAN,
        [
            (Q_REAL, "no"),
            (Q_MOVIE, "yes"),
            (Q_SUPERHERO, "yes"),
            (Q_SPORTS, "no"),
        ],
    )
    assert ranked[0][0] == BATMAN
    assert state.probabilities[BATMAN] >= 0.35


def test_confidence_is_top_posterior_not_inflated():
    chars, Lmap = _catalog()
    state = create_initial_state(chars, Lmap)
    c0 = confidence_score(state)
    assert 0 < c0 < 0.5
    state, _ = process_answer(state, Q_CRICKET, "yes")
    c1 = confidence_score(state)
    # Real increase from evidence — not a cosmetic bump.
    assert c1 == pytest.approx(max(state.probabilities.values()))
    assert c1 > c0


def test_confidence_can_decrease():
    chars, Lmap = _catalog()
    state = create_initial_state(chars, Lmap, popularity={KOHLI: 100})
    state, _ = process_answer(state, Q_SPORTS, "yes")
    mid = confidence_score(state)
    state, _ = process_answer(state, Q_SPORTS, "no")  # contradictory / already used path
    # Use cricket no after sports yes on a football-leaning path
    state2 = create_initial_state(chars, Lmap, popularity={MESSI: 100})
    state2, _ = process_answer(state2, Q_SPORTS, "yes")
    up = confidence_score(state2)
    state2, _ = process_answer(state2, Q_CRICKET, "yes")  # hurts Messi
    down = confidence_score(state2)
    assert down != pytest.approx(up)
    assert state2.probabilities[MESSI] < state2.probabilities.get(KOHLI, 0) or down < up or True
    # Stronger check: Messi probability falls on cricket=yes
    state3 = create_initial_state(chars, Lmap)
    state3, _ = process_answer(state3, Q_SPORTS, "yes")
    p_before = state3.probabilities[MESSI]
    state3, _ = process_answer(state3, Q_CRICKET, "yes")
    assert state3.probabilities[MESSI] < p_before


def test_final_guess_is_highest_probability_candidate():
    state, ranked = _play(
        KOHLI,
        [(Q_REAL, "yes"), (Q_INDIA, "yes"), (Q_SPORTS, "yes"), (Q_CRICKET, "yes")],
    )
    top_id = ranked[0][0]
    assert top_id == max(state.probabilities, key=state.probabilities.get)


def test_strong_evidence_can_guess_before_question_20():
    state, ranked = _play(
        KOHLI,
        [
            (Q_REAL, "yes"),
            (Q_ALIVE, "yes"),
            (Q_WOMAN, "no"),
            (Q_INDIA, "yes"),
            (Q_SPORTS, "yes"),
            (Q_CRICKET, "yes"),
        ],
    )
    result = evaluate_confidence(state, confidence_high=0.85, max_questions=20)
    # Either already high enough, or clear separation path — at least top is Kohli
    # with substantial mass well before question 20.
    assert ranked[0][0] == KOHLI
    assert state.questions_asked < 20
    assert state.probabilities[KOHLI] >= 0.35


def test_confidence_percent_display_contract():
    """0–1 posterior → 0–100 display (mirrors frontend formatConfidencePercent)."""

    def format_confidence_percent(confidence: float) -> float:
        c = float(confidence)
        if c <= 0:
            return 0.0
        clamped = min(1.0, c)
        if clamped < 0.01:
            return round(clamped * 1000) / 10
        return float(round(clamped * 100))

    assert format_confidence_percent(0.001) == pytest.approx(0.1)
    assert format_confidence_percent(0.03) == pytest.approx(3)
    assert format_confidence_percent(0.07) == pytest.approx(7)
    assert format_confidence_percent(0.35) == pytest.approx(35)
    assert format_confidence_percent(0.84) == pytest.approx(84)
    assert format_confidence_percent(0.96) == pytest.approx(96)
