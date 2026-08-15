"""Question selection must obey hierarchy and logic, not information gain alone."""

from __future__ import annotations

from uuid import uuid4

from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.question_consistency import (
    classify_question,
    infer_established_facts,
    is_logically_valid_question,
)
from app.engine.selector import create_initial_state, process_answer, select_next_question

KOHLI = uuid4()
SANIA = uuid4()
MESSI = uuid4()
NARUTO = uuid4()
BATMAN = uuid4()
DOG = uuid4()

Q_HUMAN = uuid4()
Q_ANIMAL = uuid4()
Q_HUMAN_ALT = uuid4()
Q_REAL = uuid4()
Q_MADE_UP = uuid4()
Q_ALIVE = uuid4()
Q_MALE = uuid4()
Q_FAMOUS = uuid4()
Q_INDIA = uuid4()
Q_INDIA_ALT = uuid4()
Q_JAPAN = uuid4()
Q_SPORTS = uuid4()
Q_CRICKET = uuid4()
Q_FENCING = uuid4()
Q_BATTER = uuid4()
Q_SCIENTIST = uuid4()
Q_ANIME = uuid4()
Q_MVP = uuid4()


def _L(value: float, n: int = 50) -> LikelihoodEntry:
    return LikelihoodEntry(value, n)


def _ref(qid, text, category) -> QuestionRef:
    return QuestionRef(id=qid, text=text, category=category)


REFS = {
    Q_HUMAN: _ref(Q_HUMAN, "Is your character human?", "Personality"),
    Q_ANIMAL: _ref(Q_ANIMAL, "Is your character an animal?", "Personality"),
    Q_HUMAN_ALT: _ref(Q_HUMAN_ALT, "Is this a human?", "Personality"),
    Q_REAL: _ref(Q_REAL, "Is this a real person?", "Personality"),
    Q_MADE_UP: _ref(Q_MADE_UP, "Is this a made-up character?", "Fictional traits"),
    Q_ALIVE: _ref(Q_ALIVE, "Is this person still alive?", "Age"),
    Q_MALE: _ref(Q_MALE, "Are they male?", "Gender"),
    Q_FAMOUS: _ref(Q_FAMOUS, "Are they famous worldwide?", "Personality"),
    Q_INDIA: _ref(Q_INDIA, "Are they from India?", "Nationality"),
    Q_INDIA_ALT: _ref(Q_INDIA_ALT, "Is this person Indian?", "Nationality"),
    Q_JAPAN: _ref(Q_JAPAN, "Are they from Japan?", "Nationality"),
    Q_SPORTS: _ref(Q_SPORTS, "Is this a sports player?", "Sports"),
    Q_CRICKET: _ref(Q_CRICKET, "Are they famous for cricket?", "Sports"),
    Q_FENCING: _ref(Q_FENCING, "Are they famous for fencing?", "Sports"),
    Q_BATTER: _ref(Q_BATTER, "Are they primarily known as a batter?", "Sports"),
    Q_SCIENTIST: _ref(Q_SCIENTIST, "Is this a scientist?", "Science"),
    Q_ANIME: _ref(Q_ANIME, "Is this from anime?", "Anime"),
    Q_MVP: _ref(Q_MVP, "Did they win MVP?", "Awards"),
}


def _mark_asked(state, qid, answer: str) -> None:
    state.used_question_ids.add(qid)
    if qid not in state.asked_question_order:
        state.asked_question_order.append(qid)
    state.answer_log[qid] = answer
    state.questions_asked = len(state.asked_question_order)


def _pick(state, questions, categories):
    return select_next_question(
        state,
        questions,
        min_samples=1,
        question_refs=REFS,
        character_categories=categories,
        explore=False,
    )


def test_classify_human_and_animal_are_exclusive_entity_types():
    human = classify_question(REFS[Q_HUMAN])
    animal = classify_question(REFS[Q_ANIMAL])
    assert human.semantic_key == "entity_human"
    assert animal.semantic_key == "entity_animal"
    assert human.family == animal.family == "entity"
    assert human.polarity != animal.polarity


def test_classify_india_wordings_are_semantic_duplicates():
    assert classify_question(REFS[Q_INDIA]).semantic_key == "origin_india"
    assert classify_question(REFS[Q_INDIA_ALT]).semantic_key == "origin_india"


