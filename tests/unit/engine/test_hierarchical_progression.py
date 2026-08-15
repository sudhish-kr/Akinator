"""Strict hierarchical progression: identity → category → subtype → specific."""

from __future__ import annotations

import random
from uuid import UUID, uuid4

from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    flow_level,
    is_sport_subtype_question,
    process_answer,
    question_hierarchy_stage,
    select_next_question,
)
from app.training.oracle import oracle_answer

KOHLI = UUID("00000000-0000-0000-0000-000000000b01")
MESSI = UUID("00000000-0000-0000-0000-000000000b02")
SRK = UUID("00000000-0000-0000-0000-000000000b03")
NARUTO = UUID("00000000-0000-0000-0000-000000000b04")

Q_REAL = UUID("00000000-0000-0000-0000-000000000c01")
Q_MALE = UUID("00000000-0000-0000-0000-000000000c02")
Q_ALIVE = UUID("00000000-0000-0000-0000-000000000c03")
Q_FAMOUS = UUID("00000000-0000-0000-0000-000000000c04")
Q_SPORTS = UUID("00000000-0000-0000-0000-000000000c05")
Q_CRICKET = UUID("00000000-0000-0000-0000-000000000c06")
Q_FOOTBALL = UUID("00000000-0000-0000-0000-000000000c07")
Q_SKATING = UUID("00000000-0000-0000-0000-000000000c08")
Q_BOXING = UUID("00000000-0000-0000-0000-000000000c09")
Q_FENCING = UUID("00000000-0000-0000-0000-000000000c0a")
Q_MARTIAL = UUID("00000000-0000-0000-0000-000000000c0b")
Q_BATSMAN = UUID("00000000-0000-0000-0000-000000000c0c")
Q_CHEF = UUID("00000000-0000-0000-0000-000000000c0d")
Q_ANIME = UUID("00000000-0000-0000-0000-000000000c0e")
Q_NINJA = UUID("00000000-0000-0000-0000-000000000c0f")
Q_INDIA = UUID("00000000-0000-0000-0000-000000000c10")

CHARS = [KOHLI, MESSI, SRK, NARUTO]
QUESTIONS = [
    Q_REAL,
    Q_MALE,
    Q_ALIVE,
    Q_FAMOUS,
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
    Q_INDIA,
]

REFS = {
    Q_REAL: QuestionRef(id=Q_REAL, text="Is this a real person?", category="Personality"),
    Q_MALE: QuestionRef(id=Q_MALE, text="Are they male?", category="Gender"),
    Q_ALIVE: QuestionRef(id=Q_ALIVE, text="Is this person still alive?", category="Age"),
    Q_FAMOUS: QuestionRef(
        id=Q_FAMOUS, text="Are they famous worldwide?", category="Personality"
    ),
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
    Q_INDIA: QuestionRef(id=Q_INDIA, text="Are they from India?", category="Nationality"),
}

CATEGORIES = {
    KOHLI: "Sports",
    MESSI: "Sports",
    SRK: "Movies",
    NARUTO: "Anime",
}

SPORT_SUBTYPES = {Q_CRICKET, Q_FOOTBALL, Q_SKATING, Q_BOXING, Q_FENCING, Q_MARTIAL}

PROFILE = {
    KOHLI: {
        Q_REAL: 0.95,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_SPORTS: 0.97,
        Q_CRICKET: 0.96,
        Q_FOOTBALL: 0.15,
        Q_SKATING: 0.05,
        Q_BOXING: 0.05,
        Q_FENCING: 0.05,
        Q_MARTIAL: 0.08,
        Q_BATSMAN: 0.9,
        Q_CHEF: 0.05,
        Q_ANIME: 0.02,
        Q_NINJA: 0.02,
        Q_INDIA: 0.95,
    },
    MESSI: {
        Q_REAL: 0.95,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_SPORTS: 0.97,
        Q_CRICKET: 0.1,
        Q_FOOTBALL: 0.96,
        Q_SKATING: 0.05,
        Q_BOXING: 0.05,
        Q_FENCING: 0.05,
        Q_MARTIAL: 0.08,
        Q_BATSMAN: 0.05,
        Q_CHEF: 0.05,
        Q_ANIME: 0.02,
        Q_NINJA: 0.02,
        Q_INDIA: 0.05,
    },
    SRK: {
        Q_REAL: 0.95,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_SPORTS: 0.05,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_SKATING: 0.02,
        Q_BOXING: 0.02,
        Q_FENCING: 0.02,
        Q_MARTIAL: 0.02,
        Q_BATSMAN: 0.02,
        Q_CHEF: 0.05,
        Q_ANIME: 0.02,
        Q_NINJA: 0.02,
        Q_INDIA: 0.95,
    },
    NARUTO: {
        Q_REAL: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.55,
        Q_FAMOUS: 0.9,
        Q_SPORTS: 0.05,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_SKATING: 0.02,
        Q_BOXING: 0.02,
        Q_FENCING: 0.02,
        Q_MARTIAL: 0.2,
        Q_BATSMAN: 0.02,
        Q_CHEF: 0.05,
        Q_ANIME: 0.97,
        Q_NINJA: 0.95,
        Q_INDIA: 0.05,
    },
}


