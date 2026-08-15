"""Regression: natural Akinator-style question progression and hard gates."""

from __future__ import annotations

import random
from uuid import UUID, uuid4

from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    is_akinator_filler_question,
    is_gender_question,
    is_hard_gated_niche,
    is_question_allowed_for_stage,
    is_reality_question,
    is_regional_state_question,
    process_answer,
    question_hierarchy_stage,
    select_next_question,
)
from app.training.oracle import oracle_answer

KOHLI = UUID("00000000-0000-0000-0000-000000000901")
MESSI = UUID("00000000-0000-0000-0000-000000000902")
SRK = UUID("00000000-0000-0000-0000-000000000903")
NARUTO = UUID("00000000-0000-0000-0000-000000000904")
BATMAN = UUID("00000000-0000-0000-0000-000000000905")
EINSTEIN = UUID("00000000-0000-0000-0000-000000000906")

Q_REAL = UUID("00000000-0000-0000-0000-000000000a01")
Q_MADE_UP = UUID("00000000-0000-0000-0000-000000000a02")
Q_MALE = UUID("00000000-0000-0000-0000-000000000a03")
Q_ALIVE = UUID("00000000-0000-0000-0000-000000000a04")
Q_FAMOUS = UUID("00000000-0000-0000-0000-000000000a05")
Q_HUMAN = UUID("00000000-0000-0000-0000-000000000a06")
Q_INDIA = UUID("00000000-0000-0000-0000-000000000a07")
Q_OTHER_COUNTRY = UUID("00000000-0000-0000-0000-000000000a08")
Q_SPORTS = UUID("00000000-0000-0000-0000-000000000a09")
Q_MOVIES = UUID("00000000-0000-0000-0000-000000000a0a")
Q_ANIME = UUID("00000000-0000-0000-0000-000000000a0b")
Q_CRICKET = UUID("00000000-0000-0000-0000-000000000a0c")
Q_FOOTBALL = UUID("00000000-0000-0000-0000-000000000a0d")
Q_CHEF = UUID("00000000-0000-0000-0000-000000000a0e")
Q_BABY = UUID("00000000-0000-0000-0000-000000000a0f")
Q_TODDLER = UUID("00000000-0000-0000-0000-000000000a10")
Q_TEEN = UUID("00000000-0000-0000-0000-000000000a11")
Q_GUILD = UUID("00000000-0000-0000-0000-000000000a12")
Q_NINJA = UUID("00000000-0000-0000-0000-000000000a13")
Q_SUPERHERO = UUID("00000000-0000-0000-0000-000000000a14")
Q_ICE = UUID("00000000-0000-0000-0000-000000000a15")
Q_JAPAN = UUID("00000000-0000-0000-0000-000000000a16")
Q_AUSTRALIA = UUID("00000000-0000-0000-0000-000000000a17")
Q_EUROPE = UUID("00000000-0000-0000-0000-000000000a18")
Q_AMERICAS = UUID("00000000-0000-0000-0000-000000000a19")
Q_USA = UUID("00000000-0000-0000-0000-000000000a1a")
Q_ALONE = UUID("00000000-0000-0000-0000-000000000a1b")
Q_BALL = UUID("00000000-0000-0000-0000-000000000a1c")
Q_JERSEY = UUID("00000000-0000-0000-0000-000000000a1d")
Q_LINKED_MH = UUID("00000000-0000-0000-0000-000000000a1e")
Q_ABOUT_SPORTS = UUID("00000000-0000-0000-0000-000000000a1f")

COUNTRY_QS = frozenset(
    {Q_INDIA, Q_OTHER_COUNTRY, Q_JAPAN, Q_AUSTRALIA, Q_EUROPE, Q_AMERICAS, Q_USA}
)

