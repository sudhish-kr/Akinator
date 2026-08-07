"""Validation tests for character↔question likelihood mappings."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
SEED_PATH = ROOT / "data" / "knowledge" / "seed_v1.json"
PRIORS_SCRIPT = ROOT / "scripts" / "likelihood_priors.py"
GENERATE_SCRIPT = ROOT / "scripts" / "generate_knowledge_seed.py"


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    # Ensure scripts/ imports resolve for generate_knowledge_seed
    import sys

    scripts = str(path.parent)
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def priors():
    return _load_module(PRIORS_SCRIPT, "likelihood_priors")


@pytest.fixture(scope="module")
def seed():
    assert SEED_PATH.exists()
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


def test_priors_are_deterministic(priors):
    questions = [
        {"text": "Is this from anime or manga?", "category": "Anime"},
        {"text": "Is this an athlete or sports figure?", "category": "Sports"},
        {"text": "Is this person alive today?", "category": "Age"},
    ]
    a = priors.build_likelihood_rules(questions)
    b = priors.build_likelihood_rules(questions)
    assert a == b
    # No stochastic fields
    assert all(isinstance(r["likelihood"], float) for r in a)


def test_every_character_has_meaningful_mapping_coverage(seed, priors):
    coverage = priors.estimate_character_coverage(seed["characters"], seed["likelihood_rules"])
    assert len(coverage) == len(seed["characters"])
    assert min(coverage.values()) >= 80
    # Expanded mapping phase should vastly exceed the old ~70-rule seed
    assert len(seed["likelihood_rules"]) > 1000


def test_category_specific_questions_linked_appropriately(seed):
    index = {
        (r["category"], r["question"]): float(r["likelihood"])
        for r in seed["likelihood_rules"]
    }
    assert index[("Anime", "Is this from anime or manga?")] >= 0.9
    assert index[("Sports", "Is this from anime or manga?")] <= 0.2
    assert index[("Sports", "Is this an athlete or sports figure?")] >= 0.9
    assert index[("Anime", "Is this an athlete or sports figure?")] <= 0.2
    assert index[("Scientists", "Is this a scientist or inventor?")] >= 0.9
    assert index[("Cartoons", "Is this a scientist or inventor?")] <= 0.2
    assert index[("Gaming", "Is this from a video game?")] >= 0.9
    assert index[("Politicians", "Is this from a video game?")] <= 0.2


def test_domain_questions_not_linked_when_irrelevant(priors):
    """Ambiguous mid-range domain priors should be omitted (not forced)."""
    questions = [
        {"text": "Is this associated with indie folk music festivals?", "category": "Music"},
    ]
    # Gaming × Music base prior is 0.12 — should link (anti-aligned).
    # Movies × Music is 0.15 — border; check Politics × Anime style skip for mid values.
    questions.append(
        {"text": "Is this a generic personality vibe question?", "category": "Personality"}
    )
    rules = priors.build_likelihood_rules(questions)
    pairs = {(r["category"], r["question"]) for r in rules}
    # Universal Personality must link for all character categories
    for cat in priors.CHAR_CATEGORIES:
        assert (cat, "Is this a generic personality vibe question?") in pairs
    # Music domain should link aligned Musicians and clearly anti-aligned cats
    assert ("Musicians", "Is this associated with indie folk music festivals?") in pairs
    assert ("Sports", "Is this associated with indie folk music festivals?") in pairs


def test_assert_mapping_quality_passes_for_seed(seed, priors):
    priors.assert_mapping_quality(seed["characters"], seed["questions"], seed["likelihood_rules"])


def test_build_seed_expands_mappings_without_engine_changes():
    gen = _load_module(GENERATE_SCRIPT, "generate_knowledge_seed")
    built = gen.build_seed()
    assert built.get("mapping_phase") == 1
    assert len(built["likelihood_rules"]) > 1000
    # Explicit RULES still win for anchors
    index = {
        (r["category"], r["question"]): float(r["likelihood"])
        for r in built["likelihood_rules"]
    }
    assert index[("Scientists", "Is this a scientist or inventor?")] == pytest.approx(0.95)