def _likelihoods():
    return {
        (cid, qid): LikelihoodEntry(v, 50)
        for cid, answers in PROFILE.items()
        for qid, v in answers.items()
    }


def _play(true_id: UUID, *, max_questions: int = 10, seed: int = 3) -> list[UUID]:
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
        assert qid not in asked
        answer = oracle_answer(likelihoods, true_id, qid, rng, noise=0.0)
        state, _ = process_answer(state, qid, answer)
        asked.append(qid)
    return asked


def test_sport_subtypes_classified_as_stage_4_not_major_category():
    for qid in SPORT_SUBTYPES:
        assert is_sport_subtype_question(REFS[qid])
        assert question_hierarchy_stage(REFS[qid]) == "4"
        assert flow_level(REFS[qid]) == 3
    assert question_hierarchy_stage(REFS[Q_SPORTS]) == "3"
    assert flow_level(REFS[Q_SPORTS]) == 2
    assert flow_level(REFS[Q_REAL]) == 1
    assert flow_level(REFS[Q_BATSMAN]) == 4


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
    assert qid in {Q_REAL, Q_MALE, Q_ALIVE, Q_FAMOUS}
    assert qid not in SPORT_SUBTYPES | {Q_CHEF, Q_NINJA, Q_BATSMAN}


def test_category_before_subcategory():
    asked = _play(KOHLI, max_questions=10)
    assert Q_SPORTS in asked
    subtypes_asked = [q for q in asked if q in SPORT_SUBTYPES]
    if subtypes_asked:
        assert asked.index(Q_SPORTS) < asked.index(subtypes_asked[0])


def test_subcategory_before_specific():
    asked = _play(KOHLI, max_questions=12)
    if Q_BATSMAN in asked:
        assert any(q in asked for q in SPORT_SUBTYPES)
        first_sub = min(asked.index(q) for q in SPORT_SUBTYPES if q in asked)
        assert first_sub < asked.index(Q_BATSMAN)


def test_no_consecutive_sport_subtypes():
    asked = _play(KOHLI, max_questions=12)
    for i in range(1, len(asked)):
        if asked[i] in SPORT_SUBTYPES:
            assert asked[i - 1] not in SPORT_SUBTYPES


def test_skating_boxing_fencing_martial_not_early():
    for true_id in (KOHLI, MESSI):
        asked = _play(true_id, max_questions=5)
        assert not set(asked) & {Q_SKATING, Q_BOXING, Q_FENCING, Q_MARTIAL}


def test_profession_before_category_blocked():
    asked = _play(KOHLI, max_questions=5)
    assert Q_CHEF not in asked


def test_anime_specific_blocked_on_real_path():
    asked = _play(KOHLI, max_questions=10)
    assert Q_NINJA not in asked
    assert Q_ANIME not in asked or (
        Q_SPORTS in asked and asked.index(Q_SPORTS) < asked.index(Q_ANIME)
    )


def test_questions_not_repeated():
    asked = _play(MESSI, max_questions=12)
    assert len(asked) == len(set(asked))


def test_kohli_broad_athlete_cricket_path():
    asked = _play(KOHLI, max_questions=10)
    assert asked[0] in {Q_REAL, Q_MALE, Q_ALIVE, Q_FAMOUS}
    assert Q_SPORTS in asked
    if Q_CRICKET in asked:
        assert asked.index(Q_SPORTS) < asked.index(Q_CRICKET)
    # Must not spam obscure sports before/instead of cricket
    early = asked[:6]
    assert Q_SKATING not in early
    assert Q_FENCING not in early


def test_messi_broad_athlete_football_path():
    asked = _play(MESSI, max_questions=10)
    assert Q_SPORTS in asked
    if Q_FOOTBALL in asked:
        assert asked.index(Q_SPORTS) < asked.index(Q_FOOTBALL)
    assert Q_SKATING not in asked[:6]


def test_one_level_step_helpers():
    assert flow_level(REFS[Q_REAL]) == 1
    assert flow_level(REFS[Q_SPORTS]) == 2
    assert flow_level(REFS[Q_CRICKET]) == 3
    assert flow_level(REFS[Q_BATSMAN]) == 4
    # Famous-for skating is a subtype, not identity.
    skating = QuestionRef(id=uuid4(), text="Is this person famous for skating?", category="Sports")
    assert is_sport_subtype_question(skating)
    assert flow_level(skating) == 3
