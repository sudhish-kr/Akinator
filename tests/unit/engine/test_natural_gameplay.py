"""Natural gameplay experience — Stage 1→4 flow for iconic characters."""

from __future__ import annotations

import random
from uuid import UUID

from app.engine.constants import FORBIDDEN_EARLY_KEYWORDS
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    process_answer,
    question_hierarchy_stage,
    resolve_selection_stage,
    select_next_question,
)
from app.training.oracle import oracle_answer

KOHLI = UUID("00000000-0000-0000-0000-000000000501")
MESSI = UUID("00000000-0000-0000-0000-000000000502")
SRK = UUID("00000000-0000-0000-0000-000000000503")
NARUTO = UUID("00000000-0000-0000-0000-000000000504")
BATMAN = UUID("00000000-0000-0000-0000-000000000505")

Q_REAL = UUID("00000000-0000-0000-0000-000000000601")
Q_MADE_UP = UUID("00000000-0000-0000-0000-000000000602")
Q_MALE = UUID("00000000-0000-0000-0000-000000000603")
Q_ALIVE = UUID("00000000-0000-0000-0000-000000000604")
Q_KID = UUID("00000000-0000-0000-0000-000000000605")
Q_INDIA = UUID("00000000-0000-0000-0000-000000000606")
Q_MODERN = UUID("00000000-0000-0000-0000-000000000607")
Q_SPORTS = UUID("00000000-0000-0000-0000-000000000608")
Q_MOVIES = UUID("00000000-0000-0000-0000-000000000609")
Q_ANIME = UUID("00000000-0000-0000-0000-000000000610")
Q_CRICKET = UUID("00000000-0000-0000-0000-000000000611")
Q_CHEF = UUID("00000000-0000-0000-0000-000000000612")
Q_VAMPIRE = UUID("00000000-0000-0000-0000-000000000613")
Q_NINJA = UUID("00000000-0000-0000-0000-000000000614")

CHARS = [KOHLI, MESSI, SRK, NARUTO, BATMAN]
QUESTIONS = [
    Q_REAL,
    Q_MADE_UP,
    Q_MALE,
    Q_ALIVE,
    Q_KID,
    Q_INDIA,
    Q_MODERN,
    Q_SPORTS,
    Q_MOVIES,
    Q_ANIME,
    Q_CRICKET,
    Q_CHEF,
    Q_VAMPIRE,
    Q_NINJA,
]

REFS = {
    Q_REAL: QuestionRef(id=Q_REAL, text="Is this a real person?", category="Personality"),
    Q_MADE_UP: QuestionRef(
        id=Q_MADE_UP, text="Is this a made-up character?", category="Fictional traits"
    ),
    Q_MALE: QuestionRef(id=Q_MALE, text="Are they male?", category="Gender"),
    Q_ALIVE: QuestionRef(id=Q_ALIVE, text="Is this person still alive?", category="Age"),
    Q_KID: QuestionRef(id=Q_KID, text="Are they a kid or teen?", category="Age"),
    Q_INDIA: QuestionRef(id=Q_INDIA, text="Are they from India?", category="Nationality"),
    Q_MODERN: QuestionRef(
        id=Q_MODERN, text="Are they from modern times?", category="Time period"
    ),
    Q_SPORTS: QuestionRef(id=Q_SPORTS, text="Is this a sports player?", category="Sports"),
    Q_MOVIES: QuestionRef(id=Q_MOVIES, text="Is this from a movie?", category="Movies"),
    Q_ANIME: QuestionRef(id=Q_ANIME, text="Is this from anime?", category="Anime"),
    Q_CRICKET: QuestionRef(
        id=Q_CRICKET, text="Are they famous for cricket?", category="Sports"
    ),
    Q_CHEF: QuestionRef(id=Q_CHEF, text="Are they a chef?", category="Profession"),
    Q_VAMPIRE: QuestionRef(id=Q_VAMPIRE, text="Are they a vampire?", category="Movies"),
    Q_NINJA: QuestionRef(id=Q_NINJA, text="Are they a ninja or samurai?", category="Anime"),
}

CATEGORIES = {
    KOHLI: "Sports",
    MESSI: "Sports",
    SRK: "Movies",
    NARUTO: "Anime",
    BATMAN: "Movies",
}

PROFILE = {
    KOHLI: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_KID: 0.05,
        Q_INDIA: 0.95,
        Q_MODERN: 0.9,
        Q_SPORTS: 0.97,
        Q_MOVIES: 0.1,
        Q_ANIME: 0.02,
        Q_CRICKET: 0.96,
        Q_CHEF: 0.05,
        Q_VAMPIRE: 0.02,
        Q_NINJA: 0.02,
    },
    MESSI: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_KID: 0.05,
        Q_INDIA: 0.05,
        Q_MODERN: 0.9,
        Q_SPORTS: 0.97,
        Q_MOVIES: 0.1,
        Q_ANIME: 0.02,
        Q_CRICKET: 0.1,
        Q_CHEF: 0.05,
        Q_VAMPIRE: 0.02,
        Q_NINJA: 0.02,
    },
    SRK: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_KID: 0.05,
        Q_INDIA: 0.95,
        Q_MODERN: 0.9,
        Q_SPORTS: 0.05,
        Q_MOVIES: 0.96,
        Q_ANIME: 0.02,
        Q_CRICKET: 0.05,
        Q_CHEF: 0.05,
        Q_VAMPIRE: 0.02,
        Q_NINJA: 0.02,
    },
    NARUTO: {
        Q_REAL: 0.05,
        Q_MADE_UP: 0.95,
        Q_MALE: 0.95,
        Q_ALIVE: 0.5,
        Q_KID: 0.7,
        Q_INDIA: 0.05,
        Q_MODERN: 0.5,
        Q_SPORTS: 0.05,
        Q_MOVIES: 0.2,
        Q_ANIME: 0.97,
        Q_CRICKET: 0.05,
        Q_CHEF: 0.05,
        Q_VAMPIRE: 0.05,
        Q_NINJA: 0.95,
    },
    BATMAN: {
        Q_REAL: 0.1,
        Q_MADE_UP: 0.9,
        Q_MALE: 0.95,
        Q_ALIVE: 0.5,
        Q_KID: 0.1,
        Q_INDIA: 0.05,
        Q_MODERN: 0.55,
        Q_SPORTS: 0.1,
        Q_MOVIES: 0.96,
        Q_ANIME: 0.05,
        Q_CRICKET: 0.05,
        Q_CHEF: 0.05,
        Q_VAMPIRE: 0.05,
        Q_NINJA: 0.05,
    },
}


