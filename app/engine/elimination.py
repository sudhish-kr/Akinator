import math
from uuid import UUID

from app.engine.constants import DEFAULT_ELIMINATION_FLOOR, DEFAULT_ELIMINATION_MAGNITUDE
from app.engine.models import GameEngineState


def entropy(probabilities: dict[UUID, float]) -> float:
    """Shannon entropy H = -sum(P(C) * log2(P(C))) for P(C) > 0 (TDD Section 2.3)."""
    h = 0.0
    for p in probabilities.values():
        if p > 0:
            h -= p * math.log2(p)
    return h


def top_two(probabilities: dict[UUID, float]) -> tuple[tuple[UUID, float] | None, tuple[UUID, float] | None]:
    sorted_items = sorted(probabilities.items(), key=lambda x: x[1], reverse=True)
    top = sorted_items[0] if sorted_items else None
    second = sorted_items[1] if len(sorted_items) > 1 else None
    return top, second


def eliminate_candidates(
    state: GameEngineState,
    floor: float = DEFAULT_ELIMINATION_FLOOR,
    magnitude: float = DEFAULT_ELIMINATION_MAGNITUDE,
) -> tuple[dict[UUID, float], UUID | None]:
    """
    Remove statistically negligible candidates (TDD Section 2.4).
    Returns (remaining_probabilities, pre_elimination_top_id).
    """
    probs = state.probabilities
    if not probs:
        return {}, None

    sorted_items = sorted(probs.items(), key=lambda x: x[1], reverse=True)
    pre_elimination_top = sorted_items[0][0]
    top_p = sorted_items[0][1]

    remaining: dict[UUID, float] = {}
    for cid, p in probs.items():
        if p < floor:
            continue
        if top_p > 0 and p < top_p / magnitude:
            continue
        remaining[cid] = p

    if not remaining:
        # TDD Section 7: fallback to highest before elimination
        return {pre_elimination_top: 1.0}, pre_elimination_top

    total = sum(remaining.values())
    return {cid: p / total for cid, p in remaining.items()}, pre_elimination_top
