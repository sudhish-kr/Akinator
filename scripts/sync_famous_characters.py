"""Patch seed + DB with famous characters and popularity scores.

Does not modify Bayesian / learning / session code.

Usage:
    python scripts/sync_famous_characters.py
    python scripts/sync_famous_characters.py --seed-only
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

from character_popularity import (  # noqa: E402
    REQUIRED_FAMOUS_CHARACTERS,
    popularity_for,
)

SEED_PATH = ROOT / "data" / "knowledge" / "seed_v1.json"


def _norm(value: str) -> str:
    return value.strip().casefold()


def patch_seed(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    characters = data.get("characters") or []
    by_name = {_norm(c["name"]): c for c in characters}
    added = 0
    updated = 0

    for name, category, aliases in REQUIRED_FAMOUS_CHARACTERS:
        key = _norm(name)
        score = popularity_for(name)
        if key in by_name:
            row = by_name[key]
            if row.get("popularity_score") != score:
                row["popularity_score"] = score
                updated += 1
            existing_aliases = list(row.get("aliases") or [])
            alias_keys = {_norm(a) for a in existing_aliases}
            for alias in aliases:
                if _norm(alias) not in alias_keys and _norm(alias) != key:
                    existing_aliases.append(alias)
                    alias_keys.add(_norm(alias))
                    updated += 1
            row["aliases"] = existing_aliases
            # Fix truncated Spider-Man alias if present
            if name == "Spider-Man":
                row["aliases"] = [
                    a for a in row["aliases"] if _norm(a) not in {"spider-m"}
                ] + [a for a in aliases if _norm(a) not in {_norm(x) for x in row["aliases"]}]
        else:
            characters.append(
                {
                    "name": name,
                    "category": category,
                    "aliases": aliases,
                    "is_active": True,
                    "popularity_score": score,
                }
            )
            by_name[key] = characters[-1]
            added += 1

    # Apply popularity to any known names already in the seed.
    for row in characters:
        score = popularity_for(row["name"])
        if score and row.get("popularity_score") != score:
            row["popularity_score"] = score
            updated += 1
        elif "popularity_score" not in row:
            row["popularity_score"] = score

    data["characters"] = characters
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"added": added, "updated": updated, "total": len(characters)}


async def sync_database() -> dict[str, int]:
    from sqlalchemy import select
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.config import settings
    from app.db.models import Character, CharacterAlias
    from app.db.repositories.game_repository import GameRepository

    engine = create_async_engine(settings.database_url, echo=False)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    try:
        async with session_factory() as db:
            repo = GameRepository(db)
            existing = (await db.execute(select(Character))).scalars().all()
            by_name = {_norm(c.name): c for c in existing}
            alias_rows = (await db.execute(select(CharacterAlias))).scalars().all()
            alias_keys = {_norm(a.alias) for a in alias_rows}

            created = 0
            scored = 0
            aliases_added = 0
            for name, category, aliases in REQUIRED_FAMOUS_CHARACTERS:
                key = _norm(name)
                score = popularity_for(name)
                if key not in by_name:
                    character = await repo.create_character(
                        name=name,
                        category=category,
                        is_active=True,
                        popularity_score=score,
                    )
                    by_name[key] = character
                    created += 1
                else:
                    character = by_name[key]
                    if getattr(character, "popularity_score", 0) != score:
                        character.popularity_score = score
                        scored += 1
                for alias in aliases:
                    ak = _norm(alias)
                    if ak in alias_keys or ak == key:
                        continue
                    await repo.create_alias(character.id, alias)
                    alias_keys.add(ak)
                    aliases_added += 1

            # Score remaining known popular names.
            for character in by_name.values():
                score = popularity_for(character.name)
                if score and getattr(character, "popularity_score", 0) != score:
                    character.popularity_score = score
                    scored += 1

            await db.commit()
            return {
                "created": created,
                "scored": scored,
                "aliases_added": aliases_added,
            }
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed-only", action="store_true")
    parser.add_argument("--path", type=Path, default=SEED_PATH)
    args = parser.parse_args()

    seed_stats = patch_seed(args.path)
    print(f"Seed {args.path}: {seed_stats}")
    if not args.seed_only:
        db_stats = asyncio.run(sync_database())
        print(f"Database: {db_stats}")


if __name__ == "__main__":
    main()
