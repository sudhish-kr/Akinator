"""JSON codec for LiveSession — portable across API workers via Redis.

Likelihood matrices can be huge; SessionStore persists them under a separate
cache key so per-turn saves stay compact (probabilities + metadata only).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from app.engine.models import GameEngineState, LikelihoodEntry, QuestionRef
from app.services.live_session import LiveSession, StoredAnswer


def _uuid(value: str | UUID) -> UUID:
    return value if isinstance(value, UUID) else UUID(str(value))


def encode_likelihoods(
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry],
) -> list[dict[str, Any]]:
    return [
        {
            "character_id": str(cid),
            "question_id": str(qid),
            "likelihood": float(entry.likelihood),
            "sample_size": int(entry.sample_size),
        }
        for (cid, qid), entry in likelihoods.items()
    ]


def decode_likelihoods(rows: list[dict[str, Any]] | None) -> dict[tuple[UUID, UUID], LikelihoodEntry]:
    if not rows:
        return {}
    return {
        (_uuid(row["character_id"]), _uuid(row["question_id"])): LikelihoodEntry(
            likelihood=float(row["likelihood"]),
            sample_size=int(row["sample_size"]),
        )
        for row in rows
    }


def encode_live_session(
    session: LiveSession,
    *,
    include_likelihoods: bool = True,
) -> dict[str, Any]:
    """Serialize a live session to a JSON-friendly dict."""
    engine = session.engine
    return {
        "session_id": str(session.session_id),
        "engine": {
            "character_ids": [str(cid) for cid in engine.character_ids],
            "probabilities": {str(cid): float(p) for cid, p in engine.probabilities.items()},
            "likelihoods": (
                encode_likelihoods(engine.likelihoods) if include_likelihoods else []
            ),
            "used_question_ids": [str(qid) for qid in engine.used_question_ids],
            "asked_question_order": [str(qid) for qid in engine.asked_question_order],
            "questions_asked": int(engine.questions_asked),
            "consecutive_dont_know": int(engine.consecutive_dont_know),
            "pre_elimination_top": (
                str(engine.pre_elimination_top) if engine.pre_elimination_top else None
            ),
        },
        "question_refs": {
            str(qid): {
                "id": str(ref.id),
                "text": ref.text,
                "category": ref.category,
            }
            for qid, ref in session.question_refs.items()
        },
        "character_names": {str(cid): name for cid, name in session.character_names.items()},
        "character_categories": {
            str(cid): cat for cid, cat in session.character_categories.items()
        },
        "character_popularity": {
            str(cid): int(score) for cid, score in session.character_popularity.items()
        },
        "all_question_ids": [str(qid) for qid in session.all_question_ids],
        "pending_question_id": (
            str(session.pending_question_id) if session.pending_question_id else None
        ),
        "last_answered_question_id": (
            str(session.last_answered_question_id)
            if session.last_answered_question_id
            else None
        ),
        "awaiting_guess": bool(session.awaiting_guess),
        "answers": [
            {"question_id": str(a.question_id), "answer": a.answer} for a in session.answers
        ],
        "last_activity_at": session.last_activity_at.astimezone(timezone.utc).isoformat(),
    }


def decode_live_session(payload: dict[str, Any]) -> LiveSession:
    """Reconstruct a LiveSession from encode_live_session output."""
    eng = payload["engine"]
    likelihoods = decode_likelihoods(eng.get("likelihoods"))
    pre_top = eng.get("pre_elimination_top")
    engine = GameEngineState(
        character_ids=[_uuid(cid) for cid in eng["character_ids"]],
        probabilities={_uuid(cid): float(p) for cid, p in eng["probabilities"].items()},
        likelihoods=likelihoods,
        used_question_ids={_uuid(qid) for qid in eng.get("used_question_ids") or []},
        asked_question_order=[
            _uuid(qid) for qid in (
                eng.get("asked_question_order") or eng.get("used_question_ids") or []
            )
        ],
        questions_asked=int(eng.get("questions_asked") or 0),
        consecutive_dont_know=int(eng.get("consecutive_dont_know") or 0),
        pre_elimination_top=_uuid(pre_top) if pre_top else None,
    )

    question_refs: dict[UUID, QuestionRef] = {}
    for key, ref in (payload.get("question_refs") or {}).items():
        qid = _uuid(ref.get("id", key))
        question_refs[qid] = QuestionRef(
            id=qid,
            text=ref["text"],
            category=ref.get("category"),
        )

    pending = payload.get("pending_question_id")
    last_answered = payload.get("last_answered_question_id")
    activity = payload.get("last_activity_at")
    if isinstance(activity, str):
        last_activity_at = datetime.fromisoformat(activity)
        if last_activity_at.tzinfo is None:
            last_activity_at = last_activity_at.replace(tzinfo=timezone.utc)
    else:
        last_activity_at = datetime.now(timezone.utc)

    popularity_raw = payload.get("character_popularity") or {}
    return LiveSession(
        session_id=_uuid(payload["session_id"]),
        engine=engine,
        question_refs=question_refs,
        character_names={
            _uuid(cid): name for cid, name in (payload.get("character_names") or {}).items()
        },
        character_categories={
            _uuid(cid): cat
            for cid, cat in (payload.get("character_categories") or {}).items()
        },
        character_popularity={
            _uuid(cid): int(score) for cid, score in popularity_raw.items()
        },
        all_question_ids=[_uuid(qid) for qid in payload.get("all_question_ids") or []],
        pending_question_id=_uuid(pending) if pending else None,
        last_answered_question_id=_uuid(last_answered) if last_answered else None,
        awaiting_guess=bool(payload.get("awaiting_guess")),
        answers=[
            StoredAnswer(question_id=_uuid(a["question_id"]), answer=a["answer"])
            for a in payload.get("answers") or []
        ],
        last_activity_at=last_activity_at,
    )
