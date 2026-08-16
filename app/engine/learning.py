"""Post-game learning engine (TDD v1.1 Section 4).

Learns from completed games by nudging L(C, Q) toward observed answers.
On a wrong guess, stores the correct character plus a distinguishing
question/answer into the knowledge base (upsert — no duplicate pairs).

Does not perform Bayesian updates or question selection.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.engine.bayesian import apply_learning_update
from app.engine.constants import (
    ANSWER_WEIGHTS,
    DEFAULT_LEARNING_RATE,
    DEFAULT_NEW_QUESTION_MIN_SAMPLES,
)
from app.engine.models import answer_from_str

# Laplace smoothing used for sample-based P(YES | C, Q).
DEFAULT_LEARNING_ALPHA = 1.0
# Session questions must differ by at least this much to split guessed vs actual.
DEFAULT_DISTINGUISH_SPREAD = 0.40


@dataclass(frozen=True)
class AnswerObservation:
    """One answered question from a completed (or terminal) game."""

    question_id: UUID
    answer: str


@dataclass(frozen=True)
class KnowledgeEntry:
    """Existing L(C, Q) row in the knowledge base."""

    likelihood: float
    sample_size: int = 0


@dataclass(frozen=True)
class KnowledgeUpdate:
    """Upsert payload for one (character, question) knowledge pair."""

    character_id: UUID
    question_id: UUID
    likelihood: float
    sample_size: int


def _answer_weight(answer: str) -> float:
    resolved = answer_from_str(answer.strip().lower().replace(" ", "_"))
    return ANSWER_WEIGHTS[resolved.value]


def _dedupe_observations(observations: list[AnswerObservation]) -> list[AnswerObservation]:
    """Keep a single observation per question (last answer wins)."""
    by_question: dict[UUID, AnswerObservation] = {}
    for obs in observations:
        by_question[obs.question_id] = obs
    return list(by_question.values())


def _nudge_or_keep(old_l: float, weight: float, learning_rate: float) -> float:
    """Confirming an already-strong fact must not inflate L (Dhoni 0.97→0.978)."""
    if (old_l >= 0.85 and weight >= 0.75) or (old_l <= 0.15 and weight <= 0.25):
        return old_l
    return apply_learning_update(old_l, weight, learning_rate)


def sample_posterior_likelihood(
    old_likelihood: float,
    sample_size: int,
    observed_weight: float,
    *,
    alpha: float = DEFAULT_LEARNING_ALPHA,
) -> float:
    """Sample-based P(YES | C, Q) = (yes_samples + α) / (n + 2α).

    yes_samples is recovered as likelihood * sample_size. Does not replace
    the learning_rate nudge used for completed-game TDD updates.
    """
    n = max(0, int(sample_size))
    yes_samples = max(0.0, min(1.0, float(old_likelihood))) * n
    new_yes = yes_samples + max(0.0, min(1.0, float(observed_weight)))
    denom = n + 1 + 2.0 * float(alpha)
    if denom <= 0:
        return 0.5
    return max(0.0, min(1.0, (new_yes + float(alpha)) / denom))


def opposing_answer_weight(answer: str) -> float:
    """Map the user's answer about the true character to evidence against the wrong guess."""
    return 1.0 - _answer_weight(answer)


def find_distinguishing_session_questions(
    guessed_character_id: UUID,
    actual_character_id: UUID,
    observations: list[AnswerObservation],
    knowledge: dict[tuple[UUID, UUID], KnowledgeEntry],
    *,
    min_spread: float = DEFAULT_DISTINGUISH_SPREAD,
) -> list[tuple[UUID, str, float]]:
    """Session questions whose stored likelihoods already separate guessed vs actual.

    Operates only on in-memory knowledge for questions the user actually answered.
    Does not scan the CharacterAnswer table.
    """
    ranked: list[tuple[UUID, str, float]] = []
    for obs in _dedupe_observations(observations):
        guessed = knowledge.get((guessed_character_id, obs.question_id))
        actual = knowledge.get((actual_character_id, obs.question_id))
        if guessed is None or actual is None:
            continue
        spread = abs(float(guessed.likelihood) - float(actual.likelihood))
        if spread >= min_spread:
            ranked.append((obs.question_id, obs.answer, spread))
    ranked.sort(key=lambda row: row[2], reverse=True)
    return ranked


def learn_from_completed_game(
    character_id: UUID,
    observations: list[AnswerObservation],
    knowledge: dict[tuple[UUID, UUID], KnowledgeEntry],
    learning_rate: float = DEFAULT_LEARNING_RATE,
) -> list[KnowledgeUpdate]:
    """
    Learn from a finished game's answers for the true character.

    Updates the knowledge base without duplicates: one upsert per (C, Q).
    Likelihood uses the existing learning_rate nudge; sample_size always +1.
    """
    updates: dict[tuple[UUID, UUID], KnowledgeUpdate] = {}

    for obs in _dedupe_observations(observations):
        key = (character_id, obs.question_id)
        existing = knowledge.get(key)
        old_l = existing.likelihood if existing else 0.5
        old_n = existing.sample_size if existing else 0
        weight = _answer_weight(obs.answer)
        updates[key] = KnowledgeUpdate(
            character_id=character_id,
            question_id=obs.question_id,
            likelihood=_nudge_or_keep(old_l, weight, learning_rate),
            sample_size=old_n + 1,
        )

    return list(updates.values())


