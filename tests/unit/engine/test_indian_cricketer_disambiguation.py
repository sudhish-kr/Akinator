"""Indian cricket peers must be split by role questions, not fame.

A live Dhoni game that only asked athlete / individual-sport / alive / India /
man was able to guess Dhoni because the selector delayed cricket and the
catalog treated every Indian cricketer as the same L-vector.
"""

from __future__ import annotations

from uuid import UUID, uuid4

from app.engine.confidence import evaluate_confidence
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    process_answer,
    select_next_question,
    should_delay_guess_for_sport_split,
)

DHONI = uuid4()
KOHLI = uuid4()
ROHIT = uuid4()
SACHIN = uuid4()
SMRITI = uuid4()
MESSI = uuid4()
SANIA = uuid4()
SRK = uuid4()

Q_REAL = uuid4()
Q_ALIVE = uuid4()
Q_MAN = uuid4()
Q_INDIA = uuid4()
Q_ATHLETE = uuid4()
Q_ALONE = uuid4()
Q_CRICKET = uuid4()
Q_FOOTBALL = uuid4()
Q_TENNIS = uuid4()
Q_WICKET = uuid4()
Q_OPENER = uuid4()
Q_DEBUT = uuid4()
Q_ACTOR = uuid4()
Q_FAMOUS = uuid4()

CHARS = [DHONI, KOHLI, ROHIT, SACHIN, SMRITI, MESSI, SANIA, SRK]
NAMES = {
    DHONI: "MS Dhoni",
    KOHLI: "Virat Kohli",
    ROHIT: "Rohit Sharma",
    SACHIN: "Sachin Tendulkar",
    SMRITI: "Smriti Mandhana",
    MESSI: "Lionel Messi",
    SANIA: "Sania Mirza",
    SRK: "Shah Rukh Khan",
}
CATEGORIES = {
    DHONI: "Sports",
    KOHLI: "Sports",
    ROHIT: "Sports",
    SACHIN: "Sports",
    SMRITI: "Sports",
    MESSI: "Sports",
    SANIA: "Sports",
    SRK: "Movies",
}
REFS = {
    Q_REAL: QuestionRef(id=Q_REAL, text="Is your character a real person?", category="Personality"),
    Q_ALIVE: QuestionRef(id=Q_ALIVE, text="Is your character still alive?", category="Age"),
    Q_MAN: QuestionRef(id=Q_MAN, text="Is your character a man?", category="Gender"),
    Q_INDIA: QuestionRef(id=Q_INDIA, text="Is your character from India?", category="Nationality"),
    Q_ATHLETE: QuestionRef(id=Q_ATHLETE, text="Is your character an athlete?", category="Sports"),
    Q_ALONE: QuestionRef(
        id=Q_ALONE, text="Does your character play alone sports?", category="Sports"
    ),
    Q_CRICKET: QuestionRef(
        id=Q_CRICKET, text="Does your character play cricket?", category="Sports"
    ),
    Q_FOOTBALL: QuestionRef(
        id=Q_FOOTBALL, text="Does your character play football?", category="Sports"
    ),
    Q_TENNIS: QuestionRef(
        id=Q_TENNIS, text="Does your character play tennis?", category="Sports"
    ),
    Q_WICKET: QuestionRef(
        id=Q_WICKET, text="Does your character keep wickets in cricket?", category="Sports"
    ),
    Q_OPENER: QuestionRef(
        id=Q_OPENER, text="Is your character mainly an opening batter?", category="Sports"
    ),
    Q_DEBUT: QuestionRef(
        id=Q_DEBUT,
        text="Did your character debut in cricket before 2000?",
        category="Sports",
    ),
    Q_ACTOR: QuestionRef(id=Q_ACTOR, text="Is your character an actor?", category="Profession"),
    Q_FAMOUS: QuestionRef(
        id=Q_FAMOUS, text="Is your character famous worldwide?", category="Personality"
    ),
}
QUESTIONS = list(REFS)


def _L(value: float) -> LikelihoodEntry:
    return LikelihoodEntry(value, 80)


def _catalog():
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry] = {}
    cricket = {DHONI, KOHLI, ROHIT, SACHIN, SMRITI}
    for cid in CHARS:
        sports = cid != SRK
        india = cid != MESSI
        man = cid not in {SMRITI, SANIA}
        likelihoods[(cid, Q_REAL)] = _L(0.96)
        likelihoods[(cid, Q_ALIVE)] = _L(0.92)
        likelihoods[(cid, Q_FAMOUS)] = _L(0.90)
        likelihoods[(cid, Q_MAN)] = _L(0.95 if man else 0.06)
        likelihoods[(cid, Q_INDIA)] = _L(0.96 if india else 0.08)
        likelihoods[(cid, Q_ATHLETE)] = _L(0.97 if sports else 0.08)
        if cid == SANIA:
            likelihoods[(cid, Q_ALONE)] = _L(0.92)
        elif sports:
            likelihoods[(cid, Q_ALONE)] = _L(0.08)
        else:
            likelihoods[(cid, Q_ALONE)] = _L(0.5)
        likelihoods[(cid, Q_CRICKET)] = _L(0.96 if cid in cricket else 0.08)
        likelihoods[(cid, Q_FOOTBALL)] = _L(0.96 if cid == MESSI else 0.08)
        likelihoods[(cid, Q_TENNIS)] = _L(0.96 if cid == SANIA else 0.08)
        likelihoods[(cid, Q_ACTOR)] = _L(0.95 if cid == SRK else 0.08)
        likelihoods[(cid, Q_WICKET)] = _L(0.96 if cid == DHONI else 0.08 if cid in cricket else 0.5)
        likelihoods[(cid, Q_OPENER)] = _L(
            0.96 if cid in {ROHIT, SMRITI} else 0.08 if cid in cricket else 0.5
        )
        likelihoods[(cid, Q_DEBUT)] = _L(0.96 if cid == SACHIN else 0.08 if cid in cricket else 0.5)
    popularity = {
        KOHLI: 100,
        DHONI: 98,
        SACHIN: 97,
        ROHIT: 95,
        MESSI: 99,
        SRK: 96,
        SMRITI: 80,
        SANIA: 78,
    }
    return create_initial_state(CHARS, likelihoods, popularity=popularity)


