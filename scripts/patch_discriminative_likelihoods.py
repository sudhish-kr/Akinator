"""Rebuild discriminative likelihood rules + character overrides, sync DB.

Usage:
    python scripts/patch_discriminative_likelihoods.py
    python scripts/patch_discriminative_likelihoods.py --seed-only
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from character_trait_priors import build_all_overrides  # noqa: E402
from likelihood_priors import assert_mapping_quality, build_likelihood_rules  # noqa: E402

SEED_PATH = ROOT / "data" / "knowledge" / "seed_v1.json"


def _norm(value: str) -> str:
    return value.strip().casefold()


def patch_seed(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    characters = data.get("characters") or []
    questions = data.get("questions") or []
    rules = build_likelihood_rules(questions, sample_size=int(data.get("default_sample_size") or 40))
    assert_mapping_quality(characters, questions, rules, min_per_character=40)

    generated = build_all_overrides(characters, questions, sample_size=80)
    # Keep any existing overrides that are not superseded by generated ones.
    merged: dict[tuple[str, str], dict] = {}
    for ov in data.get("likelihood_overrides") or []:
        merged[(_norm(ov["character"]), _norm(ov["question"]))] = ov
    for ov in generated:
        merged[(_norm(ov["character"]), _norm(ov["question"]))] = ov

    data["likelihood_rules"] = rules
    data["likelihood_overrides"] = [merged[k] for k in sorted(merged)]
    data["mapping_phase"] = int(data.get("mapping_phase") or 1) + 1
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "characters": len(characters),
        "questions": len(questions),
        "rules": len(rules),
        "overrides": len(data["likelihood_overrides"]),
    }


async def sync_db(path: Path) -> dict[str, int]:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import settings
    from app.db.repositories.game_repository import GameRepository
    from app.services.knowledge_seed import KnowledgeSeedService, load_seed_file
    from app.services.playable_catalog import invalidate_playable_catalog

    data = load_seed_file(path)
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as db:
            service = KnowledgeSeedService(GameRepository(db))
            result = await service.sync_active_likelihoods(
                data, align_categories=True, dry_run=False
            )
            await db.commit()
    finally:
        await engine.dispose()
    invalidate_playable_catalog()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-only", action="store_true")
    parser.add_argument("--path", type=Path, default=SEED_PATH)
    args = parser.parse_args()

    stats = patch_seed(args.path)
    print("Seed patched:", stats)
    if args.seed_only:
        return 0
    db_stats = asyncio.run(sync_db(args.path))
    print("DB synced:", db_stats)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
