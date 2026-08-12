"""End-to-end natural gameplay + confidence reliability regressions."""

from __future__ import annotations

import random
from uuid import UUID, uuid4

import pytest

from app.engine.confidence import confidence_score, evaluate_confidence, normalize_probabilities
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    is_sport_subtype_question,
    process_answer,
    select_next_question,
)
from app.services.session_manager import ConfidenceThresholds, GameSessionManager
from app.training.oracle import oracle_answer

KOHLI = UUID("00000000-0000-0000-0000-000000000d01")
MESSI = UUID("00000000-0000-0000-0000-000000000d02")
SRK = UUID("00000000-0000-0000-0000-000000000d03")
NARUTO = UUID("00000000-0000-0000-0000-000000000d04")
BATMAN = UUID("00000000-0000-0000-0000-000000000d05")
OBSCURE = UUID("00000000-0000-0000-0000-000000000d06")

Q_REAL = UUID("00000000-0000-0000-0000-000000000e01")
Q_MALE = UUID("00000000-0000-0000-0000-000000000e02")
Q_ALIVE = UUID("00000000-0000-0000-0000-000000000e03")
Q_FAMOUS = UUID("00000000-0000-0000-0000-000000000e04")
Q_HUMAN = UUID("00000000-0000-0000-0000-000000000e05")
Q_SPORTS = UUID("00000000-0000-0000-0000-000000000e06")
Q_CRICKET = UUID("00000000-0000-0000-0000-000000000e07")
Q_FOOTBALL = UUID("00000000-0000-0000-0000-000000000e08")
Q_SKATING = UUID("00000000-0000-0000-0000-000000000e09")
Q_BOXING = UUID("00000000-0000-0000-0000-000000000e0a")
Q_FENCING = UUID("00000000-0000-0000-0000-000000000e0b")
Q_MARTIAL = UUID("00000000-0000-0000-0000-000000000e0c")
Q_BATSMAN = UUID("00000000-0000-0000-0000-000000000e0d")
Q_CHEF = UUID("00000000-0000-0000-0000-000000000e0e")
Q_ANIME = UUID("00000000-0000-0000-0000-000000000e0f")
Q_NINJA = UUID("00000000-0000-0000-0000-000000000e10")
Q_POWERS = UUID("00000000-0000-0000-0000-000000000e11")
Q_SUPERHERO = UUID("00000000-0000-0000-0000-000000000e12")
Q_CRIME = UUID("00000000-0000-0000-0000-000000000e13")
Q_MOVIES = UUID("00000000-0000-0000-0000-000000000e14")
Q_INDIA = UUID("00000000-0000-0000-0000-000000000e15")

CHARS = [KOHLI, MESSI, SRK, NARUTO, BATMAN, OBSCURE]
QUESTIONS = [
    Q_REAL,
    Q_MALE,
    Q_ALIVE,
    Q_FAMOUS,
    Q_HUMAN,
    Q_SPORTS,
    Q_CRICKET,
    Q_FOOTBALL,
    Q_SKATING,
    Q_BOXING,
    Q_FENCING,
    Q_MARTIAL,
    Q_BATSMAN,
    Q_CHEF,
    Q_ANIME,
    Q_NINJA,
    Q_POWERS,
    Q_SUPERHERO,
    Q_CRIME,
    Q_MOVIES,
    Q_INDIA,
]

REFS = {
    Q_REAL: QuestionRef(id=Q_REAL, text="Is this a real person?", category="Personality"),
    Q_MALE: QuestionRef(id=Q_MALE, text="Are they male?", category="Gender"),
    Q_ALIVE: QuestionRef(id=Q_ALIVE, text="Is this person still alive?", category="Age"),
    Q_FAMOUS: QuestionRef(
        id=Q_FAMOUS, text="Are they famous worldwide?", category="Personality"
    ),
    Q_HUMAN: QuestionRef(id=Q_HUMAN, text="Are they human?", category="Personality"),
    Q_SPORTS: QuestionRef(id=Q_SPORTS, text="Is this a sports player?", category="Sports"),
    Q_CRICKET: QuestionRef(
        id=Q_CRICKET, text="Are they famous for cricket?", category="Sports"
    ),
    Q_FOOTBALL: QuestionRef(
        id=Q_FOOTBALL, text="Are they famous for football?", category="Sports"
    ),
    Q_SKATING: QuestionRef(
        id=Q_SKATING, text="Are they famous for skating?", category="Sports"
    ),
    Q_BOXING: QuestionRef(
        id=Q_BOXING, text="Are they famous for boxing?", category="Sports"
    ),
    Q_FENCING: QuestionRef(
        id=Q_FENCING, text="Are they famous for fencing?", category="Sports"
    ),
    Q_MARTIAL: QuestionRef(
        id=Q_MARTIAL, text="Are they famous for martial arts?", category="Sports"
    ),
    Q_BATSMAN: QuestionRef(
        id=Q_BATSMAN, text="Is your character known for batting?", category="Sports"
    ),
    Q_CHEF: QuestionRef(id=Q_CHEF, text="Are they a chef?", category="Profession"),
    Q_ANIME: QuestionRef(id=Q_ANIME, text="Is this from anime?", category="Anime"),
    Q_NINJA: QuestionRef(id=Q_NINJA, text="Are they a ninja or samurai?", category="Anime"),
    Q_POWERS: QuestionRef(
        id=Q_POWERS, text="Do they have special powers?", category="Anime"
    ),
    Q_SUPERHERO: QuestionRef(
        id=Q_SUPERHERO, text="Is your character a superhero?", category="Movies"
    ),
    Q_CRIME: QuestionRef(
        id=Q_CRIME, text="Does your character fight crime?", category="Movies"
    ),
    Q_MOVIES: QuestionRef(id=Q_MOVIES, text="Is this from a movie?", category="Movies"),
    Q_INDIA: QuestionRef(id=Q_INDIA, text="Are they from India?", category="Nationality"),
}

