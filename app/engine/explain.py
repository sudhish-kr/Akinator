"""Explainable guess attribution — read-only; does not alter Bayesian update math.

For each answered question, replays the session without that answer (leave-one-out)
using the existing `process_answer` path on a fresh state, then measures the drop
in the guessed character's posterior. Candidate rankings come from current
engine probabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.engine.learn_categories import matching_character_categories
from app.engine.models import GameEngineState, LikelihoodEntry, QuestionRef
from app.engine.selector import create_initial_state, process_answer


@dataclass(frozen=True)
class AnswerObservation:
    question_id: UUID
    answer: str


def _probability_of(state: GameEngineState, character_id: UUID) -> float:
    return float(state.probabilities.get(character_id, 0.0))


def replay_answers(
    character_ids: list[UUID],
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry],
    answers: list[AnswerObservation],
) -> GameEngineState:
    """Replay answers on a fresh uniform prior (existing process_answer only)."""
    state = create_initial_state(list(character_ids), likelihoods)
    for obs in answers:
        state, _ = process_answer(state, obs.question_id, obs.answer)
    return state


def top_candidates(
    probabilities: dict[UUID, float],
    character_names: dict[UUID, str],
    *,
    limit: int = 5,
) -> list[dict]:
    ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    out: list[dict] = []
    for cid, prob in ranked[:limit]:
        out.append(
            {
                "id": str(cid),
                "name": character_names.get(cid, str(cid)),
                "probability": round(float(prob), 4),
            }
        )
    return out


def remaining_candidates(
    probabilities: dict[UUID, float],
    character_names: dict[UUID, str],
    character_categories: dict[UUID, str] | None = None,
    *,
    category: str | None = None,
    q: str | None = None,
    exclude_ids: set[UUID] | frozenset[UUID] | None = None,
    limit: int = 40,
) -> list[dict]:
    """Rank the current posterior pool for wrong-guess recovery (in-memory)."""
    if not probabilities or limit <= 0:
        return []

    excluded = exclude_ids or set()
    needle = (q or "").strip().casefold()
    allowed_cats = matching_character_categories(category)
    cats = character_categories or {}
    ranked = sorted(probabilities.items(), key=lambda item: item[1], reverse=True)
    out: list[dict] = []
    for cid, prob in ranked:
        if cid in excluded:
            continue
        if allowed_cats and cats.get(cid) not in allowed_cats:
            continue
        name = character_names.get(cid, str(cid))
        if needle and needle not in name.casefold():
            continue
        out.append(
            {
                "id": str(cid),
                "name": name,
                "probability": round(float(prob), 4),
            }
        )
        if len(out) >= limit:
            break
    return out


def influential_questions(
    *,
    guessed_id: UUID,
    full_probability: float,
    character_ids: list[UUID],
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry],
    answers: list[AnswerObservation],
    question_refs: dict[UUID, QuestionRef],
    limit: int = 5,
) -> list[dict]:
    """Rank asked questions by leave-one-out drop in P(guessed)."""
    if not answers:
        return []

    scored: list[dict] = []
    for index, obs in enumerate(answers):
        remaining = [a for i, a in enumerate(answers) if i != index]
        without = replay_answers(character_ids, likelihoods, remaining)
        influence = full_probability - _probability_of(without, guessed_id)
        ref = question_refs.get(obs.question_id)
        scored.append(
            {
                "id": str(obs.question_id),
                "text": ref.text if ref else "",
                "answer": obs.answer,
                "influence": round(float(influence), 4),
            }
        )

    scored.sort(key=lambda row: row["influence"], reverse=True)
    return scored[:limit]


def build_guess_explanation(
    *,
    guessed_id: UUID,
    guessed_name: str,
    confidence: float,
    probabilities: dict[UUID, float],
    character_ids: list[UUID],
    character_names: dict[UUID, str],
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry],
    answers: list[AnswerObservation],
    question_refs: dict[UUID, QuestionRef],
    limit: int = 5,
) -> dict:
    """Assemble explanation payload for a guess (no mutation of live engine)."""
    full_p = float(probabilities.get(guessed_id, confidence))
    influencers = influential_questions(
        guessed_id=guessed_id,
        full_probability=full_p,
        character_ids=character_ids,
        likelihoods=likelihoods,
        answers=answers,
        question_refs=question_refs,
        limit=limit,
    )
    candidates = top_candidates(probabilities, character_names, limit=limit)

    if influencers:
        highlights = "; ".join(
            f'“{row["text"]}” → {row["answer"].replace("_", " ")}' for row in influencers[:3] if row["text"]
        )
        summary = (
            f"I chose {guessed_name} because your answers most strongly supported "
            f"that candidate — especially: {highlights}."
            if highlights
            else f"I chose {guessed_name} based on the posterior after your answers."
        )
    else:
        summary = (
            f"I chose {guessed_name} as the top remaining candidate "
            f"({round(confidence * 100)}% confidence) with no answered questions to attribute."
        )

    return {
        "summary": summary,
        "confidence_percent": round(max(0.0, min(100.0, confidence * 100.0)), 1),
        "top_candidates": candidates,
        "influential_questions": influencers,
    }
