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

OUT = ROOT / "data" / "knowledge" / "seed_v1.json"
TARGET = 2100
MIN_CHARACTERS = 2000
MIN_QUESTIONS = 500

RULES: dict[str, dict[str, float]] = {
    "Movies": {
        "Is this character fictional?": 0.9,
        "Is this a real person?": 0.15,
        "Is this associated with movies?": 0.95,
        "Is this from television?": 0.25,
        "Is this from anime or manga?": 0.05,
        "Is this from a video game?": 0.1,
        "Is this from comics or superhero media?": 0.45,
    },
    "TV Shows": {
        "Is this character fictional?": 0.9,
        "Is this a real person?": 0.1,
        "Is this from television?": 0.95,
        "Is this associated with movies?": 0.3,
        "Is this primarily known in the 21st century?": 0.55,
    },
    "Anime": {
        "Is this character fictional?": 0.97,
        "Is this a real person?": 0.03,
        "Is this from anime or manga?": 0.97,
        "Is this associated with movies?": 0.35,
        "Is this person/character from Asia?": 0.85,
        "Is this associated with magic or fantasy?": 0.55,
    },
    "Cartoons": {
        "Is this character fictional?": 0.97,
        "Is this a real person?": 0.03,
        "Is this from a cartoon or animated series?": 0.96,
        "Is this from television?": 0.7,
        "Is this a child or teenager (in their main story)?": 0.35,
        "Is this associated with magic or fantasy?": 0.25,
    },
    "Sports": {
        "Is this a real person?": 0.95,
        "Is this character fictional?": 0.05,
        "Is this an athlete or sports figure?": 0.97,
        "Is this person alive today?": 0.7,
        "Is this known for winning major awards or titles?": 0.75,
        "Is this a scientist or inventor?": 0.05,
    },
    "Scientists": {
        "Is this a real person?": 0.95,
        "Is this character fictional?": 0.05,
        "Is this a scientist or inventor?": 0.95,
        "Is this associated with movies?": 0.15,
        "Is this from anime or manga?": 0.02,
        "Is this from a video game?": 0.02,
        "Is this an athlete or sports figure?": 0.05,
        "Is this associated with science fiction?": 0.25,
        "Is this associated with space or astronomy?": 0.45,
    },
    "Historical Figures": {
        "Is this a real person?": 0.97,
        "Is this character fictional?": 0.05,
        "Is this a historical figure from before 1900?": 0.75,
        "Is this person alive today?": 0.05,
        "Is this associated with war or military leadership?": 0.45,
    },
    "Politicians": {
        "Is this a real person?": 0.97,
        "Is this character fictional?": 0.03,
        "Is this a political leader?": 0.95,
        "Is this person alive today?": 0.65,
    },
    "Musicians": {
        "Is this a real person?": 0.9,
        "Is this character fictional?": 0.1,
        "Is this known for music?": 0.97,
        "Is this primarily known in the 21st century?": 0.45,
    },
    "Business Leaders": {
        "Is this a real person?": 0.97,
        "Is this character fictional?": 0.03,
        "Is this known for business or technology entrepreneurship?": 0.95,
        "Is this person alive today?": 0.75,
    },
    "Gaming": {
        "Is this character fictional?": 0.95,
        "Is this a real person?": 0.05,
        "Is this from a video game?": 0.97,
        "Is this associated with movies?": 0.3,
        "Does this character wear a costume or mask?": 0.4,
    },
    "Mythology": {
        "Is this character fictional?": 0.85,
        "Is this a real person?": 0.05,
        "Is this from mythology or legend?": 0.97,
        "Is this associated with magic or fantasy?": 0.75,
        "Is this a historical figure from before 1900?": 0.6,
    },
    "Literature": {
        "Is this character fictional?": 0.85,
        "Is this a real person?": 0.2,
        "Is this known for literature or writing?": 0.7,
        "Is this associated with magic or fantasy?": 0.4,
    },
}


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


def build_seed() -> dict:
    characters, _ = _collect_characters()
    if len(characters) < MIN_CHARACTERS:
        raise RuntimeError(f"Only {len(characters)} characters; need >= {MIN_CHARACTERS}")
    _assert_no_duplicates(characters)

    questions = build_question_catalog(520)
    question_texts = {q["text"] for q in questions}
    missing_legacy = legacy_question_texts() - question_texts
    if missing_legacy:
        raise RuntimeError(f"Legacy RULES questions missing from catalog: {sorted(missing_legacy)}")
    if len(questions) < MIN_QUESTIONS:
        raise RuntimeError(f"Only {len(questions)} questions; need >= {MIN_QUESTIONS}")
    dup_q = _duplicate_texts(q["text"] for q in questions)
    if dup_q:
        raise RuntimeError(f"Duplicate question texts: {dup_q[:5]}")
    overrides = [
        {
            "character": "Albert Einstein",
            "question": "Is this a scientist or inventor?",
            "likelihood": 0.99,
            "sample_size": 100,
        },
        {
            "character": "Lionel Messi",
            "question": "Is this an athlete or sports figure?",
            "likelihood": 0.99,
            "sample_size": 100,
        },
        {
            "character": "Mario",
            "question": "Is this from a video game?",
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Naruto Uzumaki",
            "question": "Is this from anime or manga?",
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Darth Vader",
            "question": "Is this character a villain or antagonist?",
            "likelihood": 0.95,
            "sample_size": 80,
        },
        {
            "character": "SpongeBob SquarePants",
            "question": "Is this from a cartoon or animated series?",
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Zeus",
            "question": "Is this from mythology or legend?",
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Elizabeth Bennet",
            "question": "Is this known for literature or writing?",
            "likelihood": 0.92,
            "sample_size": 80,
        },
        {
            "character": "Barack Obama",
            "question": "Is this a political leader?",
            "likelihood": 0.98,
            "sample_size": 80,
        },
        {
            "character": "Beyoncé",
            "question": "Is this known for music?",
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Elon Musk",
            "question": "Is this known for business or technology entrepreneurship?",
            "likelihood": 0.98,
            "sample_size": 80,
        },
        {
            "character": "Walter White",
            "question": "Is this from television?",
            "likelihood": 0.97,
            "sample_size": 80,
        },
    ]

    return {
        "version": 3,
        "phase": 2,
        "question_phase": 1,
        "categories": list(CATEGORIES),
        "characters": characters,
        "questions": questions,
        "likelihood_rules": [
            {"category": cat, "question": q, "likelihood": lik, "sample_size": 40}
            for cat, mapping in RULES.items()
            for q, lik in mapping.items()
        ],
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

    q_counts: dict[str, int] = {}
    for q in seed["questions"]:
        q_counts[q["category"]] = q_counts.get(q["category"], 0) + 1

    print(f"Wrote {OUT} with {len(seed['characters'])} characters.")
    print("Character category breakdown:")
    for cat in CATEGORIES:
        print(f"  {cat}: {counts[cat]}")
    print(f"Questions: {len(seed['questions'])}")
    print("Question category breakdown:")
    for cat in sorted(q_counts, key=lambda c: (-q_counts[c], c)):
        print(f"  {cat}: {q_counts[cat]}")
    print(
        f"Rules: {len(seed['likelihood_rules'])}, "
        f"overrides: {len(seed['likelihood_overrides'])}"
    )
    assert len(seed["questions"]) >= MIN_QUESTIONS
    assert len(seed["characters"]) >= MIN_CHARACTERS
    legacy_present = legacy_question_texts().issubset({q["text"] for q in seed["questions"]})
    print(f"Legacy RULES questions present: {legacy_present}")


if __name__ == "__main__":
    main()
