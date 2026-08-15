"""Regression: early turns prioritize natural questions over niche age."""

from __future__ import annotations

import random
from uuid import UUID

from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    early_question_priority_bonus,
    is_low_priority_age_question,
    process_answer,
    select_next_question,
    should_defer_low_priority_age,
)
from app.training.oracle import oracle_answer

KOHLI = UUID("00000000-0000-0000-0000-000000000701")
MESSI = UUID("00000000-0000-0000-0000-000000000702")
EINSTEIN = UUID("00000000-0000-0000-0000-000000000703")
SRK = UUID("00000000-0000-0000-0000-000000000704")
NARUTO = UUID("00000000-0000-0000-0000-000000000705")

Q_REAL = UUID("00000000-0000-0000-0000-000000000801")
Q_MADE_UP = UUID("00000000-0000-0000-0000-000000000802")
Q_MALE = UUID("00000000-0000-0000-0000-000000000803")
Q_ALIVE = UUID("00000000-0000-0000-0000-000000000804")
Q_FAMOUS = UUID("00000000-0000-0000-0000-000000000805")
Q_INDIA = UUID("00000000-0000-0000-0000-000000000806")
Q_SPORTS = UUID("00000000-0000-0000-0000-000000000807")
Q_BABY = UUID("00000000-0000-0000-0000-000000000808")
Q_TODDLER = UUID("00000000-0000-0000-0000-000000000809")
Q_TEEN = UUID("00000000-0000-0000-0000-00000000080a")
Q_ELDERLY = UUID("00000000-0000-0000-0000-00000000080b")
Q_KID = UUID("00000000-0000-0000-0000-00000000080c")

CHARS = [KOHLI, MESSI, EINSTEIN, SRK, NARUTO]
QUESTIONS = [
    Q_REAL,
    Q_MADE_UP,
    Q_MALE,
    Q_ALIVE,
    Q_FAMOUS,
    Q_INDIA,
    Q_SPORTS,
    Q_BABY,
    Q_TODDLER,
    Q_TEEN,
    Q_ELDERLY,
    Q_KID,
]

LOW_AGE_IDS = {Q_BABY, Q_TODDLER, Q_TEEN, Q_ELDERLY, Q_KID}

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
    Q_INDIA: QuestionRef(id=Q_INDIA, text="Are they from India?", category="Nationality"),
    Q_SPORTS: QuestionRef(id=Q_SPORTS, text="Is this a sports player?", category="Sports"),
    Q_BABY: QuestionRef(id=Q_BABY, text="Are they a baby or toddler?", category="Age"),
    Q_TODDLER: QuestionRef(
        id=Q_TODDLER, text="Are they a toddler?", category="Age"
    ),
    Q_TEEN: QuestionRef(id=Q_TEEN, text="Are they a teenager?", category="Age"),
    Q_ELDERLY: QuestionRef(id=Q_ELDERLY, text="Are they elderly?", category="Age"),
    Q_KID: QuestionRef(id=Q_KID, text="Are they a kid or teen?", category="Age"),
}

CATEGORIES = {
    KOHLI: "Sports",
    MESSI: "Sports",
    EINSTEIN: "Scientists",
    SRK: "Movies",
    NARUTO: "Anime",
}

