"""Regression tests for curated Question Database v2."""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path
from uuid import UUID, uuid4

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
SEED_PATH = ROOT / "data" / "knowledge" / "seed_v1.json"
QUESTIONS_V2_PATH = ROOT / "data" / "knowledge" / "questions_v2.json"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from questions_v2_data import (  # noqa: E402
    DATASET_ID,
    LEVEL_NAMES,
    MAX_WORDS,
    build_v2_questions,
    questions_by_level,
)

from app.engine.constants import (  # noqa: E402
    PROFESSION_SPECIFIC_KEYWORDS,
    STAGE_A_QUESTION_CATEGORIES,
)
from app.engine.models import LikelihoodEntry, QuestionRef  # noqa: E402
from app.engine.selector import (  # noqa: E402
    create_initial_state,
    process_answer,
    question_hierarchy_stage,
    resolve_selection_stage,
    select_next_question,
)
from app.training.oracle import oracle_answer  # noqa: E402

HARD_VOCAB = {
    "protagonist",
    "antagonist",
    "entrepreneurship",
    "astronomy",
    "quantum",
    "franchise",
    "manga",
    "androgynous",
    "canon",
    "architect",
    "lawyer",
    "chef",
}


@pytest.fixture(scope="module")
def v2_questions():
    return build_v2_questions()


@pytest.fixture(scope="module")
def seed():
    assert SEED_PATH.exists()
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def test_v2_catalog_size_and_hierarchy(v2_questions):
    assert 220 <= len(v2_questions) <= 300
    by_level = questions_by_level()
    assert set(by_level) == set(LEVEL_NAMES)
    assert all(by_level[level] for level in LEVEL_NAMES)
    assert QUESTIONS_V2_PATH.exists()
    exported = json.loads(QUESTIONS_V2_PATH.read_text(encoding="utf-8"))
    assert exported["dataset"] == DATASET_ID
    assert len(exported["questions"]) == len(v2_questions)


def test_v2_questions_use_akinator_style_phrasing(v2_questions):
    """Most questions should sound like Akinator: 'Is/Does your character…?'"""
    classic = 0
    for q in v2_questions:
        text = q["text"].casefold()
        if text.startswith("is your character") or text.startswith("does your character"):
            classic += 1
        elif text.startswith("did your character") or text.startswith("can your character"):
            classic += 1
        elif text.startswith("has your character") or text.startswith("was your character"):
            classic += 1
    assert classic / len(v2_questions) >= 0.9
    # Core identity/category lines must exist.
    texts = {q["text"] for q in v2_questions}
    for required in (
        "Is your character a real person?",
        "Is your character still alive?",
        "Is your character a man?",
        "Is your character an athlete?",
        "Is your character from anime?",
        "Does your character play cricket?",
        "Does your character play football?",
        "Is your character a superhero?",
    ):
        assert required in texts


def test_level1_identity_uses_broad_categories_only(v2_questions):
    from app.engine.constants import STAGE_1_IDENTITY_KEYWORDS, STAGE_2_ORIGIN_KEYWORDS

    for q in v2_questions:
        if q["hierarchy_level"] != 1:
            continue
        assert q["category"] in STAGE_A_QUESTION_CATEGORIES, q
        text = q["text"].casefold()
        stage = question_hierarchy_stage(
            QuestionRef(id=uuid4(), text=q["text"], category=q["category"])
        )
        if any(kw in text for kw in STAGE_2_ORIGIN_KEYWORDS):
            assert stage == "2", q
        elif any(kw in text for kw in STAGE_1_IDENTITY_KEYWORDS):
            assert stage == "1", q


def test_seed_defaults_to_active_v2_and_deactivated_legacy(seed):
    assert seed.get("question_phase") == 2
    assert seed.get("active_question_dataset") == DATASET_ID
    questions = seed["questions"]
    active = [q for q in questions if q.get("is_active")]
    inactive = [q for q in questions if not q.get("is_active")]
    assert 220 <= len(active) <= 300
    assert len(inactive) >= 400
    assert all(q.get("dataset") == DATASET_ID for q in active)
    assert all(q.get("dataset") == "v1" for q in inactive)
    assert len(questions) >= 500


def test_early_questions_are_broad(v2_questions):
    """Uniform start must only select Level-1 / Stage-A identity questions."""
    chars = [uuid4() for _ in range(4)]
    categories = {
        chars[0]: "Sports",
        chars[1]: "Anime",
        chars[2]: "Scientists",
        chars[3]: "Movies",
    }
    active = [q for q in v2_questions if q["is_active"]]
    qids = [uuid4() for _ in active]
    refs = {
        qid: QuestionRef(id=qid, text=q["text"], category=q["category"])
        for qid, q in zip(qids, active, strict=True)
    }
    likelihoods = {
        (cid, qid): LikelihoodEntry(0.5, 40) for cid in chars for qid in qids
    }
    # Slight identity split so IG is defined, but categories stay equal-mass.
    for qid, q in zip(qids, active, strict=True):
        if "real person" in q["text"].casefold():
            likelihoods[(chars[0], qid)] = LikelihoodEntry(0.9, 40)
            likelihoods[(chars[1], qid)] = LikelihoodEntry(0.1, 40)
            likelihoods[(chars[2], qid)] = LikelihoodEntry(0.9, 40)
            likelihoods[(chars[3], qid)] = LikelihoodEntry(0.1, 40)

    state = create_initial_state(chars, likelihoods)
    stage, _ = resolve_selection_stage(state, categories)
    assert stage == "1"
    chosen = select_next_question(
        state,
        qids,
        min_samples=1,
        question_refs=refs,
        character_categories=categories,
        explore=False,
    )
    assert chosen is not None
    assert question_hierarchy_stage(refs[chosen]) == "1"
    assert refs[chosen].category in STAGE_A_QUESTION_CATEGORIES


