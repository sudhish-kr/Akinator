"""Regression tests for the expanded global character knowledge base."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
SEED_PATH = ROOT / "data" / "knowledge" / "seed_v1.json"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from character_popularity import REQUIRED_FAMOUS_CHARACTERS, popularity_for  # noqa: E402
from character_trait_priors import traits_for  # noqa: E402

REGRESSION_NAMES = [
    "Virat Kohli",
    "MS Dhoni",
    "Smriti Mandhana",
    "Sania Mirza",
    "Sachin Tendulkar",
    "Lionel Messi",
    "Cristiano Ronaldo",
    "Shah Rukh Khan",
    "Narendra Modi",
    "Albert Einstein",
    "Isaac Newton",
    "Harry Potter",
    "Spider-Man",
    "Iron Man",
    "Batman",
    "Naruto",
    "Goku",
    "Doraemon",
    "Shinchan",
    "Mario",
    "Sonic",
]


def _index_seed(seed: dict) -> tuple[dict[str, dict], dict[str, str]]:
    by_name = {c["name"].casefold(): c for c in seed["characters"]}
    alias_to_name: dict[str, str] = {}
    for c in seed["characters"]:
        alias_to_name[c["name"].casefold()] = c["name"]
        for alias in c.get("aliases") or []:
            alias_to_name[alias.casefold()] = c["name"]
    return by_name, alias_to_name


@pytest.fixture(scope="module")
def seed():
    assert SEED_PATH.exists()
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def lookup(seed):
    return _index_seed(seed)


def _resolve(lookup, name: str) -> dict:
    by_name, alias_to_name = lookup
    canonical = alias_to_name.get(name.casefold())
    assert canonical, f"Missing character or alias: {name}"
    return by_name[canonical.casefold()]


def test_regression_icons_exist_with_category_and_aliases(lookup):
    expected_cat = {
        "Virat Kohli": "Sports",
        "MS Dhoni": "Sports",
        "Smriti Mandhana": "Sports",
        "Sania Mirza": "Sports",
        "Sachin Tendulkar": "Sports",
        "Lionel Messi": "Sports",
        "Cristiano Ronaldo": "Sports",
        "Shah Rukh Khan": "Movies",
        "Narendra Modi": "Politicians",
        "Albert Einstein": "Scientists",
        "Isaac Newton": "Scientists",
        "Harry Potter": "Movies",
        "Spider-Man": "Movies",
        "Iron Man": "Movies",
        "Batman": "Movies",
        "Naruto": "Anime",
        "Goku": "Anime",
        "Doraemon": "Cartoons",
        "Shinchan": "Cartoons",
        "Mario": "Gaming",
        "Sonic": "Gaming",
    }
    for name in REGRESSION_NAMES:
        row = _resolve(lookup, name)
        assert row.get("is_active", True) is True
        assert row["category"] == expected_cat[name], (name, row["category"])
        assert popularity_for(row["name"]) >= 80 or popularity_for(name) >= 80


def test_required_famous_characters_have_aliases(lookup):
    for name, category, aliases in REQUIRED_FAMOUS_CHARACTERS:
        row = _resolve(lookup, name)
        assert row["category"] == category
        have = {a.casefold() for a in (row.get("aliases") or [])}
        have.add(row["name"].casefold())
        for alias in aliases:
            assert alias.casefold() in have, (name, alias)


def test_india_sports_traits_not_overridden_by_global_fame():
    smriti = traits_for("Smriti Mandhana", "Sports")
    sania = traits_for("Sania Mirza", "Sports")
    messi = traits_for("Lionel Messi", "Sports")
    assert smriti and "india" in smriti.regions and "cricket" in smriti.sports
    assert sania and "india" in sania.regions and "tennis" in sania.sports
    assert smriti.female is True
    assert sania.female is True
    assert messi and "india" not in messi.regions
    assert "football" in messi.sports


def test_fiction_vs_real_not_confused():
    harry = traits_for("Harry Potter", "Movies")
    srk = traits_for("Shah Rukh Khan", "Movies")
    naruto = traits_for("Naruto Uzumaki", "Anime")
    einstein = traits_for("Albert Einstein", "Scientists")
    assert harry and harry.real is False
    assert srk and srk.real is True
    assert naruto and naruto.real is False
    assert einstein and einstein.real is True
    assert einstein.alive is False


def test_seed_covers_expansion_icons(seed, lookup):
    assert len(seed["characters"]) >= 2000
    assert len(seed["categories"]) == 13
    for name in ("MS Dhoni", "P. V. Sindhu", "Neeraj Chopra", "A. P. J. Abdul Kalam", "Mario"):
        _resolve(lookup, name)
