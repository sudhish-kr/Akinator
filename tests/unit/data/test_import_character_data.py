"""Helpers for the idempotent character import script."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from import_character_data import (  # noqa: E402
    _norm,
    async_engine_url,
    describe_database,
    estimate_mapping_count,
    seed_character_records,
)


def test_norm_trims_and_casefolds():
    assert _norm("  Virat   Kohli ") == "virat kohli"


def test_seed_character_records_drops_duplicates_and_empties():
    rows, skipped = seed_character_records(
        [
            {"name": " Virat Kohli ", "category": "Sports", "aliases": ["Kohli", "kohli"]},
            {"name": "Virat Kohli", "category": "Sports"},
            {"name": "  ", "category": "Sports"},
            {"name": "Lionel Messi", "category": "Sports", "aliases": ["Messi"]},
        ]
    )
    names = [r["name"] for r in rows]
    assert names == ["Virat Kohli", "Lionel Messi"]
    assert skipped == 2
    assert rows[0]["aliases"] == ["Kohli"]


def test_estimate_mapping_count_uses_rules_and_overrides():
    data = {
        "characters": [
            {"name": "A", "category": "Sports"},
            {"name": "B", "category": "Movies"},
        ],
        "questions": [
            {"text": "Is your character from India?", "is_active": True},
            {"text": "Is this a real person?", "is_active": True},
            {"text": "Is your character from Japan?", "is_active": False},
        ],
        "likelihood_rules": [
            {"category": "Sports", "question": "Is your character from India?", "likelihood": 0.2},
            {"category": "Sports", "question": "Is this a real person?", "likelihood": 0.51},
            {"category": "Sports", "question": "Is your character from Japan?", "likelihood": 0.12},
        ],
        "likelihood_overrides": [
            {
                "character": "A",
                "question": "Is your character from India?",
                "likelihood": 0.96,
            },
            {"character": "B", "question": "Is this a real person?", "likelihood": 0.9},
        ],
    }
    assert estimate_mapping_count(data) == 2


def test_describe_database_hides_credentials():
    desc = describe_database(
        "postgresql+asyncpg://owner:secret@ep-example.neon.tech/neondb?sslmode=require"
    )
    assert "secret" not in desc
    assert "owner" not in desc
    assert "neon.tech" in desc


def test_async_engine_url_drops_libpq_params():
    url, args = async_engine_url(
        "postgresql://owner:secret@ep-x-pooler.neon.tech/neondb?sslmode=require&channel_binding=require"
    )
    assert url.startswith("postgresql+asyncpg://")
    assert "sslmode" not in url
    assert "channel_binding" not in url
    assert args.get("ssl") is True
    assert args.get("statement_cache_size") == 0