CHARS = [KOHLI, MESSI, SRK, NARUTO, BATMAN, EINSTEIN]
QUESTIONS = [
    Q_REAL,
    Q_MADE_UP,
    Q_MALE,
    Q_ALIVE,
    Q_FAMOUS,
    Q_HUMAN,
    Q_INDIA,
    Q_OTHER_COUNTRY,
    Q_JAPAN,
    Q_AUSTRALIA,
    Q_EUROPE,
    Q_AMERICAS,
    Q_USA,
    Q_SPORTS,
    Q_MOVIES,
    Q_ANIME,
    Q_CRICKET,
    Q_FOOTBALL,
    Q_CHEF,
    Q_BABY,
    Q_TODDLER,
    Q_TEEN,
    Q_GUILD,
    Q_NINJA,
    Q_SUPERHERO,
    Q_ICE,
    Q_ALONE,
    Q_BALL,
    Q_JERSEY,
    Q_LINKED_MH,
    Q_ABOUT_SPORTS,
]

REFS = {
    Q_REAL: QuestionRef(id=Q_REAL, text="Is this a real person?", category="Personality"),
    Q_MADE_UP: QuestionRef(
        id=Q_MADE_UP, text="Is this a made-up character?", category="Fictional traits"
    ),
    Q_MALE: QuestionRef(id=Q_MALE, text="Are they male?", category="Gender"),
    Q_ALIVE: QuestionRef(id=Q_ALIVE, text="Is this person still alive?", category="Age"),
    Q_FAMOUS: QuestionRef(
        id=Q_FAMOUS, text="Are they famous worldwide?", category="Personality"
    ),
    Q_HUMAN: QuestionRef(id=Q_HUMAN, text="Are they human?", category="Personality"),
    Q_INDIA: QuestionRef(id=Q_INDIA, text="Are they from India?", category="Nationality"),
    Q_OTHER_COUNTRY: QuestionRef(
        id=Q_OTHER_COUNTRY, text="Are they from another country?", category="Nationality"
    ),
    Q_JAPAN: QuestionRef(id=Q_JAPAN, text="Are they from Japan?", category="Nationality"),
    Q_AUSTRALIA: QuestionRef(
        id=Q_AUSTRALIA, text="Are they from Australia?", category="Nationality"
    ),
    Q_EUROPE: QuestionRef(id=Q_EUROPE, text="Are they from Europe?", category="Nationality"),
    Q_AMERICAS: QuestionRef(
        id=Q_AMERICAS, text="Are they from the Americas?", category="Nationality"
    ),
    Q_USA: QuestionRef(
        id=Q_USA, text="Are they from the United States?", category="Nationality"
    ),
    Q_SPORTS: QuestionRef(id=Q_SPORTS, text="Is this a sports player?", category="Sports"),
    Q_MOVIES: QuestionRef(id=Q_MOVIES, text="Is this from a movie?", category="Movies"),
    Q_ANIME: QuestionRef(id=Q_ANIME, text="Is this from anime?", category="Anime"),
    Q_CRICKET: QuestionRef(
        id=Q_CRICKET, text="Are they famous for cricket?", category="Sports"
    ),
    Q_FOOTBALL: QuestionRef(
        id=Q_FOOTBALL, text="Are they famous for football?", category="Sports"
    ),
    Q_CHEF: QuestionRef(id=Q_CHEF, text="Are they a chef?", category="Profession"),
    Q_BABY: QuestionRef(id=Q_BABY, text="Are they a baby or toddler?", category="Age"),
    Q_TODDLER: QuestionRef(id=Q_TODDLER, text="Are they a toddler?", category="Age"),
    Q_TEEN: QuestionRef(id=Q_TEEN, text="Are they a teenager?", category="Age"),
    Q_GUILD: QuestionRef(
        id=Q_GUILD, text="Are they in a made-up guild?", category="Anime"
    ),
    Q_NINJA: QuestionRef(id=Q_NINJA, text="Are they a ninja or samurai?", category="Anime"),
    Q_SUPERHERO: QuestionRef(
        id=Q_SUPERHERO, text="Are they a superhero?", category="Movies"
    ),
    Q_ICE: QuestionRef(id=Q_ICE, text="Do they have ice powers?", category="Anime"),
    Q_ALONE: QuestionRef(
        id=Q_ALONE, text="Do they play alone sports?", category="Sports"
    ),
    Q_BALL: QuestionRef(
        id=Q_BALL, text="Do they play with a ball?", category="Sports"
    ),
    Q_JERSEY: QuestionRef(
        id=Q_JERSEY, text="Do they wear a sports jersey?", category="Sports"
    ),
    Q_LINKED_MH: QuestionRef(
        id=Q_LINKED_MH, text="Are they linked to Maharashtra?", category="Politics"
    ),
    Q_ABOUT_SPORTS: QuestionRef(
        id=Q_ABOUT_SPORTS, text="Is this about sports games?", category="Sports"
    ),
}

