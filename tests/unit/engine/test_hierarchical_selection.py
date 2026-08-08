"""Regression tests for hierarchical Stage A → B → C question selection."""

from __future__ import annotations

import random
from uuid import UUID

from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    process_answer,
    question_hierarchy_stage,
    resolve_selection_stage,
    select_next_question,
)
from app.training.oracle import oracle_answer

# Characters under test
KOHLI = UUID("00000000-0000-0000-0000-000000000301")
MESSI = UUID("00000000-0000-0000-0000-000000000302")
EINSTEIN = UUID("00000000-0000-0000-0000-000000000303")
NARUTO = UUID("00000000-0000-0000-0000-000000000304")
BATMAN = UUID("00000000-0000-0000-0000-000000000305")

# Stage A
Q_REAL = UUID("00000000-0000-0000-0000-000000000401")
Q_MADE_UP = UUID("00000000-0000-0000-0000-000000000402")
Q_ALIVE = UUID("00000000-0000-0000-0000-000000000403")
Q_MALE = UUID("00000000-0000-0000-0000-000000000404")
Q_KID = UUID("00000000-0000-0000-0000-000000000405")

# Stage B domains
Q_SPORTS = UUID("00000000-0000-0000-0000-000000000411")
Q_ANIME = UUID("00000000-0000-0000-0000-000000000412")
Q_MOVIES = UUID("00000000-0000-0000-0000-000000000413")
Q_SCIENCE = UUID("00000000-0000-0000-0000-000000000414")

# Stage C specifics
Q_CHEF = UUID("00000000-0000-0000-0000-000000000421")
Q_ARCHITECT = UUID("00000000-0000-0000-0000-000000000422")
Q_LAWYER = UUID("00000000-0000-0000-0000-000000000423")
Q_CRICKET = UUID("00000000-0000-0000-0000-000000000424")
Q_FOOTBALL = UUID("00000000-0000-0000-0000-000000000425")
Q_NINJA = UUID("00000000-0000-0000-0000-000000000426")
Q_NOBEL = UUID("00000000-0000-0000-0000-000000000427")

CHARS = [KOHLI, MESSI, EINSTEIN, NARUTO, BATMAN]
QUESTIONS = [
    Q_REAL,
    Q_MADE_UP,
    Q_ALIVE,
    Q_MALE,
    Q_KID,
    Q_SPORTS,
    Q_ANIME,
    Q_MOVIES,
    Q_SCIENCE,
    Q_CHEF,
    Q_ARCHITECT,
    Q_LAWYER,
    Q_CRICKET,
    Q_FOOTBALL,
    Q_NINJA,
    Q_NOBEL,
]

REFS = {
    Q_REAL: QuestionRef(id=Q_REAL, text="Is this a real person?", category="Personality"),
    Q_MADE_UP: QuestionRef(
        id=Q_MADE_UP, text="Is this a made-up character?", category="Fictional traits"
    ),
    Q_ALIVE: QuestionRef(id=Q_ALIVE, text="Is this person still alive?", category="Age"),
    Q_MALE: QuestionRef(id=Q_MALE, text="Are they male?", category="Gender"),
    Q_KID: QuestionRef(id=Q_KID, text="Are they a kid or teen?", category="Age"),
    Q_SPORTS: QuestionRef(id=Q_SPORTS, text="Is this a sports player?", category="Sports"),
    Q_ANIME: QuestionRef(id=Q_ANIME, text="Is this from anime?", category="Anime"),
    Q_MOVIES: QuestionRef(id=Q_MOVIES, text="Is this from a movie?", category="Movies"),
    Q_SCIENCE: QuestionRef(id=Q_SCIENCE, text="Is this a scientist?", category="Science"),
    Q_CHEF: QuestionRef(id=Q_CHEF, text="Are they a chef?", category="Profession"),
    Q_ARCHITECT: QuestionRef(
        id=Q_ARCHITECT, text="Are they a architect?", category="Profession"
    ),
    Q_LAWYER: QuestionRef(id=Q_LAWYER, text="Are they a lawyer?", category="Profession"),
    Q_CRICKET: QuestionRef(
        id=Q_CRICKET, text="Are they famous for cricket?", category="Sports"
    ),
    Q_FOOTBALL: QuestionRef(
        id=Q_FOOTBALL, text="Are they famous for football?", category="Sports"
    ),
    Q_NINJA: QuestionRef(id=Q_NINJA, text="Are they a ninja or samurai?", category="Anime"),
    Q_NOBEL: QuestionRef(
        id=Q_NOBEL, text="Did they win a Nobel science prize?", category="Awards"
    ),
}