CATEGORIES = {
    KOHLI: "Sports",
    MESSI: "Sports",
    SRK: "Movies",
    NARUTO: "Anime",
    BATMAN: "Movies",
    OBSCURE: "Sports",
}

NAMES = {
    KOHLI: "Virat Kohli",
    MESSI: "Lionel Messi",
    SRK: "Shah Rukh Khan",
    NARUTO: "Naruto",
    BATMAN: "Batman",
    OBSCURE: "Obscure Skater",
}

POPULARITY = {
    KOHLI: 100,
    MESSI: 100,
    SRK: 98,
    NARUTO: 96,
    BATMAN: 97,
    OBSCURE: 1,
}

SPORT_SUBTYPES = {Q_CRICKET, Q_FOOTBALL, Q_SKATING, Q_BOXING, Q_FENCING, Q_MARTIAL}
NARROW_EARLY = {Q_SKATING, Q_BOXING, Q_FENCING, Q_MARTIAL, Q_CHEF, Q_NINJA, Q_POWERS, Q_BATSMAN}
BROAD = {Q_REAL, Q_MALE, Q_ALIVE, Q_FAMOUS, Q_HUMAN}

PROFILE = {
    KOHLI: {
        Q_REAL: 0.95,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_HUMAN: 0.95,
        Q_SPORTS: 0.97,
        Q_CRICKET: 0.96,
        Q_FOOTBALL: 0.12,
        Q_SKATING: 0.04,
        Q_BOXING: 0.04,
        Q_FENCING: 0.03,
        Q_MARTIAL: 0.05,
        Q_BATSMAN: 0.92,
        Q_CHEF: 0.04,
        Q_ANIME: 0.02,
        Q_NINJA: 0.02,
        Q_POWERS: 0.02,
        Q_SUPERHERO: 0.05,
        Q_CRIME: 0.05,
        Q_MOVIES: 0.1,
        Q_INDIA: 0.95,
    },
    MESSI: {
        Q_REAL: 0.95,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_HUMAN: 0.95,
        Q_SPORTS: 0.98,
        Q_CRICKET: 0.08,
        Q_FOOTBALL: 0.97,
        Q_SKATING: 0.04,
        Q_BOXING: 0.05,
        Q_FENCING: 0.03,
        Q_MARTIAL: 0.05,
        Q_BATSMAN: 0.05,
        Q_CHEF: 0.04,
        Q_ANIME: 0.02,
        Q_NINJA: 0.02,
        Q_POWERS: 0.02,
        Q_SUPERHERO: 0.05,
        Q_CRIME: 0.05,
        Q_MOVIES: 0.1,
        Q_INDIA: 0.05,
    },
    SRK: {
        Q_REAL: 0.95,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_HUMAN: 0.95,
        Q_SPORTS: 0.08,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_SKATING: 0.03,
        Q_BOXING: 0.03,
        Q_FENCING: 0.03,
        Q_MARTIAL: 0.04,
        Q_BATSMAN: 0.04,
        Q_CHEF: 0.05,
        Q_ANIME: 0.04,
        Q_NINJA: 0.03,
        Q_POWERS: 0.05,
        Q_SUPERHERO: 0.1,
        Q_CRIME: 0.2,
        Q_MOVIES: 0.96,
        Q_INDIA: 0.9,
    },
    NARUTO: {
        Q_REAL: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.2,
        Q_FAMOUS: 0.9,
        Q_HUMAN: 0.9,
        Q_SPORTS: 0.05,
        Q_CRICKET: 0.02,
        Q_FOOTBALL: 0.02,
        Q_SKATING: 0.02,
        Q_BOXING: 0.02,
        Q_FENCING: 0.02,
        Q_MARTIAL: 0.15,
        Q_BATSMAN: 0.02,
        Q_CHEF: 0.04,
        Q_ANIME: 0.98,
        Q_NINJA: 0.96,
        Q_POWERS: 0.95,
        Q_SUPERHERO: 0.2,
        Q_CRIME: 0.15,
        Q_MOVIES: 0.15,
        Q_INDIA: 0.05,
    },
    BATMAN: {
        Q_REAL: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.15,
        Q_FAMOUS: 0.95,
        Q_HUMAN: 0.95,
        Q_SPORTS: 0.05,
        Q_CRICKET: 0.02,
        Q_FOOTBALL: 0.02,
        Q_SKATING: 0.02,
        Q_BOXING: 0.08,
        Q_FENCING: 0.05,
        Q_MARTIAL: 0.2,
        Q_BATSMAN: 0.02,
        Q_CHEF: 0.04,
        Q_ANIME: 0.08,
        Q_NINJA: 0.1,
        Q_POWERS: 0.25,
        Q_SUPERHERO: 0.97,
        Q_CRIME: 0.96,
        Q_MOVIES: 0.95,
        Q_INDIA: 0.05,
    },
    OBSCURE: {
        Q_REAL: 0.9,
        Q_MALE: 0.9,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.2,
        Q_HUMAN: 0.95,
        Q_SPORTS: 0.9,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_SKATING: 0.95,
        Q_BOXING: 0.05,
        Q_FENCING: 0.05,
        Q_MARTIAL: 0.05,
        Q_BATSMAN: 0.05,
        Q_CHEF: 0.05,
        Q_ANIME: 0.02,
        Q_NINJA: 0.02,
        Q_POWERS: 0.02,
        Q_SUPERHERO: 0.05,
        Q_CRIME: 0.05,
        Q_MOVIES: 0.1,
        Q_INDIA: 0.2,
    },
}