CATEGORIES = {
    KOHLI: "Sports",
    MESSI: "Sports",
    SRK: "Movies",
    NARUTO: "Anime",
    BATMAN: "Movies",
    EINSTEIN: "Scientists",
}

PROFILE = {
    KOHLI: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_HUMAN: 0.95,
        Q_INDIA: 0.95,
        Q_OTHER_COUNTRY: 0.1,
        Q_SPORTS: 0.97,
        Q_MOVIES: 0.1,
        Q_ANIME: 0.02,
        Q_CRICKET: 0.96,
        Q_FOOTBALL: 0.15,
        Q_CHEF: 0.05,
        Q_BABY: 0.02,
        Q_TODDLER: 0.02,
        Q_TEEN: 0.05,
        Q_GUILD: 0.02,
        Q_NINJA: 0.02,
        Q_SUPERHERO: 0.05,
        Q_ICE: 0.02,
    },
    MESSI: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_HUMAN: 0.95,
        Q_INDIA: 0.05,
        Q_OTHER_COUNTRY: 0.9,
        Q_SPORTS: 0.97,
        Q_MOVIES: 0.1,
        Q_ANIME: 0.02,
        Q_CRICKET: 0.1,
        Q_FOOTBALL: 0.96,
        Q_CHEF: 0.05,
        Q_BABY: 0.02,
        Q_TODDLER: 0.02,
        Q_TEEN: 0.05,
        Q_GUILD: 0.02,
        Q_NINJA: 0.02,
        Q_SUPERHERO: 0.05,
        Q_ICE: 0.02,
    },
    SRK: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_HUMAN: 0.95,
        Q_INDIA: 0.95,
        Q_OTHER_COUNTRY: 0.1,
        Q_SPORTS: 0.05,
        Q_MOVIES: 0.96,
        Q_ANIME: 0.02,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_CHEF: 0.05,
        Q_BABY: 0.02,
        Q_TODDLER: 0.02,
        Q_TEEN: 0.05,
        Q_GUILD: 0.02,
        Q_NINJA: 0.02,
        Q_SUPERHERO: 0.1,
        Q_ICE: 0.02,
    },
    NARUTO: {
        Q_REAL: 0.05,
        Q_MADE_UP: 0.95,
        Q_MALE: 0.95,
        Q_ALIVE: 0.55,
        Q_FAMOUS: 0.9,
        Q_HUMAN: 0.9,
        Q_INDIA: 0.05,
        Q_OTHER_COUNTRY: 0.2,
        Q_SPORTS: 0.05,
        Q_MOVIES: 0.2,
        Q_ANIME: 0.97,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_CHEF: 0.05,
        Q_BABY: 0.05,
        Q_TODDLER: 0.05,
        Q_TEEN: 0.55,
        Q_GUILD: 0.4,
        Q_NINJA: 0.95,
        Q_SUPERHERO: 0.2,
        Q_ICE: 0.3,
    },
    BATMAN: {
        Q_REAL: 0.1,
        Q_MADE_UP: 0.9,
        Q_MALE: 0.95,
        Q_ALIVE: 0.55,
        Q_FAMOUS: 0.95,
        Q_HUMAN: 0.95,
        Q_INDIA: 0.05,
        Q_OTHER_COUNTRY: 0.4,
        Q_SPORTS: 0.1,
        Q_MOVIES: 0.96,
        Q_ANIME: 0.05,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_CHEF: 0.05,
        Q_BABY: 0.02,
        Q_TODDLER: 0.02,
        Q_TEEN: 0.05,
        Q_GUILD: 0.05,
        Q_NINJA: 0.05,
        Q_SUPERHERO: 0.95,
        Q_ICE: 0.05,
    },
    EINSTEIN: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.05,
        Q_FAMOUS: 0.95,
        Q_HUMAN: 0.95,
        Q_INDIA: 0.1,
        Q_OTHER_COUNTRY: 0.85,
        Q_SPORTS: 0.05,
        Q_MOVIES: 0.1,
        Q_ANIME: 0.02,
        Q_CRICKET: 0.05,
        Q_FOOTBALL: 0.05,
        Q_CHEF: 0.05,
        Q_BABY: 0.02,
        Q_TODDLER: 0.02,
        Q_TEEN: 0.05,
        Q_GUILD: 0.02,
        Q_NINJA: 0.02,
        Q_SUPERHERO: 0.05,
        Q_ICE: 0.02,
    },
}