CATEGORIES = {
    KOHLI: "Sports",
    MESSI: "Sports",
    EINSTEIN: "Scientists",
    NARUTO: "Anime",
    BATMAN: "Movies",
}

PROFILE = {
    KOHLI: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_ALIVE: 0.9,
        Q_MALE: 0.95,
        Q_KID: 0.05,
        Q_SPORTS: 0.97,
        Q_ANIME: 0.02,
        Q_MOVIES: 0.1,
        Q_SCIENCE: 0.05,
        Q_CHEF: 0.05,
        Q_ARCHITECT: 0.05,
        Q_LAWYER: 0.05,
        Q_CRICKET: 0.96,
        Q_FOOTBALL: 0.2,
        Q_NINJA: 0.02,
        Q_NOBEL: 0.05,
    },
    MESSI: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_ALIVE: 0.9,
        Q_MALE: 0.95,
        Q_KID: 0.05,
        Q_SPORTS: 0.97,
        Q_ANIME: 0.02,
        Q_MOVIES: 0.1,
        Q_SCIENCE: 0.05,
        Q_CHEF: 0.05,
        Q_ARCHITECT: 0.05,
        Q_LAWYER: 0.05,
        Q_CRICKET: 0.1,
        Q_FOOTBALL: 0.97,
        Q_NINJA: 0.02,
        Q_NOBEL: 0.05,
    },
    EINSTEIN: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_ALIVE: 0.05,
        Q_MALE: 0.95,
        Q_KID: 0.05,
        Q_SPORTS: 0.05,
        Q_ANIME: 0.02,
        Q_MOVIES: 0.15,
        Q_SCIENCE: 0.96,
        Q_CHEF: 0.05,
        Q_ARCHITECT: 0.1,
        Q_LAWYER: 0.05,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_NINJA: 0.02,
        Q_NOBEL: 0.9,
    },
    NARUTO: {
        Q_REAL: 0.05,
        Q_MADE_UP: 0.95,
        Q_ALIVE: 0.5,
        Q_MALE: 0.95,
        Q_KID: 0.7,
        Q_SPORTS: 0.05,
        Q_ANIME: 0.97,
        Q_MOVIES: 0.25,
        Q_SCIENCE: 0.05,
        Q_CHEF: 0.05,
        Q_ARCHITECT: 0.05,
        Q_LAWYER: 0.05,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_NINJA: 0.95,
        Q_NOBEL: 0.02,
    },
    BATMAN: {
        Q_REAL: 0.1,
        Q_MADE_UP: 0.9,
        Q_ALIVE: 0.5,
        Q_MALE: 0.95,
        Q_KID: 0.1,
        Q_SPORTS: 0.1,
        Q_ANIME: 0.05,
        Q_MOVIES: 0.96,
        Q_SCIENCE: 0.2,
        Q_CHEF: 0.05,
        Q_ARCHITECT: 0.05,
        Q_LAWYER: 0.05,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_NINJA: 0.05,
        Q_NOBEL: 0.05,
    },
}


def _likelihoods() -> dict[tuple[UUID, UUID], LikelihoodEntry]:
    return {
        (cid, qid): LikelihoodEntry(lik, 50)
        for cid, answers in PROFILE.items()
        for qid, lik in answers.items()
    }


def _play(true_id: UUID, *, max_questions: int = 8, seed: int = 11) -> list[UUID]:
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
        answer = oracle_answer(likelihoods, true_id, qid, rng, noise=0.0)
        state, _ = process_answer(state, qid, answer)
        asked.append(qid)
    return asked


def test_question_hierarchy_marks_profession_and_franchise_as_stage_c():
    assert question_hierarchy_stage(REFS[Q_REAL]) == "A"
    assert question_hierarchy_stage(REFS[Q_SPORTS]) == "B"
    assert question_hierarchy_stage(REFS[Q_ANIME]) == "B"
    assert question_hierarchy_stage(REFS[Q_CHEF]) == "C"
    assert question_hierarchy_stage(REFS[Q_CRICKET]) == "C"
    assert question_hierarchy_stage(REFS[Q_NINJA]) == "C"
    assert question_hierarchy_stage(REFS[Q_NOBEL]) == "C"