def _likelihoods():
    return {
        (cid, qid): LikelihoodEntry(v, 50)
        for cid, answers in PROFILE.items()
        for qid, v in answers.items()
    }


def _play(true_id: UUID, *, max_questions: int = 8, seed: int = 5) -> list[UUID]:
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


def test_question_stages_map_identity_origin_category_subcategory():
    assert question_hierarchy_stage(REFS[Q_REAL]) == "1"
    assert question_hierarchy_stage(REFS[Q_INDIA]) == "2"
    assert question_hierarchy_stage(REFS[Q_SPORTS]) == "3"
    assert question_hierarchy_stage(REFS[Q_CRICKET]) == "4"
    assert question_hierarchy_stage(REFS[Q_CHEF]) == "4"
    assert question_hierarchy_stage(REFS[Q_VAMPIRE]) == "4"


def test_uniform_start_is_stage_1_identity_only():
    equal = [KOHLI, SRK, NARUTO]  # one category each — equal mass
    cats = {cid: CATEGORIES[cid] for cid in equal}
    L = {
        (cid, qid): LikelihoodEntry(PROFILE[cid][qid], 50)
        for cid in equal
        for qid in PROFILE[cid]
    }
    state = create_initial_state(equal, L)
    stage, _ = resolve_selection_stage(state, cats)
    assert stage == "1"
    qid = select_next_question(
        state,
        QUESTIONS,
        min_samples=1,
        question_refs=REFS,
        character_categories=cats,
        explore=False,
    )
    assert qid is not None
    assert question_hierarchy_stage(REFS[qid]) == "1"
    text = REFS[qid].text.casefold()
    for kw in FORBIDDEN_EARLY_KEYWORDS:
        assert kw not in text


def test_icons_never_get_forbidden_early_questions():
    for true_id, label in [
        (KOHLI, "Virat Kohli"),
        (MESSI, "Lionel Messi"),
        (SRK, "Shah Rukh Khan"),
        (NARUTO, "Naruto"),
        (BATMAN, "Batman"),
    ]:
        asked = _play(true_id, max_questions=5, seed=7)
        assert asked, label
        state = create_initial_state(CHARS, _likelihoods())
        rng = random.Random(7)
        for qid in asked:
            stage, _ = resolve_selection_stage(state, CATEGORIES)
            text = REFS[qid].text.casefold()
            if stage in {"1", "2", "3"}:
                for kw in FORBIDDEN_EARLY_KEYWORDS:
                    assert kw not in text, (label, stage, text)
                assert qid not in {Q_CHEF, Q_VAMPIRE}
                assert question_hierarchy_stage(REFS[qid]) != "4" or stage == "4"
            answer = oracle_answer(_likelihoods(), true_id, qid, rng, noise=0.0)
            state, _ = process_answer(state, qid, answer)


def test_virat_path_stays_off_anime_early():
    asked = _play(KOHLI, max_questions=6, seed=11)
    state = create_initial_state(CHARS, _likelihoods())
    rng = random.Random(11)
    for qid in asked:
        stage, dominant = resolve_selection_stage(state, CATEGORIES)
        if stage in {"1", "2"}:
            assert REFS[qid].category != "Anime"
        if REFS[qid].category == "Anime":
            assert dominant == "Anime"
        answer = oracle_answer(_likelihoods(), KOHLI, qid, rng, noise=0.0)
        state, _ = process_answer(state, qid, answer)


def test_naruto_path_stays_off_sports_early():
    asked = _play(NARUTO, max_questions=6, seed=11)
    state = create_initial_state(CHARS, _likelihoods())
    rng = random.Random(11)
    for qid in asked:
        stage, dominant = resolve_selection_stage(state, CATEGORIES)
        if stage in {"1", "2"}:
            assert REFS[qid].category != "Sports"
        if REFS[qid].category == "Sports":
            assert dominant == "Sports"
        answer = oracle_answer(_likelihoods(), NARUTO, qid, rng, noise=0.0)
        state, _ = process_answer(state, qid, answer)


def test_five_icons_receive_distinct_natural_paths():
    paths = {
        "Virat Kohli": tuple(_play(KOHLI)),
        "Lionel Messi": tuple(_play(MESSI)),
        "Shah Rukh Khan": tuple(_play(SRK)),
        "Naruto": tuple(_play(NARUTO)),
        "Batman": tuple(_play(BATMAN)),
    }
    assert all(len(seq) >= 2 for seq in paths.values())
    assert len(set(paths.values())) >= 3
