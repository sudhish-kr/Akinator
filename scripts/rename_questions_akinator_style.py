"""Rename live DB questions to Akinator-style text IN PLACE (same UUID).

Preserves character_answers likelihood rows. Run after regenerating the seed:

    python scripts/generate_knowledge_seed.py
    python scripts/rename_questions_akinator_style.py
    python scripts/sync_questions_v2.py
    python scripts/sync_likelihood_mappings.py
"""

from __future__ import annotations

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

from akinator_style_rewrites import rewrite_map, to_akinator_style
from app.config import settings
from app.db.models import Question
from questions_v2_data import _QUESTIONS, build_v2_questions


def _norm(value: str) -> str:
    return value.strip().casefold()


async def main() -> None:
    # Map every source/legacy text we still know about → new Akinator text.
    source_texts = [row[0] for row in _QUESTIONS]
    mapping = rewrite_map(source_texts)
    # Also accept already-rewritten texts (idempotent).
    for q in build_v2_questions():
        mapping.setdefault(q["text"], q["text"])
        legacy = q.get("legacy_text")
        if legacy:
            mapping[legacy] = q["text"]

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    renamed = 0
    skipped = 0
    collisions = 0
    async with session_factory() as db:
        rows = (await db.execute(select(Question))).scalars().all()
        by_new = {_norm(q.text): q for q in rows}

        for row in rows:
            target = mapping.get(row.text) or to_akinator_style(row.text)
            if _norm(target) == _norm(row.text):
                skipped += 1
                continue
            existing = by_new.get(_norm(target))
            if existing is not None and existing.id != row.id:
                # Prefer keeping the active/newer wording row; deactivate duplicate source.
                row.is_active = False
                collisions += 1
                continue
            row.text = target
            by_new[_norm(target)] = row
            renamed += 1

        await db.commit()

    await engine.dispose()
    print(
        f"akinator rename complete: renamed={renamed} skipped={skipped} "
        f"collisions_deactivated={collisions}"
    )


if __name__ == "__main__":
    asyncio.run(main())