def _likelihoods():
    country_defaults = {
        Q_JAPAN: 0.05,
        Q_AUSTRALIA: 0.05,
        Q_EUROPE: 0.1,
        Q_AMERICAS: 0.1,
        Q_USA: 0.1,
        Q_ALONE: 0.45,
        Q_BALL: 0.55,
        Q_JERSEY: 0.5,
        Q_LINKED_MH: 0.12,
        Q_ABOUT_SPORTS: 0.4,
    }
    country_overrides = {
        NARUTO: {Q_JAPAN: 0.92, Q_OTHER_COUNTRY: 0.2},
        MESSI: {Q_AMERICAS: 0.9, Q_OTHER_COUNTRY: 0.9},
        EINSTEIN: {Q_EUROPE: 0.9, Q_OTHER_COUNTRY: 0.85},
        BATMAN: {Q_USA: 0.85, Q_AMERICAS: 0.85},
    }
    out: dict[tuple[UUID, UUID], LikelihoodEntry] = {}
    for cid, answers in PROFILE.items():
        merged = {**country_defaults, **answers, **country_overrides.get(cid, {})}
        for qid, v in merged.items():
            out[(cid, qid)] = LikelihoodEntry(v, 50)
    return out


def _play(true_id: UUID, *, max_questions: int = 10, seed: int = 7) -> list[UUID]:
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


def test_made_up_guild_is_not_stage_1_identity():
    """Bare 'made-up' must not promote guild questions into Phase 1."""
    assert question_hierarchy_stage(REFS[Q_GUILD]) == "4"
    assert is_hard_gated_niche(REFS[Q_GUILD]) is True
    assert is_question_allowed_for_stage(REFS[Q_GUILD], stage="1", dominant_category=None) is False
    assert is_question_allowed_for_stage(REFS[Q_MADE_UP], stage="1", dominant_category=None) is True


def test_early_questions_are_broad():
    state = create_initial_state(CHARS, _likelihoods())
    # First question at a uniform start must be Phase-1 identity.
    qid = select_next_question(
        state,
        QUESTIONS,
        min_samples=1,
        question_refs=REFS,
        character_categories=CATEGORIES,
        explore=False,
    )
    assert qid is not None
    assert question_hierarchy_stage(REFS[qid]) == "1"
    assert qid not in {Q_GUILD, Q_CHEF, Q_BABY, Q_CRICKET, Q_ANIME, Q_ICE, Q_SPORTS}
    # After a few vague answers, still no niche topics.
    for _ in range(3):
        qid = select_next_question(
            state,
            QUESTIONS,
            min_samples=1,
            question_refs=REFS,
            character_categories=CATEGORIES,
            explore=False,
        )
        assert qid is not None
        assert qid not in {Q_GUILD, Q_CHEF, Q_BABY, Q_CRICKET, Q_ICE, Q_NINJA}
        state, _ = process_answer(state, qid, "dont_know")