def _likelihoods() -> dict[tuple[UUID, UUID], LikelihoodEntry]:
    out: dict[tuple[UUID, UUID], LikelihoodEntry] = {}
    for cid, answers in PROFILE.items():
        for qid, value in answers.items():
            out[(cid, qid)] = LikelihoodEntry(value, 40)
    return out


def _play(true_id: UUID, *, max_questions: int = 12, seed: int = 3) -> list[UUID]:
    rng = random.Random(seed)
    likelihoods = _likelihoods()
    state = create_initial_state(CHARS, likelihoods)
    asked: list[UUID] = []
    for _ in range(max_questions):
        qid = select_next_question(
            state,
            QUESTIONS,
            min_samples=1,
            question_refs=REFS,
            character_categories=CATEGORIES,
            explore=False,
            rng=rng,
        )
        if qid is None:
            break
        asked.append(qid)
        ans = oracle_answer(likelihoods, true_id, qid, rng, noise=0.0)
        state, _ = process_answer(state, qid, ans)
    return asked


def _manager() -> GameSessionManager:
    return GameSessionManager(
        thresholds=ConfidenceThresholds(
            high=0.85, separation=0.6, margin=0.4, max_questions=20
        ),
        min_samples=1,
    )


def _start_mgr():
    mgr = _manager()
    live = mgr.start(
        session_id=uuid4(),
        character_ids=CHARS,
        likelihoods=_likelihoods(),
        question_ids=QUESTIONS,
        question_refs=REFS,
        character_names=NAMES,
        character_categories=CATEGORIES,
        character_popularity=POPULARITY,
    )
    return mgr, live


def test_first_questions_are_broad():
    state = create_initial_state(CHARS, _likelihoods())
    qid = select_next_question(
        state,
        QUESTIONS,
        min_samples=1,
        question_refs=REFS,
        character_categories=CATEGORIES,
        explore=False,
    )
    assert qid in BROAD


def test_early_questions_never_skating_boxing_fencing_martial():
    for true_id in (KOHLI, MESSI, NARUTO, BATMAN):
        asked = _play(true_id, max_questions=5)
        assert not set(asked) & {Q_SKATING, Q_BOXING, Q_FENCING, Q_MARTIAL}


def test_early_questions_never_obscure_professions():
    for true_id in (KOHLI, MESSI, NARUTO, BATMAN):
        asked = _play(true_id, max_questions=5)
        assert Q_CHEF not in asked


def test_anime_blocked_on_real_person_path():
    asked = _play(KOHLI, max_questions=10)
    assert Q_NINJA not in asked
    assert Q_POWERS not in asked


def test_sports_specific_after_athlete():
    asked = _play(KOHLI, max_questions=12)
    assert Q_SPORTS in asked
    subtypes = [q for q in asked if q in SPORT_SUBTYPES]
    if subtypes:
        assert asked.index(Q_SPORTS) < asked.index(subtypes[0])
    if Q_BATSMAN in asked:
        assert any(q in asked for q in SPORT_SUBTYPES)
        assert min(asked.index(q) for q in SPORT_SUBTYPES if q in asked) < asked.index(
            Q_BATSMAN
        )