def test_cricket_role_questions_are_not_semantic_duplicates():
    cricket = classify_question(REFS[Q_CRICKET])
    batter = classify_question(REFS[Q_BATTER])
    wicket = classify_question(
        QuestionRef(
            id=uuid4(),
            text="Does your character keep wickets in cricket?",
            category="Sports",
        )
    )
    debut = classify_question(
        QuestionRef(
            id=uuid4(),
            text="Did your character debut in cricket before 2000?",
            category="Sports",
        )
    )
    assert cricket.semantic_key != batter.semantic_key
    assert wicket.semantic_key != batter.semantic_key
    assert debut.semantic_key not in {cricket.semantic_key, batter.semantic_key, wicket.semantic_key}


def test_human_candidate_pool_cannot_receive_animal_question():
    """Sports-only pool must never ask the competing entity-type question."""
    chars = [KOHLI, SANIA]
    categories = {KOHLI: "Sports", SANIA: "Sports"}
    questions = [Q_ALIVE, Q_HUMAN, Q_ANIMAL, Q_FAMOUS, Q_SPORTS]
    likelihoods = {}
    for cid in chars:
        likelihoods[(cid, Q_ALIVE)] = _L(0.9)
        likelihoods[(cid, Q_HUMAN)] = _L(0.95)
        likelihoods[(cid, Q_FAMOUS)] = _L(0.7)
        likelihoods[(cid, Q_SPORTS)] = _L(0.97)
    # Miscalibrated animal likelihoods — high IG must not override logic.
    likelihoods[(KOHLI, Q_ANIMAL)] = _L(0.95)
    likelihoods[(SANIA, Q_ANIMAL)] = _L(0.05)

    state = create_initial_state(chars, likelihoods)
    asked = []
    for _ in range(6):
        qid = _pick(state, questions, categories)
        if qid is None:
            break
        asked.append(qid)
        assert qid != Q_ANIMAL
        answer = "yes" if qid in {Q_ALIVE, Q_HUMAN, Q_FAMOUS, Q_SPORTS} else "no"
        state, _ = process_answer(state, qid, answer)
    assert Q_ANIMAL not in asked


def test_animal_candidate_pool_cannot_receive_human_question():
    chars = [DOG]
    categories = {DOG: "Animals"}
    questions = [Q_ALIVE, Q_HUMAN, Q_ANIMAL, Q_FAMOUS]
    likelihoods = {
        (DOG, Q_ALIVE): _L(0.9),
        (DOG, Q_ANIMAL): _L(0.97),
        (DOG, Q_FAMOUS): _L(0.4),
        # High IG trap: human would look useful if it were allowed.
        (DOG, Q_HUMAN): _L(0.05),
    }
    state = create_initial_state(chars, likelihoods)
    asked = []
    for _ in range(4):
        qid = _pick(state, questions, categories)
        if qid is None:
            break
        asked.append(qid)
        assert qid != Q_HUMAN
        answer = "yes" if qid in {Q_ALIVE, Q_ANIMAL} else "no"
        state, _ = process_answer(state, qid, answer)
    assert Q_HUMAN not in asked


def test_fictional_candidates_skip_irrelevant_real_person_questions():
    chars = [NARUTO, BATMAN]
    categories = {NARUTO: "Anime", BATMAN: "Anime"}
    questions = [Q_MADE_UP, Q_SCIENTIST, Q_ANIME, Q_FAMOUS]
    likelihoods = {}
    for cid in chars:
        likelihoods[(cid, Q_MADE_UP)] = _L(0.95)
        likelihoods[(cid, Q_ANIME)] = _L(0.7)
        likelihoods[(cid, Q_FAMOUS)] = _L(0.8)
    likelihoods[(NARUTO, Q_SCIENTIST)] = _L(0.95)
    likelihoods[(BATMAN, Q_SCIENTIST)] = _L(0.05)

    state = create_initial_state(chars, likelihoods)
    _mark_asked(state, Q_MADE_UP, "yes")
    asked = []
    for _ in range(4):
        qid = _pick(state, questions, categories)
        if qid is None:
            break
        asked.append(qid)
        assert qid != Q_SCIENTIST
        state, _ = process_answer(state, qid, "yes")
    assert Q_SCIENTIST not in asked