def test_opening_classifiers_match_akinator_identity():
    assert is_reality_question(REFS[Q_REAL]) is True
    assert is_reality_question(REFS[Q_MADE_UP]) is True
    assert is_reality_question(REFS[Q_GUILD]) is False
    assert is_gender_question(REFS[Q_MALE]) is True
    assert is_gender_question(REFS[Q_HUMAN]) is False
    assert is_akinator_filler_question(REFS[Q_ALONE]) is True
    assert is_akinator_filler_question(REFS[Q_BALL]) is True
    assert is_akinator_filler_question(REFS[Q_JERSEY]) is True
    assert is_akinator_filler_question(REFS[Q_ABOUT_SPORTS]) is True
    assert is_akinator_filler_question(REFS[Q_SPORTS]) is False
    assert is_regional_state_question(REFS[Q_LINKED_MH]) is True
    assert is_regional_state_question(REFS[Q_INDIA]) is False
    punjabi = QuestionRef(
        id=uuid4(), text="Is your character from Punjabi movies?", category="Movies"
    )
    assert is_regional_state_question(punjabi) is False


def test_opening_flow_real_gender_alive_then_country():
    """Akinator path: real → gender → alive → country (not filler or cricket)."""
    asked = _play(KOHLI, max_questions=5, seed=11)
    assert asked[0] == Q_REAL
    assert asked[1] == Q_MALE
    assert asked[2] == Q_ALIVE
    assert asked[3] in COUNTRY_QS
    assert asked[3] == Q_INDIA
    assert asked[4] == Q_SPORTS
    assert Q_CRICKET not in asked[:5]
    assert Q_CHEF not in asked[:5]
    assert Q_ALONE not in asked[:5]
    assert Q_BALL not in asked[:5]
    assert len([q for q in asked if q in COUNTRY_QS]) == 1


def test_never_asks_second_country_after_india_yes():
    """Regression: India yes must not be followed by Japan/Australia/Europe spam."""
    rng = random.Random(3)
    likelihoods = _likelihoods()
    state = create_initial_state(CHARS, likelihoods)
    asked: list[UUID] = []
    for _ in range(10):
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
        if qid in {Q_REAL, Q_MALE, Q_ALIVE, Q_INDIA}:
            answer = "yes"
        elif qid in COUNTRY_QS:
            answer = "no"
        else:
            answer = oracle_answer(likelihoods, KOHLI, qid, rng, noise=0.0)
        state, _ = process_answer(state, qid, answer)
        asked.append(qid)

    country_asked = [q for q in asked if q in COUNTRY_QS]
    assert country_asked, "expected one country question"
    assert country_asked[0] == Q_INDIA
    assert country_asked == [Q_INDIA], [REFS[q].text for q in country_asked]
    assert Q_JAPAN not in asked
    assert Q_AUSTRALIA not in asked
    assert Q_EUROPE not in asked
    assert Q_AMERICAS not in asked
    assert Q_USA not in asked
    assert Q_OTHER_COUNTRY not in asked
    # After India, flow should move to domain — not more geography.
    assert any(q in {Q_SPORTS, Q_MOVIES, Q_ANIME} for q in asked)


def test_india_no_allows_followup_country_question():
    """Akinator-like tree: India=NO should allow another place question."""
    rng = random.Random(5)
    likelihoods = _likelihoods()
    state = create_initial_state(CHARS, likelihoods)
    asked: list[UUID] = []
    for _ in range(6):
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
        if qid in {Q_REAL, Q_MALE, Q_ALIVE}:
            answer = "yes"
        elif qid == Q_INDIA:
            answer = "no"
        elif qid in COUNTRY_QS:
            answer = "yes"
        else:
            answer = "dont_know"
        state, _ = process_answer(state, qid, answer)
        asked.append(qid)

    country_asked = [q for q in asked if q in COUNTRY_QS]
    assert Q_INDIA in country_asked
    assert len(country_asked) >= 2, [REFS[q].text for q in country_asked]


def test_baby_toddler_teen_cannot_appear_early():
    asked = _play(KOHLI, max_questions=6)
    assert not set(asked) & {Q_BABY, Q_TODDLER, Q_TEEN}


def test_profession_cannot_appear_before_category_detection():
    asked = _play(KOHLI, max_questions=5)
    assert Q_CHEF not in asked