PROFILE = {
    KOHLI: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.9,
        Q_INDIA: 0.95,
        Q_SPORTS: 0.97,
        Q_BABY: 0.02,
        Q_TODDLER: 0.02,
        Q_TEEN: 0.05,
        Q_ELDERLY: 0.05,
        Q_KID: 0.05,
    },
    MESSI: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_INDIA: 0.05,
        Q_SPORTS: 0.97,
        Q_BABY: 0.02,
        Q_TODDLER: 0.02,
        Q_TEEN: 0.05,
        Q_ELDERLY: 0.05,
        Q_KID: 0.05,
    },
    EINSTEIN: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.05,
        Q_FAMOUS: 0.95,
        Q_INDIA: 0.05,
        Q_SPORTS: 0.05,
        Q_BABY: 0.02,
        Q_TODDLER: 0.02,
        Q_TEEN: 0.05,
        Q_ELDERLY: 0.2,
        Q_KID: 0.05,
    },
    SRK: {
        Q_REAL: 0.95,
        Q_MADE_UP: 0.05,
        Q_MALE: 0.95,
        Q_ALIVE: 0.9,
        Q_FAMOUS: 0.95,
        Q_INDIA: 0.95,
        Q_SPORTS: 0.05,
        Q_BABY: 0.02,
        Q_TODDLER: 0.02,
        Q_TEEN: 0.05,
        Q_ELDERLY: 0.1,
        Q_KID: 0.05,
    },
    NARUTO: {
        Q_REAL: 0.05,
        Q_MADE_UP: 0.95,
        Q_MALE: 0.95,
        Q_ALIVE: 0.5,
        Q_FAMOUS: 0.9,
        Q_INDIA: 0.05,
        Q_SPORTS: 0.05,
        Q_BABY: 0.05,
        Q_TODDLER: 0.1,
        Q_TEEN: 0.7,
        Q_ELDERLY: 0.05,
        Q_KID: 0.7,
    },
}


def _likelihoods():
    return {
        (cid, qid): LikelihoodEntry(v, 50)
        for cid, answers in PROFILE.items()
        for qid, v in answers.items()
    }


def _first_questions(true_id: UUID, *, n: int = 2, seed: int = 3) -> list[UUID]:
    rng = random.Random(seed)
    likelihoods = _likelihoods()
    state = create_initial_state(CHARS, likelihoods)
    asked: list[UUID] = []
    for _ in range(n):
        qid = select_next_question(
            state,
            QUESTIONS,
            min_samples=1,
            question_refs=REFS,
            character_categories=CATEGORIES,
            explore=False,
            rng=rng,
        )
        assert qid is not None
        answer = oracle_answer(likelihoods, true_id, qid, rng, noise=0.0)
        state, _ = process_answer(state, qid, answer)
        asked.append(qid)
    return asked


def test_low_priority_age_helpers():
    assert is_low_priority_age_question(REFS[Q_BABY])
    assert is_low_priority_age_question(REFS[Q_TEEN])
    assert is_low_priority_age_question(REFS[Q_ELDERLY])
    assert not is_low_priority_age_question(REFS[Q_REAL])
    assert early_question_priority_bonus(REFS[Q_REAL]) > early_question_priority_bonus(
        REFS[Q_SPORTS]
    )
    assert early_question_priority_bonus(REFS[Q_SPORTS]) > 0
    assert should_defer_low_priority_age(
        questions_asked=1, stage="1", ig=0.5, best_non_low_ig=0.4
    )
    # Niche age stays gated through category phase; only Stage 4 may unlock.
    assert should_defer_low_priority_age(
        questions_asked=8, stage="3", ig=0.3, best_non_low_ig=0.31
    )
    assert not should_defer_low_priority_age(
        questions_asked=8, stage="4", ig=0.3, best_non_low_ig=0.31
    )


def test_question_two_never_low_age_for_real_person_paths():
    for true_id, label in [
        (KOHLI, "Virat Kohli"),
        (MESSI, "Lionel Messi"),
        (EINSTEIN, "Albert Einstein"),
        (SRK, "Shah Rukh Khan"),
    ]:
        asked = _first_questions(true_id, n=2, seed=11)
        assert len(asked) == 2, label
        second = asked[1]
        text = REFS[second].text.casefold()
        assert second not in LOW_AGE_IDS, (label, text)
        for kw in ("baby", "toddler", "teenager", "elderly"):
            assert kw not in text, (label, text)


def test_early_turns_prefer_natural_priority_over_age():
    for true_id in (KOHLI, MESSI, EINSTEIN, SRK):
        # Five early turns are enough to prove age stays locked. A 6th pick used
        # to be the contradictory "made-up?" after "real person? YES".
        asked = _first_questions(true_id, n=5, seed=5)
        assert asked[0] not in LOW_AGE_IDS
        assert all(qid not in LOW_AGE_IDS for qid in asked)
        # First pick should be a ranked early-priority question (identity/origin/domain).
        assert early_question_priority_bonus(REFS[asked[0]]) >= 0.14
