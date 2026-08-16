"""Idempotent import of MindGuess character knowledge into the configured database.

Uses the existing schema (characters, aliases, questions, character_answers) and
the curated seed at data/knowledge/seed_v1.json. Existing rows are preserved.
Re-running does not create duplicate characters, aliases, questions, or mappings.

Usage:
    python scripts/import_character_data.py
    python scripts/import_character_data.py --dry-run
    python scripts/import_character_data.py --path data/knowledge/seed_v1.json
    python scripts/import_character_data.py --verify-only

Connection: DATABASE_URL from the environment / .env. Never pass or log secrets.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Character, CharacterAlias, CharacterAnswer, Question
from app.db.url import normalize_asyncpg_url
from app.services.knowledge_seed import KnowledgeSeedError, load_seed_file, validate_seed_payload

DEFAULT_SEED = ROOT / "data" / "knowledge" / "seed_v1.json"
BATCH_SIZE = 2000
VERIFY_NAMES = [
    "Virat Kohli",
    "Sania Mirza",
    "Smriti Mandhana",
    "Shah Rukh Khan",
    "Narendra Modi",
    "Lionel Messi",
    "Batman",
    "Naruto",
    "Goku",
]
INDIA_QUESTION = "Is your character from India?"
INDIA_YES_THRESHOLD = 0.7
# Category rules closer than this to 0.5 are omitted; the engine already defaults to 0.5.
RULE_LINK_THRESHOLD = 0.15
EXPECTED_INDIAN = {
    "virat kohli",
    "sania mirza",
    "smriti mandhana",
    "shah rukh khan",
    "narendra modi",
}
EXPECTED_NOT_INDIAN = {"lionel messi", "batman", "naruto", "goku"}


def _norm(value: str) -> str:
    return " ".join(value.strip().split()).casefold()


def describe_database(url: str) -> str:
    """Host/database only — never include user or password."""
    parsed = urlparse(url.replace("postgresql+asyncpg://", "postgresql://", 1))
    db = (parsed.path or "/").lstrip("/").split("?")[0] or "(none)"
    host = parsed.hostname or "local"
    scheme = "sqlite" if (parsed.scheme or "").startswith("sqlite") else "postgres"
    return f"{scheme}://{host}/{db}"


def async_engine_url(url: str) -> tuple[str, dict[str, Any]]:
    """Convert a Postgres URL for asyncpg. Drops libpq-only query params."""
    return normalize_asyncpg_url(url)


def estimate_mapping_count(data: dict[str, Any]) -> int:
    """Distinct (character, question) pairs the seed would write."""
    active_qs = {
        _norm(q["text"])
        for q in data.get("questions") or []
        if bool(q.get("is_active", True))
    }
    rules = data.get("likelihood_rules") or []
    overrides = data.get("likelihood_overrides") or []
    by_cat: dict[str, set[str]] = {}
    for rule in rules:
        q_norm = _norm(rule["question"])
        if q_norm not in active_qs:
            continue
        if abs(float(rule["likelihood"]) - 0.5) < RULE_LINK_THRESHOLD:
            continue
        by_cat.setdefault(_norm(rule["category"]), set()).add(q_norm)
    pairs: set[tuple[str, str]] = set()
    for item in data.get("characters") or []:
        for q in by_cat.get(_norm(item["category"]), ()):
            pairs.add((_norm(item["name"]), q))
    for ov in overrides:
        q_norm = _norm(ov["question"])
        if q_norm not in active_qs:
            continue
        pairs.add((_norm(ov["character"]), q_norm))
    return len(pairs)


def seed_character_records(characters: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], int]:
    """Normalize, drop unusable rows, and collapse duplicate names (first wins)."""
    skipped = 0
    seen: dict[str, dict[str, Any]] = {}
    for item in characters:
        if not isinstance(item, dict):
            skipped += 1
            continue
        name = " ".join(str(item.get("name") or "").split())
        category = " ".join(str(item.get("category") or "").split())
        if not name or not category:
            skipped += 1
            continue
        key = _norm(name)
        if key in seen:
            skipped += 1
            continue
        aliases: list[str] = []
        alias_seen: set[str] = {key}
        for raw in item.get("aliases") or []:
            alias = " ".join(str(raw).split())
            if not alias or _norm(alias) in alias_seen:
                continue
            alias_seen.add(_norm(alias))
            aliases.append(alias)
        seen[key] = {
            "name": name,
            "category": category,
            "image_url": item.get("image_url"),
            "is_active": bool(item.get("is_active", True)),
            "popularity_score": int(item.get("popularity_score") or 0),
            "aliases": aliases,
        }
    return list(seen.values()), skipped


def likelihood_pairs(
    data: dict[str, Any],
    char_by_name: dict[str, Character],
    q_by_text: dict[str, Question],
) -> list[tuple[Any, Any, float, int]]:
    """Build (character_id, question_id, likelihood, sample_size) from seed only.

    Only active questions are mapped. Category rules near 0.5 are omitted
    because the engine already treats a missing pair as 0.5. Per-character
    overrides are always written (they are curated facts).
    """
    active_q = {key: q for key, q in q_by_text.items() if q.is_active}
    default_sample = int(data.get("default_sample_size", 10))
    rules_index: dict[str, dict[str, tuple[float, int]]] = {}
    for rule in data.get("likelihood_rules") or []:
        q_norm = _norm(rule["question"])
        if q_norm not in active_q:
            continue
        lik = float(rule["likelihood"])
        if abs(lik - 0.5) < RULE_LINK_THRESHOLD:
            continue
        cat = _norm(rule["category"])
        sample = int(rule.get("sample_size", default_sample))
        rules_index.setdefault(cat, {})[q_norm] = (lik, sample)

    pair_values: dict[tuple[Any, Any], tuple[float, int]] = {}
    seed_chars = data.get("characters") or []
    for item in seed_chars:
        character = char_by_name.get(_norm(item["name"]))
        if character is None:
            continue
        for q_norm, (lik, sample) in rules_index.get(_norm(item["category"]), {}).items():
            question = active_q[q_norm]
            pair_values[(character.id, question.id)] = (lik, sample)

    for ov in data.get("likelihood_overrides") or []:
        character = char_by_name.get(_norm(ov["character"]))
        question = active_q.get(_norm(ov["question"]))
        if character is None or question is None:
            continue
        sample = int(ov.get("sample_size", default_sample))
        pair_values[(character.id, question.id)] = (float(ov["likelihood"]), sample)

    return [(cid, qid, lik, sample) for (cid, qid), (lik, sample) in pair_values.items()]


def _insert_answers():
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    from sqlalchemy.dialects.sqlite import insert as sqlite_insert

    return pg_insert, sqlite_insert


async def _load_index(db: AsyncSession) -> tuple[dict[str, Character], set[str], dict[str, Question]]:
    characters = (await db.execute(select(Character))).scalars().all()
    aliases = (await db.execute(select(CharacterAlias))).scalars().all()
    questions = (await db.execute(select(Question))).scalars().all()
    by_name = {_norm(c.name): c for c in characters}
    taken = set(by_name)
    for alias in aliases:
        taken.add(_norm(alias.alias))
    q_by_text = {_norm(q.text): q for q in questions}
    return by_name, taken, q_by_text


async def import_seed(path: Path, *, dry_run: bool, replace_mappings: bool = False) -> dict[str, int]:
    data = load_seed_file(path)
    validate_seed_payload(data)

    prepared, duplicates_skipped = seed_character_records(data["characters"])
    engine_url, connect_args = async_engine_url(settings.database_url)
    engine = create_async_engine(engine_url, echo=False, connect_args=connect_args)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    stats = {
        "source_characters": len(data["characters"]),
        "source_questions": len(data["questions"]),
        "prepared_characters": len(prepared),
        "duplicates_removed": duplicates_skipped,
        "characters_imported": 0,
        "characters_skipped": 0,
        "aliases_imported": 0,
        "questions_imported": 0,
        "questions_skipped": 0,
        "mappings_created": 0,
        "mappings_skipped": 0,
        "existing_characters": 0,
        "mappings_replaced": 0,
        "dry_run": int(dry_run),
    }

    try:
        async with session_factory() as db:
            by_name, taken, q_by_text = await _load_index(db)
            stats["existing_characters"] = len(by_name)

            for i, item in enumerate(prepared, start=1):
                key = _norm(item["name"])
                if key in by_name:
                    stats["characters_skipped"] += 1
                    character = by_name[key]
                elif key in taken:
                    stats["characters_skipped"] += 1
                    continue
                else:
                    if dry_run:
                        stats["characters_imported"] += 1
                        character = None
                    else:
                        character = Character(
                            id=uuid4(),
                            name=item["name"],
                            category=item["category"],
                            image_url=item.get("image_url"),
                            is_active=item["is_active"],
                            popularity_score=item["popularity_score"],
                        )
                        db.add(character)
                        by_name[key] = character
                        taken.add(key)
                        stats["characters_imported"] += 1

                for alias in item["aliases"]:
                    alias_key = _norm(alias)
                    if alias_key in taken:
                        continue
                    if dry_run:
                        stats["aliases_imported"] += 1
                        taken.add(alias_key)
                        continue
                    if character is None:
                        continue
                    db.add(
                        CharacterAlias(id=uuid4(), character_id=character.id, alias=alias)
                    )
                    taken.add(alias_key)
                    stats["aliases_imported"] += 1

                if not dry_run and i % 200 == 0:
                    await db.flush()
                    print(f"  characters processed {i}/{len(prepared)}", flush=True)

            for i, item in enumerate(data["questions"], start=1):
                text = " ".join(str(item["text"]).split())
                key = _norm(text)
                if key in q_by_text:
                    stats["questions_skipped"] += 1
                    continue
                if dry_run:
                    stats["questions_imported"] += 1
                    continue
                ig = item.get("avg_information_gain", item.get("initial_information_gain"))
                question = Question(
                    id=uuid4(),
                    text=text,
                    category=str(item["category"]).strip(),
                    is_active=bool(item.get("is_active", True)),
                    times_asked=int(item.get("times_asked", 0)),
                    avg_information_gain=float(ig) if ig is not None else None,
                )
                db.add(question)
                q_by_text[key] = question
                stats["questions_imported"] += 1
                if i % 200 == 0:
                    print(f"  questions processed {i}/{len(data['questions'])}", flush=True)

            if not dry_run:
                await db.commit()
                by_name, taken, q_by_text = await _load_index(db)

            if replace_mappings and not dry_run:
                deleted = await db.execute(delete(CharacterAnswer))
                stats["mappings_replaced"] = int(deleted.rowcount or 0)
                await db.commit()
                print(
                    f"  cleared character_answers ({stats['mappings_replaced']} rows)",
                    flush=True,
                )

            if dry_run:
                stats["mappings_created"] = estimate_mapping_count(data)
                return stats

            pairs = likelihood_pairs(data, by_name, q_by_text)

            existing_result = await db.execute(
                select(CharacterAnswer.character_id, CharacterAnswer.question_id)
            )
            existing = {(cid, qid) for cid, qid in existing_result.all()}
            new_rows = [p for p in pairs if (p[0], p[1]) not in existing]
            stats["mappings_skipped"] = len(pairs) - len(new_rows)

            dialect = engine.dialect.name
            pg_insert, sqlite_insert = _insert_answers()
            insert_fn = sqlite_insert if dialect == "sqlite" else pg_insert

            total = len(new_rows)
            if total == 0:
                return stats
            for start in range(0, total, BATCH_SIZE):
                chunk = new_rows[start : start + BATCH_SIZE]
                values = [
                    {
                        "id": uuid4(),
                        "character_id": cid,
                        "question_id": qid,
                        "likelihood": lik,
                        "sample_size": sample,
                    }
                    for cid, qid, lik, sample in chunk
                ]
                stmt = insert_fn(CharacterAnswer).values(values)
                stmt = stmt.on_conflict_do_nothing(
                    index_elements=["character_id", "question_id"]
                )
                await db.execute(stmt)
                await db.commit()
                stats["mappings_created"] += len(chunk)
                done = min(start + BATCH_SIZE, total)
                if done == total or done % 5000 < BATCH_SIZE:
                    print(f"  mappings inserted {done}/{total}", flush=True)

            return stats
    finally:
        await engine.dispose()


async def verify_catalog() -> dict[str, Any]:
    engine_url, connect_args = async_engine_url(settings.database_url)
    engine = create_async_engine(engine_url, echo=False, connect_args=connect_args)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    report: dict[str, Any] = {"found": {}, "india": {}, "counts": {}}
    try:
        async with session_factory() as db:
            report["counts"] = {
                "characters": int(
                    (await db.execute(select(func.count()).select_from(Character))).scalar_one()
                ),
                "questions": int(
                    (await db.execute(select(func.count()).select_from(Question))).scalar_one()
                ),
                "mappings": int(
                    (
                        await db.execute(select(func.count()).select_from(CharacterAnswer))
                    ).scalar_one()
                ),
            }
            for name in VERIFY_NAMES:
                key = _norm(name)
                character = (
                    await db.execute(select(Character).where(func.lower(Character.name) == key))
                ).scalar_one_or_none()
                if character is None:
                    alias = (
                        await db.execute(
                            select(CharacterAlias).where(func.lower(CharacterAlias.alias) == key)
                        )
                    ).scalar_one_or_none()
                    if alias is not None:
                        character = await db.get(Character, alias.character_id)
                report["found"][name] = None if character is None else {
                    "name": character.name,
                    "category": character.category,
                }

            india_q = (
                await db.execute(select(Question).where(Question.text == INDIA_QUESTION))
            ).scalar_one_or_none()
            if india_q is None:
                report["india"]["question"] = "missing"
                return report
            report["india"]["question"] = india_q.text

            names = [info["name"] for info in report["found"].values() if info]
            if not names:
                return report
            rows = (
                await db.execute(
                    select(Character.name, CharacterAnswer.likelihood)
                    .join(CharacterAnswer, CharacterAnswer.character_id == Character.id)
                    .where(
                        CharacterAnswer.question_id == india_q.id,
                        or_(*[Character.name == n for n in names]),
                    )
                )
            ).all()
            india_map = {name: float(lik) for name, lik in rows}
            report["india"]["by_character"] = india_map
            report["india"]["expected_indian_ok"] = all(
                india_map.get(name, 0) >= INDIA_YES_THRESHOLD
                for name, info in report["found"].items()
                if info and _norm(name) in EXPECTED_INDIAN
            )
            report["india"]["expected_foreign_ok"] = all(
                india_map.get(info["name"], 1.0) < INDIA_YES_THRESHOLD
                for name, info in report["found"].items()
                if info and _norm(name) in EXPECTED_NOT_INDIAN
            )
            return report
    finally:
        await engine.dispose()


def _print_stats(stats: dict[str, int]) -> None:
    mode = "dry-run" if stats.get("dry_run") else "imported"
    print(f"Character data {mode}:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def _print_verify(report: dict[str, Any]) -> None:
    print("Catalog verification:")
    for key, value in report.get("counts", {}).items():
        print(f"  {key}: {value}")
    for name in VERIFY_NAMES:
        info = report["found"].get(name)
        if info:
            print(f"  {name}: found as {info['name']} ({info['category']})")
        else:
            print(f"  {name}: MISSING")
    india = report.get("india") or {}
    print(f"  India question: {india.get('question')}")
    for name, lik in sorted((india.get("by_character") or {}).items()):
        print(f"  India likelihood {name}: {lik:.3f}")
    print(f"  Indian candidates mapped yes: {india.get('expected_indian_ok')}")
    print(f"  Foreign candidates not Indian: {india.get('expected_foreign_ok')}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--path", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--replace-mappings",
        action="store_true",
        help="Delete existing character_answers then insert seed mappings (preserves characters)",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Skip import; query named characters and India mappings",
    )
    args = parser.parse_args()

    print(f"Database: {describe_database(settings.database_url)}")
    print(f"Seed: {args.path}")

    if args.verify_only:
        _print_verify(asyncio.run(verify_catalog()))
        return

    if not args.path.exists():
        print(f"Seed file not found: {args.path}", file=sys.stderr)
        sys.exit(1)

    try:
        stats = asyncio.run(
            import_seed(
                args.path,
                dry_run=args.dry_run,
                replace_mappings=args.replace_mappings,
            )
        )
    except KnowledgeSeedError as exc:
        print(f"Import failed: {exc}", file=sys.stderr)
        sys.exit(1)
    _print_stats(stats)
    if not args.dry_run:
        _print_verify(asyncio.run(verify_catalog()))


if __name__ == "__main__":
    main()
