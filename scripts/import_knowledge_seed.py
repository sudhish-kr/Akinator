"""
Import curated knowledge-base seed data.

Usage:
    alembic upgrade head
    python scripts/generate_knowledge_seed.py   # optional refresh of seed JSON
    python scripts/import_knowledge_seed.py
    python scripts/import_knowledge_seed.py --dry-run
    python scripts/import_knowledge_seed.py --path data/knowledge/seed_v1.json
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.repositories.game_repository import GameRepository
from app.services.knowledge_seed import (
    KnowledgeSeedError,
    KnowledgeSeedService,
    load_seed_file,
)

DEFAULT_SEED = ROOT / "data" / "knowledge" / "seed_v1.json"


async def run(path: Path, dry_run: bool) -> int:
    data = load_seed_file(path)
    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as db:
            repo = GameRepository(db)
            service = KnowledgeSeedService(repo)
            try:
                result = await service.import_seed(data, dry_run=dry_run)
            except KnowledgeSeedError as exc:
                print(f"Import failed: {exc}", file=sys.stderr)
                return 1
    finally:
        await engine.dispose()

    mode = "dry-run" if dry_run else "imported"
    print(
        f"Knowledge seed {mode}: "
        f"{result['characters']} characters, "
        f"{result['aliases']} aliases, "
        f"{result['questions']} questions, "
        f"{result['likelihoods']} likelihood mappings."
    )
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Import MindGuess knowledge-base seed data")
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_SEED,
        help=f"Path to seed JSON (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate only; do not write to the database",
    )
    args = parser.parse_args()
    if not args.path.exists():
        print(f"Seed file not found: {args.path}", file=sys.stderr)
        sys.exit(1)
    raise SystemExit(asyncio.run(run(args.path, args.dry_run)))


if __name__ == "__main__":
    main()
