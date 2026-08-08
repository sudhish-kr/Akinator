"""Activate curated Question Database v2 in the live DB; deactivate legacy questions.

Does not modify the Bayesian engine or learning code. Soft-deactivates existing
non-v2 questions (is_active=False) and upserts v2 rows as active.

Usage:
    python scripts/sync_questions_v2.py
    python scripts/sync_questions_v2.py --path data/knowledge/seed_v1.json
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Character, Question
from app.db.repositories.game_repository import GameRepository
from app.services.knowledge_seed import KnowledgeSeedError, load_seed_file
from questions_v2_data import DATASET_ID, build_v2_questions

DEFAULT_SEED = ROOT / "data" / "knowledge" / "seed_v1.json"


def _norm(value: str) -> str:
    return value.strip().casefold()


def _resolve_db_path(database_url: str) -> str:
    if "sqlite" in database_url:
        raw = database_url.split(":///", 1)[-1]
        path = Path(raw)
        if not path.is_absolute():
            path = (ROOT / path).resolve()
        return str(path)
    return database_url


def _active_v2_from_seed(path: Path) -> list[dict]:
    if path.exists():
        data = load_seed_file(path)
        questions = [
            q
            for q in (data.get("questions") or [])
            if q.get("is_active") and q.get("dataset", DATASET_ID) == DATASET_ID
        ]
        if questions:
            return questions
    return build_v2_questions()


async def sync_questions(path: Path) -> dict[str, int]:
    v2_questions = _active_v2_from_seed(path)
    if len(v2_questions) < 200:
        raise KnowledgeSeedError(f"Expected >= 200 v2 questions; got {len(v2_questions)}")

    v2_by_text = {_norm(q["text"]): q for q in v2_questions}
    v2_texts = set(v2_by_text)

    seed_rules: list[dict] = []
    if path.exists():
        seed = load_seed_file(path)
        seed_rules = list(seed.get("likelihood_rules") or [])

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as db:
            repo = GameRepository(db)
            existing = (await db.execute(select(Question))).scalars().all()
            by_text = {_norm(q.text): q for q in existing}

            deactivated = 0
            for question in existing:
                if _norm(question.text) not in v2_texts and question.is_active:
                    question.is_active = False
                    deactivated += 1

            created = 0
            reactivated = 0
            updated = 0
            for key, item in v2_by_text.items():
                ig = item.get("avg_information_gain", item.get("initial_information_gain"))
                if key in by_text:
                    row = by_text[key]
                    changed = False
                    if not row.is_active:
                        row.is_active = True
                        reactivated += 1
                        changed = True
                    if row.category != item["category"]:
                        row.category = item["category"]
                        changed = True
                    if ig is not None and row.avg_information_gain != float(ig):
                        row.avg_information_gain = float(ig)
                        changed = True
                    if changed:
                        updated += 1
                else:
                    await repo.create_question(
                        text=item["text"].strip(),
                        category=str(item["category"]).strip(),
                        is_active=True,
                        times_asked=int(item.get("times_asked", 0)),
                        avg_information_gain=float(ig) if ig is not None else None,
                    )
                    created += 1

            await db.flush()

            # Refresh likelihood rows for active v2 questions when seed rules exist.
            likelihoods_written = 0
            if seed_rules:
                questions = (await db.execute(select(Question))).scalars().all()
                q_by_text = {_norm(q.text): q for q in questions if q.is_active}
                characters = (await db.execute(select(Character))).scalars().all()
                chars_by_cat: dict[str, list[Character]] = {}
                for character in characters:
                    if not character.is_active:
                        continue
                    chars_by_cat.setdefault(_norm(character.category), []).append(character)

                default_sample = 40
                for rule in seed_rules:
                    q = q_by_text.get(_norm(rule["question"]))
                    if q is None:
                        continue
                    for character in chars_by_cat.get(_norm(rule["category"]), ()):
                        await repo.upsert_character_answer(
                            character.id,
                            q.id,
                            float(rule["likelihood"]),
                            int(rule.get("sample_size", default_sample)),
                        )
                        likelihoods_written += 1

            await db.commit()

            active_count = (
                await db.execute(
                    select(Question).where(Question.is_active.is_(True))
                )
            ).scalars().all()
            inactive_count = (
                await db.execute(
                    select(Question).where(Question.is_active.is_(False))
                )
            ).scalars().all()

            return {
                "v2_source": len(v2_questions),
                "created": created,
                "reactivated": reactivated,
                "updated": updated,
                "deactivated": deactivated,
                "active": len(active_count),
                "inactive": len(inactive_count),
                "likelihoods_written": likelihoods_written,
            }
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_SEED)
    args = parser.parse_args()

    print(f"Database: {_resolve_db_path(settings.database_url)}")
    print(f"Seed: {args.path}")
    result = asyncio.run(sync_questions(args.path))
    for key, value in result.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