def store_distinguishing_fact(
    correct_character_id: UUID,
    question_id: UUID,
    answer: str,
    knowledge: dict[tuple[UUID, UUID], KnowledgeEntry],
    learning_rate: float = DEFAULT_LEARNING_RATE,
) -> KnowledgeUpdate:
    """
    When the AI guessed wrong: store the correct object with the
    distinguishing question and its answer (upsert, never a duplicate row).
    """
    key = (correct_character_id, question_id)
    existing = knowledge.get(key)
    old_l = existing.likelihood if existing else 0.5
    old_n = existing.sample_size if existing else 0
    weight = _answer_weight(answer)
    return KnowledgeUpdate(
        character_id=correct_character_id,
        question_id=question_id,
        likelihood=_nudge_or_keep(old_l, weight, learning_rate),
        sample_size=old_n + 1,
    )


def _update_wrong_guess_character(
    updates: dict[tuple[UUID, UUID], KnowledgeUpdate],
    *,
    guessed_character_id: UUID,
    observations: list[AnswerObservation],
    knowledge: dict[tuple[UUID, UUID], KnowledgeEntry],
    correct_character_id: UUID,
    min_samples: int,
    min_spread: float,
) -> None:
    """Nudge the wrong guess opposite the user's answers on questions that split A vs B.

    Never creates a new (guessed, question) mapping from a single noisy observation.
    """
    for qid, ans, _spread in find_distinguishing_session_questions(
        guessed_character_id,
        correct_character_id,
        observations,
        knowledge,
        min_spread=min_spread,
    ):
        if abs(_answer_weight(ans) - 0.5) < 1e-9:
            continue
        key = (guessed_character_id, qid)
        existing = knowledge.get(key)
        if existing is None or int(existing.sample_size) < min_samples:
            continue
        opp = opposing_answer_weight(ans)
        if (existing.likelihood >= 0.85 and opp >= 0.75) or (
            existing.likelihood <= 0.15 and opp <= 0.25
        ):
            new_l = existing.likelihood
        else:
            new_l = sample_posterior_likelihood(
                existing.likelihood, existing.sample_size, opp
            )
        updates[key] = KnowledgeUpdate(
            character_id=guessed_character_id,
            question_id=qid,
            likelihood=new_l,
            sample_size=existing.sample_size + 1,
        )


def learn_from_wrong_guess(
    correct_character_id: UUID,
    observations: list[AnswerObservation],
    knowledge: dict[tuple[UUID, UUID], KnowledgeEntry],
    *,
    distinguishing_question_id: UUID | None = None,
    distinguishing_answer: str | None = None,
    learning_rate: float = DEFAULT_LEARNING_RATE,
    guessed_character_id: UUID | None = None,
    min_samples: int = DEFAULT_NEW_QUESTION_MIN_SAMPLES,
    min_spread: float = DEFAULT_DISTINGUISH_SPREAD,
) -> list[KnowledgeUpdate]:
    """
    Wrong-guess learning: update KB for the correct character from the
    game answers, and ensure the distinguishing Q/A is stored once.

    When `guessed_character_id` is known, also update existing well-sampled
    mappings for questions that already separate the two characters.

    If distinguishing Q/A is omitted, prefer the session question with the
    largest |L(guessed) − L(actual)|; otherwise the last observation.
    """
    updates = {
        (u.character_id, u.question_id): u
        for u in learn_from_completed_game(
            correct_character_id, observations, knowledge, learning_rate
        )
    }

    dist_q = distinguishing_question_id
    dist_a = distinguishing_answer
    if dist_q is None or dist_a is None:
        if (
            guessed_character_id is not None
            and guessed_character_id != correct_character_id
        ):
            splits = find_distinguishing_session_questions(
                guessed_character_id,
                correct_character_id,
                observations,
                knowledge,
                min_spread=min_spread,
            )
            if splits:
                dist_q = dist_q or splits[0][0]
                dist_a = dist_a or splits[0][1]
        if (dist_q is None or dist_a is None) and observations:
            last = _dedupe_observations(observations)[-1]
            dist_q = dist_q or last.question_id
            dist_a = dist_a or last.answer

    if dist_q is not None and dist_a is not None:
        # Apply distinguishing upsert on top of session learning (still one row per pair)
        base_knowledge = dict(knowledge)
        for key, upd in updates.items():
            base_knowledge[key] = KnowledgeEntry(upd.likelihood, upd.sample_size)

        fact = store_distinguishing_fact(
            correct_character_id, dist_q, dist_a, base_knowledge, learning_rate
        )
        # If the fact was already produced by session learning, replace with
        # one combined sample bump from distinguishing (avoid double-counting
        # when it was only in observations once). Prefer single upsert:
        key = (fact.character_id, fact.question_id)
        if key in updates:
            # Already learned from session — keep session update (same Q/A, no dup)
            pass
        else:
            updates[key] = fact

    if guessed_character_id and guessed_character_id != correct_character_id:
        _update_wrong_guess_character(
            updates,
            guessed_character_id=guessed_character_id,
            observations=observations,
            knowledge=knowledge,
            correct_character_id=correct_character_id,
            min_samples=min_samples,
            min_spread=min_spread,
        )

    return list(updates.values())