def test_anime_cannot_appear_on_real_person_path():
    asked = _play(KOHLI, max_questions=8)
    # Real sports path should not pivot into anime / guild / ninja.
    assert Q_ANIME not in asked or asked.index(Q_SPORTS) < asked.index(Q_ANIME)
    assert Q_GUILD not in asked
    assert Q_NINJA not in asked
    assert Q_ICE not in asked


def test_sports_specific_cannot_appear_before_sports_detection():
    asked = _play(KOHLI, max_questions=10)
    if Q_CRICKET in asked:
        assert Q_SPORTS in asked
        assert asked.index(Q_SPORTS) < asked.index(Q_CRICKET)


def test_fictional_universe_gated_before_fictional_category():
    state = create_initial_state(CHARS, _likelihoods())
    # Before any answers, guild / ice powers must be rejected.
    qid = select_next_question(
        state,
        QUESTIONS,
        min_samples=1,
        question_refs=REFS,
        character_categories=CATEGORIES,
        explore=False,
    )
    assert qid not in {Q_GUILD, Q_ICE, Q_NINJA}


def test_made_up_guild_cannot_appear_in_early_gameplay():
    for true_id in (KOHLI, MESSI, NARUTO, BATMAN):
        asked = _play(true_id, max_questions=5)
        assert Q_GUILD not in asked


def test_questions_not_repeated_in_session():
    asked = _play(MESSI, max_questions=12)
    assert len(asked) == len(set(asked))


def test_virat_kohli_natural_sports_cricket_path():
    asked = _play(KOHLI, max_questions=10)
    texts = [REFS[q].text for q in asked]
    assert any("real person" in t or "male" in t or "alive" in t or "famous" in t for t in texts[:4])
    assert Q_SPORTS in asked
    if Q_CRICKET in asked:
        assert asked.index(Q_SPORTS) < asked.index(Q_CRICKET)
    assert Q_GUILD not in asked
    assert Q_ANIME not in asked or asked.index(Q_SPORTS) < asked.index(Q_ANIME)


def test_messi_natural_sports_football_path():
    asked = _play(MESSI, max_questions=10)
    assert Q_SPORTS in asked
    if Q_FOOTBALL in asked:
        assert asked.index(Q_SPORTS) < asked.index(Q_FOOTBALL)
    assert Q_GUILD not in asked
    assert Q_NINJA not in asked


def test_naruto_anime_path_after_fictional_detection():
    asked = _play(NARUTO, max_questions=10)
    assert Q_MADE_UP in asked or Q_REAL in asked
    assert Q_ANIME in asked
    # Anime-specific niche only after anime category question (or late).
    if Q_NINJA in asked:
        assert asked.index(Q_ANIME) < asked.index(Q_NINJA)
    if Q_GUILD in asked:
        assert asked.index(Q_ANIME) < asked.index(Q_GUILD)
    # Early block of guild
    assert Q_GUILD not in asked[:4]


def test_batman_superhero_path_after_fictional_detection():
    asked = _play(BATMAN, max_questions=10)
    assert Q_MADE_UP in asked or Q_REAL in asked
    assert Q_MOVIES in asked or Q_SUPERHERO in asked
    assert Q_GUILD not in asked
    assert Q_NINJA not in asked
    # Superhero is domain-specific — not an opening identity question.
    if Q_SUPERHERO in asked:
        assert asked.index(Q_SUPERHERO) >= 2


def test_filler_questions_stay_out_of_opening():
    asked = _play(KOHLI, max_questions=8, seed=11)
    filler = {Q_ALONE, Q_BALL, Q_JERSEY, Q_LINKED_MH, Q_ABOUT_SPORTS}
    assert not filler.intersection(asked)


def test_hard_gate_helpers_cover_forbidden_topics():
    for text in (
        "Are they a chef?",
        "Are they a baby?",
        "Are they in a made-up guild?",
        "Do they have ice powers?",
        "Are they a teenager?",
    ):
        ref = QuestionRef(id=uuid4(), text=text, category="Anime")
        assert is_hard_gated_niche(ref)
        assert question_hierarchy_stage(ref) == "4"
