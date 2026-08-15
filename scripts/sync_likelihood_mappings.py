"""Sync character↔question likelihood mappings from the knowledge seed.

Uses KnowledgeSeedService.sync_active_likelihoods — the same seed rules /
overrides as import_knowledge_seed / sync_questions_v2. Does not recreate the
database or delete characters/questions.

Usage:
    python scripts/sync_likelihood_mappings.py
    python scripts/sync_likelihood_mappings.py --dry-run
    python scripts/sync_likelihood_mappings.py --path data/knowledge/seed_v1.json
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

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.repositories.game_repository import GameRepository
from app.services.knowledge_seed import (
    KnowledgeSeedError,
    KnowledgeSeedService,
    load_seed_file,
)
from sync_famous_characters import sync_database as sync_famous_characters

DEFAULT_SEED = ROOT / "data" / "knowledge" / "seed_v1.json"


def _resolve_db_path(database_url: str) -> str:
    if "sqlite" in database_url:
        raw = database_url.split(":///", 1)[-1]
        path = Path(raw)
        if not path.is_absolute():
            path = (ROOT / path).resolve()
        return str(path)
    return database_url


async def run(path: Path, dry_run: bool, skip_famous: bool) -> int:
    if not skip_famous and not dry_run:
        famous_stats = await sync_famous_characters()
        print(f"Famous characters: {famous_stats}")

    data = load_seed_file(path)
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as db:
            service = KnowledgeSeedService(GameRepository(db))
            try:
                result = await service.sync_active_likelihoods(
                    data, align_categories=True, dry_run=dry_run
                )
            except KnowledgeSeedError as exc:
                print(f"Sync failed: {exc}", file=sys.stderr)
                return 1
    finally:
        await engine.dispose()

    mode = "dry-run" if dry_run else "synced"
    print(f"Likelihood mappings {mode}:")
    for key, value in result.items():
        print(f"  {key}: {value}")
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--skip-famous",
        action="store_true",
        help="Do not upsert famous characters before syncing likelihoods",
    )
    args = parser.parse_args()
    if not args.path.exists():
        print(f"Seed file not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    print(f"Database: {_resolve_db_path(settings.database_url)}")
    print(f"Seed: {args.path}")
    raise SystemExit(asyncio.run(run(args.path, args.dry_run, args.skip_famous)))


if __name__ == "__main__":
    main()
