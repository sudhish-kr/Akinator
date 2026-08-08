"""Famous characters + popularity for natural gameplay."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
SEED_PATH = ROOT / "data" / "knowledge" / "seed_v1.json"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from character_popularity import REQUIRED_FAMOUS_CHARACTERS, popularity_for  # noqa: E402


def test_required_famous_characters_exist_with_aliases_and_popularity():
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    by_name = {c["name"].casefold(): c for c in seed["characters"]}
    for name, category, aliases in REQUIRED_FAMOUS_CHARACTERS:
        row = by_name.get(name.casefold())
        assert row is not None, f"Missing famous character: {name}"
        assert row["category"] == category
        assert row.get("is_active", True) is True
        assert int(row.get("popularity_score", 0)) >= popularity_for(name)
        have = {a.casefold() for a in (row.get("aliases") or [])}
        for alias in aliases:
            assert alias.casefold() in have or alias.casefold() == name.casefold(), (
                name,
                alias,
            )


def test_regression_icons_are_high_priority():
    for name in [
        "Virat Kohli",
        "Lionel Messi",
        "Shah Rukh Khan",
        "Naruto Uzumaki",
        "Batman",
    ]:
        assert popularity_for(name) >= 90