def test_profession_questions_never_before_category_detection(v2_questions):
    profession_texts = {
        q["text"].casefold()
        for q in v2_questions
        if q["category"] == "Profession"
        or any(kw in q["text"].casefold() for kw in PROFESSION_SPECIFIC_KEYWORDS)
    }
    assert profession_texts

    kohli = uuid4()
    naruto = uuid4()
    einstein = uuid4()
    batman = uuid4()
    chars = [kohli, naruto, einstein, batman]
    categories = {
        kohli: "Sports",
        naruto: "Anime",
        einstein: "Scientists",
        batman: "Movies",
    }
    active = v2_questions
    qids = [uuid4() for _ in active]
    refs = {
        qid: QuestionRef(id=qid, text=q["text"], category=q["category"])
        for qid, q in zip(qids, active, strict=True)
    }
    text_by_id = {qid: q["text"].casefold() for qid, q in zip(qids, active, strict=True)}

    def lik_for(cid: UUID, text: str) -> float:
        t = text.casefold()
        profile = {
            kohli: {
                "real person": 0.95,
                "made-up": 0.05,
                "sports player": 0.97,
                "from anime": 0.02,
                "singer": 0.05,
                "actor": 0.05,
            },
            naruto: {
                "real person": 0.05,
                "made-up": 0.95,
                "sports player": 0.05,
                "from anime": 0.97,
                "singer": 0.05,
                "actor": 0.1,
            },
            einstein: {
                "real person": 0.95,
                "made-up": 0.05,
                "sports player": 0.05,
                "from anime": 0.02,
                "scientist": 0.96,
                "singer": 0.05,
                "actor": 0.05,
            },
            batman: {
                "real person": 0.1,
                "made-up": 0.9,
                "sports player": 0.1,
                "from anime": 0.05,
                "from a movie": 0.96,
                "singer": 0.05,
                "actor": 0.2,
            },
        }[cid]
        for needle, value in profile.items():
            if needle in t:
                return value
        return 0.45

    likelihoods = {
        (cid, qid): LikelihoodEntry(lik_for(cid, refs[qid].text), 50)
        for cid in chars
        for qid in qids
    }

    for true_id in chars:
        rng = random.Random(9)
        state = create_initial_state(chars, likelihoods)
        for _ in range(5):
            stage, _dominant = resolve_selection_stage(state, categories)
            qid = select_next_question(
                state,
                qids,
                min_samples=1,
                question_refs=refs,
                character_categories=categories,
                explore=False,
                rng=rng,
            )
            assert qid is not None
            text = text_by_id[qid]
            if stage in {"1", "2", "3"}:
                assert text not in profession_texts
                assert refs[qid].category != "Profession"
                for kw in ("singer", "actor", "actress"):
                    if kw in text:
                        pytest.fail(f"Profession wording in stage {stage}: {text}")
            answer = oracle_answer(likelihoods, true_id, qid, rng, noise=0.0)
            state, _ = process_answer(state, qid, answer)


def test_anime_questions_never_appear_for_real_person_paths(v2_questions):
    kohli = uuid4()
    messi = uuid4()
    einstein = uuid4()
    chars = [kohli, messi, einstein]
    categories = {kohli: "Sports", messi: "Sports", einstein: "Scientists"}
    active = v2_questions
    qids = [uuid4() for _ in active]
    refs = {
        qid: QuestionRef(id=qid, text=q["text"], category=q["category"])
        for qid, q in zip(qids, active, strict=True)
    }

    def lik_for(cid: UUID, text: str, category: str) -> float:
        t = text.casefold()
        if "real person" in t:
            return 0.95
        if "made-up" in t:
            return 0.05
        if category == "Anime" or "anime" in t:
            return 0.02
        if "sports player" in t:
            return 0.97 if cid in {kohli, messi} else 0.05
        if "scientist" in t:
            return 0.95 if cid == einstein else 0.05
        if "still alive" in t:
            return 0.9 if cid != einstein else 0.05
        return 0.45

    likelihoods = {
        (cid, qid): LikelihoodEntry(lik_for(cid, refs[qid].text, refs[qid].category or ""), 50)
        for cid in chars
        for qid in qids
    }

    for true_id in chars:
        rng = random.Random(21)
        state = create_initial_state(chars, likelihoods)
        for _ in range(6):
            stage, dominant = resolve_selection_stage(state, categories)
            qid = select_next_question(
                state,
                qids,
                min_samples=1,
                question_refs=refs,
                character_categories=categories,
                explore=False,
                rng=rng,
            )
            if qid is None:
                break
            if refs[qid].category == "Anime" or "anime" in refs[qid].text.casefold():
                assert dominant == "Anime", (stage, dominant, refs[qid].text)
            if stage == "1":
                assert refs[qid].category != "Anime"
            answer = oracle_answer(likelihoods, true_id, qid, rng, noise=0.0)
            state, _ = process_answer(state, qid, answer)