def test_indian_candidate_pool_prefers_india_relevant_questions():
    chars = [KOHLI, SANIA, MESSI]
    categories = {KOHLI: "Sports", SANIA: "Sports", MESSI: "Sports"}
    questions = [Q_ALIVE, Q_INDIA, Q_JAPAN, Q_SPORTS]
    likelihoods = {}
    for cid in chars:
        likelihoods[(cid, Q_ALIVE)] = _L(0.9)
        likelihoods[(cid, Q_SPORTS)] = _L(0.97)
    likelihoods[(KOHLI, Q_INDIA)] = _L(0.96)
    likelihoods[(SANIA, Q_INDIA)] = _L(0.96)
    likelihoods[(MESSI, Q_INDIA)] = _L(0.08)
    likelihoods[(KOHLI, Q_JAPAN)] = _L(0.05)
    likelihoods[(SANIA, Q_JAPAN)] = _L(0.05)
    likelihoods[(MESSI, Q_JAPAN)] = _L(0.08)

    state = create_initial_state(chars, likelihoods)
    _mark_asked(state, Q_ALIVE, "yes")
    qid = _pick(state, questions, categories)
    assert qid == Q_INDIA


def test_sports_category_before_specific_sport_traits():
    chars = [KOHLI, MESSI]
    categories = {KOHLI: "Sports", MESSI: "Sports"}
    questions = [Q_ALIVE, Q_INDIA, Q_SPORTS, Q_CRICKET, Q_BATTER, Q_MVP]
    likelihoods = {}
    for cid in chars:
        likelihoods[(cid, Q_ALIVE)] = _L(0.9)
        likelihoods[(cid, Q_SPORTS)] = _L(0.97)
        likelihoods[(cid, Q_MVP)] = _L(0.4)
    likelihoods[(KOHLI, Q_INDIA)] = _L(0.96)
    likelihoods[(MESSI, Q_INDIA)] = _L(0.08)
    likelihoods[(KOHLI, Q_CRICKET)] = _L(0.96)
    likelihoods[(MESSI, Q_CRICKET)] = _L(0.1)
    likelihoods[(KOHLI, Q_BATTER)] = _L(0.9)
    likelihoods[(MESSI, Q_BATTER)] = _L(0.1)

    state = create_initial_state(chars, likelihoods)
    _mark_asked(state, Q_ALIVE, "yes")
    _mark_asked(state, Q_INDIA, "yes")
    qid = _pick(state, questions, categories)
    assert qid == Q_SPORTS
    assert qid not in {Q_CRICKET, Q_BATTER, Q_MVP}


def test_cricket_questions_do_not_appear_before_cricket_is_established():
    chars = [KOHLI, MESSI]
    categories = {KOHLI: "Sports", MESSI: "Sports"}
    questions = [Q_ALIVE, Q_INDIA, Q_SPORTS, Q_CRICKET, Q_BATTER, Q_FENCING]
    likelihoods = {}
    for cid in chars:
        likelihoods[(cid, Q_ALIVE)] = _L(0.9)
        likelihoods[(cid, Q_SPORTS)] = _L(0.97)
        likelihoods[(cid, Q_FENCING)] = _L(0.08)
    likelihoods[(KOHLI, Q_INDIA)] = _L(0.96)
    likelihoods[(MESSI, Q_INDIA)] = _L(0.08)
    likelihoods[(KOHLI, Q_CRICKET)] = _L(0.96)
    likelihoods[(MESSI, Q_CRICKET)] = _L(0.1)
    likelihoods[(KOHLI, Q_BATTER)] = _L(0.9)
    likelihoods[(MESSI, Q_BATTER)] = _L(0.1)

    state = create_initial_state(chars, likelihoods)
    _mark_asked(state, Q_ALIVE, "yes")
    _mark_asked(state, Q_INDIA, "yes")
    first = _pick(state, questions, categories)
    assert first == Q_SPORTS
    assert first not in {Q_CRICKET, Q_BATTER, Q_FENCING}

    state, _ = process_answer(state, Q_SPORTS, "yes")
    # Cricket may now appear; batter still requires cricket to be established.
    next_q = _pick(state, questions, categories)
    assert next_q != Q_BATTER
    assert next_q != Q_FENCING
    if next_q == Q_CRICKET:
        state, _ = process_answer(state, Q_CRICKET, "yes")
        after = _pick(state, questions, categories)
        assert after != Q_FENCING


