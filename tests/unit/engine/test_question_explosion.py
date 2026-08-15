"""Question explosion: stop when Qs no longer split the remaining pool."""

from __future__ import annotations

from uuid import UUID, uuid4

from app.engine.confidence import evaluate_confidence, resolve_turn
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    is_useful_split_on_pool,
    process_answer,
    select_next_question,
)
from app.services.session_manager import ConfidenceThresholds, GameSessionManager

DHONI = uuid4()
KOHLI = uuid4()
ROHIT = uuid4()
SACHIN = uuid4()
MESSI = uuid4()

Q_ATHLETE = uuid4()
Q_INDIA = uuid4()
Q_CRICKET = uuid4()
Q_WICKET = uuid4()
Q_OPENER = uuid4()
Q_GREEN = uuid4()
Q_FENCE = uuid4()
Q_ARCH = uuid4()


def _L(value: float, n: int = 80) -> LikelihoodEntry:
    return LikelihoodEntry(value, n)


def _cricket_catalog(*, green_mapped: bool = False):
    chars = [DHONI, KOHLI, ROHIT, SACHIN, MESSI]
    cricket = {DHONI, KOHLI, ROHIT, SACHIN}
    refs = {
        Q_ATHLETE: QuestionRef(id=Q_ATHLETE, text="Is your character an athlete?", category="Sports"),
        Q_INDIA: QuestionRef(id=Q_INDIA, text="Is your character from India?", category="Nationality"),
        Q_CRICKET: QuestionRef(
            id=Q_CRICKET, text="Does your character play cricket?", category="Sports"
        ),
        Q_WICKET: QuestionRef(
            id=Q_WICKET, text="Does your character keep wickets in cricket?", category="Sports"
        ),
        Q_OPENER: QuestionRef(
            id=Q_OPENER, text="Is your character mainly an opening batter?", category="Sports"
        ),
        Q_GREEN: QuestionRef(
            id=Q_GREEN, text="Does your character have green skin?", category="Physical appearance"
        ),
        Q_FENCE: QuestionRef(id=Q_FENCE, text="Does your character fence?", category="Sports"),
        Q_ARCH: QuestionRef(id=Q_ARCH, text="Is your character an architect?", category="Profession"),
    }
    cats = {cid: "Sports" for cid in chars}
    likes: dict[tuple[UUID, UUID], LikelihoodEntry] = {}
    for cid in chars:
        likes[(cid, Q_ATHLETE)] = _L(0.97)
        likes[(cid, Q_INDIA)] = _L(0.96 if cid != MESSI else 0.08)
        likes[(cid, Q_CRICKET)] = _L(0.96 if cid in cricket else 0.08)
        likes[(cid, Q_WICKET)] = _L(0.96 if cid == DHONI else 0.08)
        likes[(cid, Q_OPENER)] = _L(0.96 if cid == ROHIT else 0.08)
        likes[(cid, Q_FENCE)] = _L(0.08)
        likes[(cid, Q_ARCH)] = _L(0.08)
        if green_mapped:
            likes[(cid, Q_GREEN)] = _L(0.08)
    names = {
        DHONI: "MS Dhoni",
        KOHLI: "Virat Kohli",
        ROHIT: "Rohit Sharma",
        SACHIN: "Sachin Tendulkar",
        MESSI: "Lionel Messi",
    }
    state = create_initial_state(
        chars, likes, popularity={KOHLI: 100, DHONI: 98, SACHIN: 97, ROHIT: 95, MESSI: 99}
    )
    return state, list(refs), refs, cats, names


def _next(state, questions, refs, cats):
    return select_next_question(
        state, questions, min_samples=1, question_refs=refs, character_categories=cats
    )


def test_green_skin_is_not_useful_on_indian_cricketers():
    state, questions, refs, cats, _ = _cricket_catalog(green_mapped=False)
    for qid, ans in [(Q_ATHLETE, "yes"), (Q_INDIA, "yes"), (Q_CRICKET, "yes")]:
        state, _ = process_answer(state, qid, ans)
    assert not is_useful_split_on_pool(state, Q_GREEN, ig=0.2)
    nxt = _next(state, questions, refs, cats)
    assert nxt != Q_GREEN
    assert nxt != Q_FENCE
    assert nxt != Q_ARCH
    assert nxt in {Q_WICKET, Q_OPENER}


def test_cricket_peers_select_role_not_appearance_or_fencing():
    state, questions, refs, cats, names = _cricket_catalog(green_mapped=True)
    asked: list[UUID] = []
    for qid, ans in [(Q_ATHLETE, "yes"), (Q_INDIA, "yes"), (Q_CRICKET, "yes")]:
        state, _ = process_answer(state, qid, ans)
        asked.append(qid)
    for _ in range(8):
        nxt = _next(state, questions, refs, cats)
        if nxt is None:
            break
        assert nxt not in {Q_GREEN, Q_FENCE, Q_ARCH}, refs[nxt].text
        asked.append(nxt)
        ans = "yes" if nxt == Q_WICKET else "no"
        state, _ = process_answer(state, nxt, ans)
        remaining = {names[cid] for cid in state.active_character_ids()}
        if remaining <= {"MS Dhoni"}:
            break
    assert Q_GREEN not in asked
    assert Q_WICKET in asked


def test_after_opener_still_asks_other_cricket_roles():
    """Wicket/bowler/debut must not be treated as duplicates of opening batter."""
    state, questions, refs, cats, _ = _cricket_catalog(green_mapped=True)
    for qid, ans in [
        (Q_ATHLETE, "yes"),
        (Q_INDIA, "yes"),
        (Q_CRICKET, "yes"),
        (Q_OPENER, "no"),
    ]:
        state, _ = process_answer(state, qid, ans)
    nxt = _next(state, questions, refs, cats)
    assert nxt in {Q_WICKET}


def test_session_never_exceeds_safety_budget():
    state, questions, refs, cats, names = _cricket_catalog(green_mapped=True)
    mgr = GameSessionManager(
        thresholds=ConfidenceThresholds(high=0.99, separation=0.99, margin=0.99, max_questions=8),
        min_samples=1,
    )
    likes = state.likelihoods
    live = mgr.start(
        session_id=uuid4(),
        character_ids=state.character_ids,
        likelihoods=likes,
        question_ids=questions,
        question_refs=refs,
        character_names=names,
        character_categories=cats,
        character_popularity={KOHLI: 100, DHONI: 98, SACHIN: 97, ROHIT: 95, MESSI: 99},
    )
    for _ in range(40):
        if live.awaiting_guess:
            break
        turn = mgr.submit_answer(live, live.pending_question_id, "dont_know")
        assert turn.questions_asked <= 8
    assert live.awaiting_guess is True
    assert live.engine.questions_asked <= 8


def test_no_useful_question_triggers_guess():
    state = create_initial_state([DHONI, KOHLI], {})
    state.probabilities = {DHONI: 0.02, KOHLI: 0.02}
    state.questions_asked = 7
    result = resolve_turn(state, next_question_id=None, confidence_high=0.88, max_questions=20)
    assert result.should_guess is True
    assert result.reason == "no_questions_remain"


def test_budget_guesses_even_when_pool_is_tied():
    state = create_initial_state([DHONI, KOHLI, ROHIT], {})
    state.probabilities = {DHONI: 0.34, KOHLI: 0.33, ROHIT: 0.33}
    state.questions_asked = 20
    result = evaluate_confidence(state, max_questions=20)
    assert result.should_guess is True
    assert result.reason == "question_budget"