def test_questions_not_repeated():
    asked = _play(MESSI, max_questions=12)
    assert len(asked) == len(set(asked))


def test_no_consecutive_unrelated_narrow_sports():
    asked = _play(KOHLI, max_questions=12)
    for i in range(1, len(asked)):
        if asked[i] in SPORT_SUBTYPES:
            assert asked[i - 1] not in SPORT_SUBTYPES


def test_virat_athlete_cricket_path():
    asked = _play(KOHLI, max_questions=12)
    assert asked[0] in BROAD
    assert Q_SPORTS in asked
    if Q_CRICKET in asked:
        assert asked.index(Q_SPORTS) < asked.index(Q_CRICKET)
    assert not set(asked[:6]) & {Q_SKATING, Q_BOXING, Q_FENCING, Q_MARTIAL, Q_CHEF}


def test_messi_athlete_football_path():
    asked = _play(MESSI, max_questions=12)
    assert Q_SPORTS in asked
    if Q_FOOTBALL in asked:
        assert asked.index(Q_SPORTS) < asked.index(Q_FOOTBALL)


def test_naruto_fictional_anime_path():
    asked = _play(NARUTO, max_questions=12)
    assert Q_ANIME in asked
    if Q_NINJA in asked:
        assert asked.index(Q_ANIME) < asked.index(Q_NINJA)
    assert Q_SPORTS not in asked or asked.index(Q_ANIME) < asked.index(Q_SPORTS)


def test_batman_fictional_superhero_path():
    asked = _play(BATMAN, max_questions=12)
    assert Q_SUPERHERO in asked or Q_MOVIES in asked
    early = asked[:5]
    assert Q_NINJA not in early
    assert Q_CHEF not in early


def test_confidence_nonzero_with_valid_probs():
    state = create_initial_state(CHARS, _likelihoods())
    assert confidence_score(state) > 0


def test_confidence_changes_increases_decreases():
    mgr, live = _start_mgr()
    start_conf = max(live.engine.probabilities.values())
    live.pending_question_id = Q_SPORTS
    up = mgr.submit_answer(live, Q_SPORTS, "yes")
    assert up.top_confidence != pytest.approx(start_conf, abs=1e-9)
    assert up.top_confidence > start_conf

    mgr2, live2 = _start_mgr()
    live2.pending_question_id = Q_SPORTS
    mgr2.submit_answer(live2, Q_SPORTS, "yes")
    after_yes = live2.engine.probabilities[MESSI]
    live2.pending_question_id = Q_CRICKET
    down = mgr2.submit_answer(live2, Q_CRICKET, "yes")
    # Cricket=yes eliminates / crushes footballers like Messi.
    assert MESSI not in live2.engine.probabilities or live2.engine.probabilities[MESSI] < after_yes
    assert down.top_confidence != pytest.approx(up.top_confidence, abs=1e-6)


def test_confidence_high_when_one_candidate_dominates():
    state = create_initial_state([KOHLI, MESSI], _likelihoods())
    state.probabilities = {KOHLI: 0.92, MESSI: 0.08}
    result = evaluate_confidence(state, confidence_high=0.85)
    assert result.should_guess
    assert result.confidence >= 0.85


def test_game_can_finish_before_20_questions():
    mgr, live = _start_mgr()
    # Drive toward Kohli with strong sports + cricket answers.
    for qid, ans in [
        (Q_ALIVE, "yes"),
        (Q_REAL, "yes"),
        (Q_SPORTS, "yes"),
        (Q_CRICKET, "yes"),
        (Q_BATSMAN, "yes"),
        (Q_INDIA, "yes"),
    ]:
        if live.awaiting_guess:
            break
        live.pending_question_id = qid
        turn = mgr.submit_answer(live, qid, ans)
    assert live.engine.questions_asked < 20
    # Either ready to guess or confidence clearly elevated.
    assert live.awaiting_guess or turn.top_confidence >= 0.5


def test_popularity_tie_break_prefers_famous_character():
    mgr, live = _start_mgr()
    live.engine.probabilities = {KOHLI: 0.5, OBSCURE: 0.5}
    assert mgr.best_guess_id(live) == KOHLI


def test_normalize_probabilities_sums_to_one():
    fixed = normalize_probabilities({KOHLI: 2.0, MESSI: 1.0})
    assert sum(fixed.values()) == pytest.approx(1.0)


def test_sport_subtype_helpers():
    assert is_sport_subtype_question(REFS[Q_SKATING])
    assert is_sport_subtype_question(REFS[Q_BOXING])
    assert not is_sport_subtype_question(REFS[Q_SPORTS])