def test_uniform_start_is_stage_a():
    # Equal mass across categories (one character each)
    equal_chars = [KOHLI, EINSTEIN, NARUTO, BATMAN]
    equal_cats = {cid: CATEGORIES[cid] for cid in equal_chars}
    equal_L = {
        (cid, qid): LikelihoodEntry(PROFILE[cid][qid], 50)
        for cid in equal_chars
        for qid in PROFILE[cid]
    }
    state = create_initial_state(equal_chars, equal_L)
    stage, _ = resolve_selection_stage(state, equal_cats)
    assert stage == "A"
    qid = select_next_question(
        state,
        QUESTIONS,
        min_samples=1,
        question_refs=REFS,
        character_categories=equal_cats,
        explore=False,
    )
    assert qid is not None
    assert question_hierarchy_stage(REFS[qid]) == "A"
    assert qid not in {Q_CHEF, Q_ARCHITECT, Q_LAWYER, Q_ANIME, Q_SPORTS, Q_CRICKET}


def test_missing_category_map_fails_safe_to_broad_only():
    state = create_initial_state(CHARS, _likelihoods())
    qid = select_next_question(
        state,
        QUESTIONS,
        min_samples=1,
        question_refs=REFS,
        character_categories=None,
        explore=False,
    )
    assert qid is not None
    assert question_hierarchy_stage(REFS[qid]) == "A"


def test_early_gameplay_never_asks_profession_specific_questions():
    """Chef / Architect / Lawyer stay locked until Stage C with a Profession-preferring domain."""
    profession_ids = {Q_CHEF, Q_ARCHITECT, Q_LAWYER}
    likelihoods = _likelihoods()
    for true_id in CHARS:
        rng = random.Random(3)
        state = create_initial_state(CHARS, likelihoods)
        for _ in range(4):
            stage, _dominant = resolve_selection_stage(state, CATEGORIES)
            qid = select_next_question(
                state,
                QUESTIONS,
                min_samples=1,
                question_refs=REFS,
                character_categories=CATEGORIES,
                explore=False,
                rng=rng,
            )
            assert qid is not None, true_id
            text = REFS[qid].text.casefold()
            if stage in {"A", "B"}:
                assert "chef" not in text
                assert "architect" not in text
                assert "lawyer" not in text
                assert qid not in profession_ids
                assert REFS[qid].category != "Profession"
            answer = oracle_answer(likelihoods, true_id, qid, rng, noise=0.0)
            state, _ = process_answer(state, qid, answer)


def test_virat_path_never_asks_anime_questions_early():
    asked = _play(KOHLI, max_questions=6, seed=11)
    assert asked
    # First two turns must stay Stage A / non-Anime
    for qid in asked[:3]:
        assert REFS[qid].category != "Anime"
        assert qid != Q_NINJA
    # Across full early path, Anime domain must not appear before Sports dominates
    state = create_initial_state(CHARS, _likelihoods())
    rng = random.Random(11)
    for qid in asked:
        stage, dominant = resolve_selection_stage(state, CATEGORIES)
        if stage == "A":
            assert REFS[qid].category != "Anime"
        if REFS[qid].category == "Anime":
            assert dominant == "Anime"
        answer = oracle_answer(_likelihoods(), KOHLI, qid, rng, noise=0.0)
        state, _ = process_answer(state, qid, answer)


def test_naruto_path_never_asks_sports_questions_early():
    asked = _play(NARUTO, max_questions=6, seed=11)
    assert asked
    state = create_initial_state(CHARS, _likelihoods())
    rng = random.Random(11)
    for qid in asked:
        stage, dominant = resolve_selection_stage(state, CATEGORIES)
        if stage == "A":
            assert REFS[qid].category != "Sports"
            assert qid not in {Q_CRICKET, Q_FOOTBALL, Q_SPORTS}
        if REFS[qid].category == "Sports":
            assert dominant == "Sports"
        answer = oracle_answer(_likelihoods(), NARUTO, qid, rng, noise=0.0)
        state, _ = process_answer(state, qid, answer)


def test_five_icons_receive_distinct_hierarchical_paths():
    paths = {
        "Virat Kohli": tuple(_play(KOHLI)),
        "Lionel Messi": tuple(_play(MESSI)),
        "Albert Einstein": tuple(_play(EINSTEIN)),
        "Naruto": tuple(_play(NARUTO)),
        "Batman": tuple(_play(BATMAN)),
    }
    assert all(len(seq) >= 2 for seq in paths.values())
    assert len(set(paths.values())) == 5