def test_already_answered_questions_are_never_repeated():
    chars = [KOHLI, MESSI]
    categories = {KOHLI: "Sports", MESSI: "Sports"}
    questions = [Q_ALIVE, Q_HUMAN, Q_FAMOUS]
    likelihoods = {}
    for cid in chars:
        likelihoods[(cid, Q_ALIVE)] = _L(0.9)
        likelihoods[(cid, Q_HUMAN)] = _L(0.95)
        likelihoods[(cid, Q_FAMOUS)] = _L(0.7)

    state = create_initial_state(chars, likelihoods)
    state, _ = process_answer(state, Q_ALIVE, "yes")
    asked = [Q_ALIVE]
    for _ in range(4):
        qid = _pick(state, questions, categories)
        if qid is None:
            break
        assert qid not in asked
        asked.append(qid)
        state, _ = process_answer(state, qid, "yes")


def test_semantically_duplicate_questions_are_filtered():
    chars = [KOHLI, SANIA]
    categories = {KOHLI: "Sports", SANIA: "Sports"}
    questions = [Q_INDIA, Q_INDIA_ALT, Q_FAMOUS]
    likelihoods = {}
    for cid in chars:
        likelihoods[(cid, Q_INDIA)] = _L(0.96)
        likelihoods[(cid, Q_INDIA_ALT)] = _L(0.96)
        likelihoods[(cid, Q_FAMOUS)] = _L(0.7)

    state = create_initial_state(chars, likelihoods)
    _mark_asked(state, Q_ALIVE, "yes")
    _mark_asked(state, Q_INDIA, "yes")
    # Alive is marked but not in `questions`; India is answered.
    qid = _pick(state, questions, categories)
    assert qid != Q_INDIA
    assert qid != Q_INDIA_ALT
    # Famous does not split Kohli vs Sania here — stop rather than ask trivia.
    assert qid in {Q_FAMOUS, None}


def test_contradictory_questions_are_filtered_even_with_high_information_gain():
    chars = [KOHLI, MESSI]
    categories = {KOHLI: "Sports", MESSI: "Movies"}
    questions = [Q_HUMAN, Q_ANIMAL, Q_FAMOUS]
    likelihoods = {
        (KOHLI, Q_HUMAN): _L(0.95),
        (MESSI, Q_HUMAN): _L(0.95),
        (KOHLI, Q_FAMOUS): _L(0.8),
        (MESSI, Q_FAMOUS): _L(0.8),
        # High-IG contradiction trap.
        (KOHLI, Q_ANIMAL): _L(0.95),
        (MESSI, Q_ANIMAL): _L(0.05),
    }
    state = create_initial_state(chars, likelihoods)
    _mark_asked(state, Q_HUMAN, "yes")
    qid = _pick(state, questions, categories)
    assert qid != Q_ANIMAL
    # Famous is statistically flat on this pair; None means guess, not wander.
    assert qid in {Q_FAMOUS, None}


def test_selector_still_chooses_high_value_question_among_valid_ones():
    chars = [KOHLI, MESSI]
    categories = {KOHLI: "Sports", MESSI: "Sports"}
    questions = [Q_MALE, Q_FAMOUS]
    likelihoods = {
        (KOHLI, Q_MALE): _L(0.95),
        (MESSI, Q_MALE): _L(0.05),
        (KOHLI, Q_FAMOUS): _L(0.8),
        (MESSI, Q_FAMOUS): _L(0.8),
    }
    state = create_initial_state(chars, likelihoods)
    _mark_asked(state, Q_ALIVE, "yes")
    qid = _pick(state, questions, categories)
    assert qid == Q_MALE


def test_human_yes_marks_animal_invalid_from_facts_not_probability():
    state = create_initial_state([KOHLI], {(KOHLI, Q_HUMAN): _L(0.9), (KOHLI, Q_ANIMAL): _L(0.9)})
    _mark_asked(state, Q_HUMAN, "yes")
    facts = infer_established_facts(state, REFS, remaining_categories=frozenset({"Sports", "Movies"}))
    assert facts.values.get("entity") == "human"
    assert is_logically_valid_question(REFS[Q_ANIMAL], facts) is False
    assert is_logically_valid_question(REFS[Q_HUMAN_ALT], facts) is False


def test_emergency_fallback_does_not_pick_contradictory_animal():
    """Even the last-resort pool must not return a logically invalid question."""
    chars = [KOHLI]
    categories = {KOHLI: "Sports"}
    questions = [Q_ANIMAL]
    likelihoods = {(KOHLI, Q_ANIMAL): _L(0.5)}
    state = create_initial_state(chars, likelihoods)
    _mark_asked(state, Q_HUMAN, "yes")
    qid = _pick(state, questions, categories)
    assert qid is None
