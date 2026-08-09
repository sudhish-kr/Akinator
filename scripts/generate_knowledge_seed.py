"""Generate data/knowledge/seed_v1.json — Knowledge Expansion Phase 1 (2000+ characters).

Run: python scripts/generate_knowledge_seed.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent
ROOT = SCRIPTS.parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from knowledge_phase1_data import CATEGORIES, CURATED_CORE, themed_fill  # noqa: E402
from knowledge_questions_data import build_question_catalog, legacy_question_texts  # noqa: E402
from likelihood_priors import assert_mapping_quality, build_likelihood_rules  # noqa: E402
from questions_v2_data import (  # noqa: E402
    DATASET_ID as V2_DATASET_ID,
    QUESTION_PHASE as V2_QUESTION_PHASE,
    build_v2_questions,
)
from akinator_style_rewrites import to_akinator_style  # noqa: E402

OUT = ROOT / "data" / "knowledge" / "seed_v1.json"
QUESTIONS_V2_OUT = ROOT / "data" / "knowledge" / "questions_v2.json"
TARGET = 2100
MIN_CHARACTERS = 2000
MIN_QUESTIONS = 500
MIN_ACTIVE_V2 = 220
MAX_ACTIVE_V2 = 280

RULES: dict[str, dict[str, float]] = {
    "Movies": {
        "Is this a made-up character?": 0.9,
        "Is this a real person?": 0.15,
        "Is this from a movie?": 0.95,
        "Is this from a TV show?": 0.25,
        "Is this from anime?": 0.05,
        "Is this from a video game?": 0.1,
        "Is this a superhero?": 0.45,
    },
    "TV Shows": {
        "Is this a made-up character?": 0.9,
        "Is this a real person?": 0.1,
        "Is this from a TV show?": 0.95,
        "Is this from a movie?": 0.3,
        "Are they known today?": 0.55,
    },
    "Anime": {
        "Is this a made-up character?": 0.97,
        "Is this a real person?": 0.03,
        "Is this from anime?": 0.97,
        "Is this from a movie?": 0.35,
        "Are they from Asia?": 0.85,
        "Is this about magic?": 0.55,
    },
    "Cartoons": {
        "Is this a made-up character?": 0.97,
        "Is this a real person?": 0.03,
        "Is this from a cartoon?": 0.96,
        "Is this from a TV show?": 0.7,
        "Are they a kid or teen?": 0.35,
        "Is this about magic?": 0.25,
    },
    "Sports": {
        "Is this a real person?": 0.95,
        "Is this a made-up character?": 0.05,
        "Is this a sports player?": 0.97,
        "Is this person still alive?": 0.7,
        "Have they won big awards?": 0.75,
        "Is this a scientist?": 0.05,
    },
    "Scientists": {
        "Is this a real person?": 0.95,
        "Is this a made-up character?": 0.05,
        "Is this a scientist?": 0.95,
        "Is this from a movie?": 0.15,
        "Is this from anime?": 0.02,
        "Is this from a video game?": 0.02,
        "Is this a sports player?": 0.05,
        "Is this sci-fi?": 0.25,
        "Is this about space?": 0.45,
    },
    "Historical Figures": {
        "Is this a real person?": 0.97,
        "Is this a made-up character?": 0.05,
        "Is this from long ago?": 0.75,
        "Is this person still alive?": 0.05,
        "Are they linked to war?": 0.45,
    },
    "Politicians": {
        "Is this a real person?": 0.97,
        "Is this a made-up character?": 0.03,
        "Is this a political leader?": 0.95,
        "Is this person still alive?": 0.65,
    },
    "Musicians": {
        "Is this a real person?": 0.9,
        "Is this a made-up character?": 0.1,
        "Is this a musician?": 0.97,
        "Are they known today?": 0.45,
    },
    "Business Leaders": {
        "Is this a real person?": 0.97,
        "Is this a made-up character?": 0.03,
        "Is this a business leader?": 0.95,
        "Is this person still alive?": 0.75,
    },
    "Gaming": {
        "Is this a made-up character?": 0.95,
        "Is this a real person?": 0.05,
        "Is this from a video game?": 0.97,
        "Is this from a movie?": 0.3,
        "Do they wear a costume?": 0.4,
    },
    "Mythology": {
        "Is this a made-up character?": 0.85,
        "Is this a real person?": 0.05,
        "Is this from an old legend?": 0.97,
        "Is this about magic?": 0.75,
        "Is this from long ago?": 0.6,
    },
    "Literature": {
        "Is this a made-up character?": 0.85,
        "Is this a real person?": 0.2,
        "Is this a writer?": 0.7,
        "Is this about magic?": 0.4,
    },
}


def _remap_question_keys(rules: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    remapped: dict[str, dict[str, float]] = {}
    for category, mapping in rules.items():
        remapped[category] = {
            to_akinator_style(question): value for question, value in mapping.items()
        }
    return remapped


RULES = _remap_question_keys(RULES)


def _default_aliases(name: str) -> list[str]:
    parts = name.strip().split()
    if len(parts) >= 2:
        return [parts[-1]]
    return [name.strip()[: min(8, len(name.strip()))]]


def _collect_characters() -> tuple[list[dict], dict[str, int]]:
    seen: set[str] = set()
    characters: list[dict] = []
    per_category: dict[str, int] = {cat: 0 for cat in CATEGORIES}
    fill_start: dict[str, int] = {cat: 0 for cat in CATEGORIES}

    def add(name: str, category: str, aliases: list[str]) -> bool:
        key = name.casefold().strip()
        if not key or key in seen:
            return False
        clean_aliases: list[str] = []
        alias_seen: set[str] = set()
        for alias in aliases:
            ak = alias.casefold().strip()
            if not ak or ak == key or ak in seen or ak in alias_seen:
                continue
            alias_seen.add(ak)
            clean_aliases.append(alias.strip())
        if not clean_aliases:
            for fallback in _default_aliases(name):
                fk = fallback.casefold().strip()
                if fk and fk != key and fk not in seen:
                    clean_aliases.append(fallback.strip())
                    break
        if not clean_aliases:
            return False
        seen.add(key)
        for alias in clean_aliases:
            seen.add(alias.casefold())
        characters.append(
            {
                "name": name.strip(),
                "category": category,
                "aliases": clean_aliases,
                "is_active": True,
            }
        )
        per_category[category] += 1
        return True

    per_cat_target = TARGET // len(CATEGORIES)
    extra = TARGET % len(CATEGORIES)
    category_targets = {
        cat: per_cat_target + (1 if i < extra else 0)
        for i, cat in enumerate(CATEGORIES)
    }

    for category in CATEGORIES:
        for name, aliases in CURATED_CORE.get(category, []):
            add(name, category, list(aliases))

    for category in CATEGORIES:
        quota = category_targets[category]
        stall = 0
        while per_category[category] < quota:
            need = quota - per_category[category]
            batch = themed_fill(
                category,
                max(need, 12),
                start_index=fill_start[category],
            )
            fill_start[category] += max(len(batch), 1)
            added_any = False
            for name, aliases in batch:
                if per_category[category] >= quota:
                    break
                if add(name, category, list(aliases)):
                    added_any = True
            if added_any:
                stall = 0
            else:
                stall += 1
                fill_start[category] += 50
                if stall > 8:
                    raise RuntimeError(f"Could not fill category {category!r}")

    idx = 0
    while len(characters) < TARGET:
        category = CATEGORIES[idx % len(CATEGORIES)]
        batch = themed_fill(category, 16, start_index=fill_start[category])
        fill_start[category] += max(len(batch), 1)
        for name, aliases in batch:
            if len(characters) >= TARGET:
                break
            add(name, category, list(aliases))
        idx += 1
        if idx > TARGET * 4:
            break

    return characters, per_category


def _duplicate_texts(texts) -> list[str]:
    seen: set[str] = set()
    out: set[str] = set()
    for t in texts:
        k = t.casefold().strip()
        if k in seen:
            out.add(t)
        seen.add(k)
    return sorted(out)


def _assert_no_duplicates(characters: list[dict]) -> None:
    names: list[str] = []
    aliases: list[str] = []
    for item in characters:
        names.append(item["name"])
        aliases.extend(item.get("aliases") or [])

    def dup(values: list[str]) -> list[str]:
        seen: set[str] = set()
        out: set[str] = set()
        for v in values:
            k = v.casefold().strip()
            if k in seen:
                out.add(k)
            seen.add(k)
        return sorted(out)

    dup_names = dup(names)
    dup_aliases = dup(aliases)
    name_keys = {n.casefold().strip() for n in names}
    alias_name_collide = sorted({a.casefold().strip() for a in aliases if a.casefold().strip() in name_keys})
    if dup_names or dup_aliases or alias_name_collide:
        raise RuntimeError(
            "Duplicate keys remain: "
            f"names={dup_names[:5]} aliases={dup_aliases[:5]} collide={alias_name_collide[:5]}"
        )


def _merge_question_datasets() -> list[dict]:
    """Active curated v2 + deactivated legacy/AI catalog (kept, not deleted)."""
    v2 = build_v2_questions()
    v2_keys = {q["text"].casefold().strip() for q in v2}

    legacy_catalog = build_question_catalog(520)
    merged: list[dict] = []
    seen: set[str] = set()

    for item in v2:
        key = item["text"].casefold().strip()
        seen.add(key)
        merged.append(dict(item))

    for item in legacy_catalog:
        key = item["text"].casefold().strip()
        if key in seen or key in v2_keys:
            continue
        seen.add(key)
        deactivated = dict(item)
        deactivated["is_active"] = False
        deactivated["dataset"] = "v1"
        deactivated.pop("hierarchy_level", None)
        deactivated.pop("hierarchy_name", None)
        merged.append(deactivated)

    return merged


def build_seed() -> dict:
    characters, _ = _collect_characters()
    if len(characters) < MIN_CHARACTERS:
        raise RuntimeError(f"Only {len(characters)} characters; need >= {MIN_CHARACTERS}")
    _assert_no_duplicates(characters)

    questions = _merge_question_datasets()
    active = [q for q in questions if q.get("is_active")]
    inactive = [q for q in questions if not q.get("is_active")]
    if not (MIN_ACTIVE_V2 <= len(active) <= MAX_ACTIVE_V2):
        raise RuntimeError(
            f"Active v2 questions={len(active)}; expected {MIN_ACTIVE_V2}-{MAX_ACTIVE_V2}"
        )
    if len(questions) < MIN_QUESTIONS:
        raise RuntimeError(f"Only {len(questions)} total questions; need >= {MIN_QUESTIONS}")

    question_texts = {q["text"] for q in questions}
    missing_legacy = legacy_question_texts() - question_texts
    if missing_legacy:
        raise RuntimeError(f"Legacy RULES questions missing from catalog: {sorted(missing_legacy)}")
    if any(q.get("dataset") != V2_DATASET_ID for q in active):
        raise RuntimeError("All active questions must be dataset=v2")
    if any(q.get("is_active") for q in inactive):
        raise RuntimeError("Inactive catalog entries must have is_active=False")

    dup_q = _duplicate_texts(q["text"] for q in questions)
    if dup_q:
        raise RuntimeError(f"Duplicate question texts: {dup_q[:5]}")
    overrides = [
        {
            "character": "Albert Einstein",
            "question": to_akinator_style("Is this a scientist?"),
            "likelihood": 0.99,
            "sample_size": 100,
        },
        {
            "character": "Lionel Messi",
            "question": to_akinator_style("Is this a sports player?"),
            "likelihood": 0.99,
            "sample_size": 100,
        },
        {
            "character": "Mario",
            "question": to_akinator_style("Is this from a video game?"),
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Naruto Uzumaki",
            "question": to_akinator_style("Is this from anime?"),
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Darth Vader",
            "question": to_akinator_style("Is this a villain?"),
            "likelihood": 0.95,
            "sample_size": 80,
        },
        {
            "character": "SpongeBob SquarePants",
            "question": to_akinator_style("Is this from a cartoon?"),
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Zeus",
            "question": to_akinator_style("Is this from an old legend?"),
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Elizabeth Bennet",
            "question": to_akinator_style("Is this a writer?"),
            "likelihood": 0.92,
            "sample_size": 80,
        },
        {
            "character": "Barack Obama",
            "question": to_akinator_style("Is this a political leader?"),
            "likelihood": 0.98,
            "sample_size": 80,
        },
        {
            "character": "Beyoncé",
            "question": to_akinator_style("Is this a musician?"),
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Elon Musk",
            "question": to_akinator_style("Is this a business leader?"),
            "likelihood": 0.98,
            "sample_size": 80,
        },
        {
            "character": "Walter White",
            "question": to_akinator_style("Is this from a TV show?"),
            "likelihood": 0.97,
            "sample_size": 80,
        },
    ]
    for row in overrides:
        if row["question"] not in question_texts:
            raise RuntimeError(f"Override question missing from catalog: {row['question']}")

    rules = build_likelihood_rules(questions, explicit_rules=RULES)
    assert_mapping_quality(characters, questions, rules)

    return {
        "version": 5,
        "phase": 3,
        "question_phase": V2_QUESTION_PHASE,
        "mapping_phase": 1,
        "active_question_dataset": V2_DATASET_ID,
        "categories": list(CATEGORIES),
        "characters": characters,
        "questions": questions,
        "likelihood_rules": rules,
        "likelihood_overrides": overrides,
        "default_likelihood": 0.5,
        "default_sample_size": 10,
    }


def main() -> None:
    seed = build_seed()
    counts: dict[str, int] = {cat: 0 for cat in CATEGORIES}
    for item in seed["characters"]:
        counts[item["category"]] += 1

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    v2_only = [q for q in seed["questions"] if q.get("dataset") == V2_DATASET_ID]
    QUESTIONS_V2_OUT.write_text(
        json.dumps(
            {
                "dataset": V2_DATASET_ID,
                "question_phase": V2_QUESTION_PHASE,
                "questions": v2_only,
            },
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    q_counts: dict[str, int] = {}
    active_counts: dict[str, int] = {}
    for q in seed["questions"]:
        q_counts[q["category"]] = q_counts.get(q["category"], 0) + 1
        if q.get("is_active"):
            active_counts[q["category"]] = active_counts.get(q["category"], 0) + 1

    active_n = sum(1 for q in seed["questions"] if q.get("is_active"))
    inactive_n = len(seed["questions"]) - active_n

    print(f"Wrote {OUT} with {len(seed['characters'])} characters.")
    print("Character category breakdown:")
    for cat in CATEGORIES:
        print(f"  {cat}: {counts[cat]}")
    print(f"Questions total: {len(seed['questions'])} (active={active_n}, inactive={inactive_n})")
    print(f"Wrote {QUESTIONS_V2_OUT} with {len(v2_only)} curated v2 questions.")
    print("Active question category breakdown:")
    for cat in sorted(active_counts, key=lambda c: (-active_counts[c], c)):
        print(f"  {cat}: {active_counts[cat]}")
    print(
        f"Rules: {len(seed['likelihood_rules'])}, "
        f"overrides: {len(seed['likelihood_overrides'])}"
    )
    assert active_n >= MIN_ACTIVE_V2
    assert len(seed["characters"]) >= MIN_CHARACTERS
    assert len(seed["likelihood_rules"]) > 1000
    legacy_present = legacy_question_texts().issubset({q["text"] for q in seed["questions"]})
    print(f"Legacy RULES questions present: {legacy_present}")


if __name__ == "__main__":
    main()