def _next(state):
    return select_next_question(
        state,
        QUESTIONS,
        question_refs=REFS,
        character_categories=CATEGORIES,
        character_names=NAMES,
        min_samples=1,
    )


def _play(path: list[tuple[UUID, str]]):
    state = _catalog()
    for qid, ans in path:
        state, _ = process_answer(state, qid, ans)
    return state


def test_generic_answers_do_not_guess_dhoni():
    path = [
        (Q_ATHLETE, "yes"),
        (Q_ALONE, "no"),
        (Q_ALIVE, "yes"),
        (Q_INDIA, "yes"),
        (Q_MAN, "yes"),
    ]
    state = _play(path)
    conf = evaluate_confidence(state)
    assert conf.should_guess is False
    remaining = {NAMES[cid] for cid in state.active_character_ids()}
    assert "MS Dhoni" in remaining
    assert "Virat Kohli" in remaining
    assert "Rohit Sharma" in remaining
    assert "Sachin Tendulkar" in remaining
    nxt = _next(state)
    assert nxt == Q_CRICKET


def test_after_cricket_asks_a_role_not_a_guess():
    state = _play(
        [
            (Q_ATHLETE, "yes"),
            (Q_INDIA, "yes"),
            (Q_MAN, "yes"),
            (Q_ALIVE, "yes"),
            (Q_CRICKET, "yes"),
        ]
    )
    conf = evaluate_confidence(state)
    assert conf.should_guess is False
    nxt = _next(state)
    assert nxt in {Q_WICKET, Q_OPENER, Q_DEBUT}
    assert nxt not in {Q_FAMOUS, Q_REAL, Q_ATHLETE}


def test_wicketkeeper_yes_ranks_dhoni_over_kohli():
    state = _play(
        [
            (Q_ATHLETE, "yes"),
            (Q_INDIA, "yes"),
            (Q_MAN, "yes"),
            (Q_CRICKET, "yes"),
            (Q_WICKET, "yes"),
        ]
    )
    ranked = sorted(state.probabilities, key=lambda cid: -state.probabilities[cid])
    assert ranked[0] == DHONI
    remaining = set(state.active_character_ids())
    assert DHONI in remaining
    assert KOHLI not in remaining
    assert ROHIT not in remaining


def test_kohli_path_does_not_collapse_to_dhoni():
    state = _play(
        [
            (Q_ATHLETE, "yes"),
            (Q_INDIA, "yes"),
            (Q_MAN, "yes"),
            (Q_CRICKET, "yes"),
            (Q_WICKET, "no"),
            (Q_OPENER, "no"),
            (Q_DEBUT, "no"),
        ]
    )
    ranked = sorted(state.probabilities, key=lambda cid: -state.probabilities[cid])
    assert ranked[0] == KOHLI
    assert ranked[0] != DHONI


def test_delay_guess_until_cricket_and_role_asked():
    state = _play(
        [
            (Q_ATHLETE, "yes"),
            (Q_INDIA, "yes"),
            (Q_MAN, "yes"),
            (Q_ALIVE, "yes"),
        ]
    )
    assert should_delay_guess_for_sport_split(state, REFS, CATEGORIES) is True
    state, _ = process_answer(state, Q_CRICKET, "yes")
    assert should_delay_guess_for_sport_split(state, REFS, CATEGORIES) is True
    state, _ = process_answer(state, Q_WICKET, "yes")
    assert should_delay_guess_for_sport_split(state, REFS, CATEGORIES) is False


def test_inflated_dhoni_generic_likelihood_still_delays_guess():
    """Live learning had nudged Dhoni athlete/India slightly above Kohli."""
    state = _catalog()
    state.likelihoods[(DHONI, Q_ATHLETE)] = _L(0.978)
    state.likelihoods[(DHONI, Q_INDIA)] = _L(0.970)
    state.likelihoods[(DHONI, Q_MAN)] = _L(0.963)
    state.likelihoods[(DHONI, Q_ALIVE)] = _L(0.940)
    for qid, ans in [
        (Q_ATHLETE, "yes"),
        (Q_INDIA, "yes"),
        (Q_MAN, "yes"),
        (Q_ALIVE, "yes"),
    ]:
        state, _ = process_answer(state, qid, ans)
    remaining = {NAMES[cid] for cid in state.active_character_ids()}
    assert "MS Dhoni" in remaining
    assert "Virat Kohli" in remaining
    assert should_delay_guess_for_sport_split(state, REFS, CATEGORIES) is True
    nxt = _next(state)
    assert nxt in {Q_CRICKET, Q_FOOTBALL, Q_TENNIS}
    assert nxt != Q_FAMOUS
