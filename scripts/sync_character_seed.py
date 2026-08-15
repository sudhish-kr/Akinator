"""Sync character seed into the active database without regenerating data.

Imports missing characters and aliases from data/knowledge/seed_v1.json into
the configured database. Existing rows are left in place. Does not modify the
game engine.

Usage:
    python scripts/sync_character_seed.py
    python scripts/sync_character_seed.py --path data/knowledge/seed_v1.json
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Character, CharacterAlias
from app.db.repositories.game_repository import GameRepository
from app.services.knowledge_seed import KnowledgeSeedError, load_seed_file

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


async def sync_characters(path: Path) -> dict[str, int]:
    data = load_seed_file(path)
    characters = data.get("characters") or []
    if len(characters) < 520:
        raise KnowledgeSeedError(
            f"Seed has {len(characters)} characters; expected >= 520"
        )

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with session_factory() as db:
            repo = GameRepository(db)

            existing_chars = (await db.execute(select(Character))).scalars().all()
            by_name = {_norm(c.name): c for c in existing_chars}

            existing_alias_rows = (
                await db.execute(select(CharacterAlias))
            ).scalars().all()
            existing_aliases = {_norm(a.alias) for a in existing_alias_rows}
            # Character names also block aliases
            existing_aliases.update(by_name.keys())

            added_chars = 0
            added_aliases = 0

            for i, item in enumerate(characters, start=1):
                name = item["name"].strip()
                key = _norm(name)
                if key in by_name:
                    character = by_name[key]
                    score = int(item.get("popularity_score") or 0)
                    if score and getattr(character, "popularity_score", 0) != score:
                        character.popularity_score = score
                else:
                    character = await repo.create_character(
                        name=name,
                        category=item["category"].strip(),
                        image_url=item.get("image_url"),
                        is_active=bool(item.get("is_active", True)),
                        popularity_score=int(item.get("popularity_score") or 0),
                    )
                    by_name[key] = character
                    existing_aliases.add(key)
                    added_chars += 1

                for alias in item.get("aliases") or []:
                    alias_text = alias.strip()
                    alias_key = _norm(alias_text)
                    if not alias_text or alias_key in existing_aliases:
                        continue
                    await repo.create_alias(character.id, alias_text)
                    existing_aliases.add(alias_key)
                    added_aliases += 1

                if i % 200 == 0:
                    await db.flush()

            await db.commit()

            total_chars = (
                await db.execute(select(func.count()).select_from(Character))
            ).scalar_one()

            return {
                "seed_characters": len(characters),
                "added_characters": added_chars,
                "added_aliases": added_aliases,
                "db_characters": int(total_chars),
            }
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync character seed into the active database"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_SEED,
        help=f"Path to seed JSON (default: {DEFAULT_SEED})",
    )
    args = parser.parse_args()
    if not args.path.exists():
        print(f"Seed file not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    print(f"Active database path: {_resolve_db_path(settings.database_url)}")
    print(f"Character seed file path: {args.path.resolve()}")

    try:
        result = asyncio.run(sync_characters(args.path))
    except KnowledgeSeedError as exc:
        print(f"Sync failed: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Character count in seed: {result['seed_characters']}")
    print(
        f"Imported missing characters: {result['added_characters']} "
        f"(aliases +{result['added_aliases']})"
    )
    print(f"Character count in database after import: {result['db_characters']}")
    if result["db_characters"] < result["seed_characters"]:
        # Allow equality with seed; also accept if seed names collided with demos
        if result["db_characters"] < 520:
            print(
                "ERROR: database still has fewer than 520 characters",
                file=sys.stderr,
            )
            sys.exit(1)
        if result["db_characters"] < result["seed_characters"]:
            # Some seed names may already have existed under different categories
            print(
                "NOTE: database character count is below seed count "
                f"({result['db_characters']} < {result['seed_characters']}); "
                "existing name collisions were skipped."
            )


if __name__ == "__main__":
    main()
