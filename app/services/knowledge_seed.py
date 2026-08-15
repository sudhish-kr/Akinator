"""Knowledge-base seed validation and import (characters, aliases, likelihoods).

Does not modify the Bayesian engine — only persists curated seed data.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from app.db.repositories.game_repository import GameRepository


class KnowledgeSeedError(Exception):
    """Raised when seed data fails validation or conflicts with the database."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _norm(value: str) -> str:
    return value.strip().casefold()


def _duplicate_keys(values: list[str]) -> list[str]:
    counts = Counter(_norm(v) for v in values if v and str(v).strip())
    return sorted(key for key, n in counts.items() if n > 1)


def load_seed_file(path: Path | str) -> dict[str, Any]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise KnowledgeSeedError("Seed file must be a JSON object")
    return data


def validate_seed_payload(data: dict[str, Any]) -> None:
    """Validate structure and in-file duplicates before any DB writes."""
    characters = data.get("characters")
    questions = data.get("questions")
    if not isinstance(characters, list) or not characters:
        raise KnowledgeSeedError("Seed must include a non-empty 'characters' list")
    if not isinstance(questions, list) or not questions:
        raise KnowledgeSeedError("Seed must include a non-empty 'questions' list")

    char_names: list[str] = []
    all_aliases: list[str] = []
    for i, item in enumerate(characters):
        if not isinstance(item, dict):
            raise KnowledgeSeedError(f"characters[{i}] must be an object")
        name = item.get("name")
        category = item.get("category")
        if not isinstance(name, str) or not name.strip():
            raise KnowledgeSeedError(f"characters[{i}] missing name")
        if not isinstance(category, str) or not category.strip():
            raise KnowledgeSeedError(f"characters[{i}] missing category")
        char_names.append(name)
        aliases = item.get("aliases") or []
        if not isinstance(aliases, list):
            raise KnowledgeSeedError(f"characters[{i}].aliases must be a list")
        for j, alias in enumerate(aliases):
            if not isinstance(alias, str) or not alias.strip():
                raise KnowledgeSeedError(f"characters[{i}].aliases[{j}] invalid")
            all_aliases.append(alias)

    dup_chars = _duplicate_keys(char_names)
    if dup_chars:
        raise KnowledgeSeedError(f"Duplicate characters in seed: {', '.join(dup_chars)}")

    name_keys = {_norm(n) for n in char_names}
    alias_vs_name = sorted({_norm(a) for a in all_aliases if _norm(a) in name_keys})
    if alias_vs_name:
        raise KnowledgeSeedError(
            f"Aliases collide with character names: {', '.join(alias_vs_name)}"
        )

    dup_aliases = _duplicate_keys(all_aliases)
    if dup_aliases:
        raise KnowledgeSeedError(f"Duplicate aliases in seed: {', '.join(dup_aliases)}")

    question_texts: list[str] = []
    for i, item in enumerate(questions):
        if not isinstance(item, dict):
            raise KnowledgeSeedError(f"questions[{i}] must be an object")
        text = item.get("text")
        category = item.get("category")
        if not isinstance(text, str) or not text.strip():
            raise KnowledgeSeedError(f"questions[{i}] missing text")
        if not isinstance(category, str) or not category.strip():
            raise KnowledgeSeedError(f"questions[{i}] missing category")
        if "is_active" in item and not isinstance(item["is_active"], bool):
            raise KnowledgeSeedError(f"questions[{i}] is_active must be a boolean")
        ig = item.get("avg_information_gain", item.get("initial_information_gain"))
        if ig is None:
            raise KnowledgeSeedError(
                f"questions[{i}] missing initial information-gain metadata "
                "(avg_information_gain)"
            )
        if not isinstance(ig, (int, float)) or not 0.0 <= float(ig) <= 1.0:
            raise KnowledgeSeedError(
                f"questions[{i}] has invalid avg_information_gain"
            )
        times_asked = item.get("times_asked", 0)
        if not isinstance(times_asked, int) or times_asked < 0:
            raise KnowledgeSeedError(f"questions[{i}] has invalid times_asked")
        question_texts.append(text)

    dup_questions = _duplicate_keys(question_texts)
    if dup_questions:
        raise KnowledgeSeedError(f"Duplicate questions in seed: {', '.join(dup_questions)}")

    q_keys = {_norm(t) for t in question_texts}
    cat_keys = {_norm(c.get("category", "")) for c in characters}

    for i, rule in enumerate(data.get("likelihood_rules") or []):
        if not isinstance(rule, dict):
            raise KnowledgeSeedError(f"likelihood_rules[{i}] must be an object")
        cat = rule.get("category")
        q = rule.get("question")
        lik = rule.get("likelihood")
        if not isinstance(cat, str) or _norm(cat) not in cat_keys:
            raise KnowledgeSeedError(
                f"likelihood_rules[{i}] references unknown category: {cat!r}"
            )
        if not isinstance(q, str) or _norm(q) not in q_keys:
            raise KnowledgeSeedError(
                f"likelihood_rules[{i}] references unknown question: {q!r}"
            )
        if not isinstance(lik, (int, float)) or not 0.0 <= float(lik) <= 1.0:
            raise KnowledgeSeedError(f"likelihood_rules[{i}] has invalid likelihood")

    name_lookup = {_norm(n): n for n in char_names}
    for i, ov in enumerate(data.get("likelihood_overrides") or []):
        if not isinstance(ov, dict):
            raise KnowledgeSeedError(f"likelihood_overrides[{i}] must be an object")
        cname = ov.get("character")
        q = ov.get("question")
        lik = ov.get("likelihood")
        if not isinstance(cname, str) or _norm(cname) not in name_lookup:
            raise KnowledgeSeedError(
                f"likelihood_overrides[{i}] references unknown character: {cname!r}"
            )
        if not isinstance(q, str) or _norm(q) not in q_keys:
            raise KnowledgeSeedError(
                f"likelihood_overrides[{i}] references unknown question: {q!r}"
            )
        if not isinstance(lik, (int, float)) or not 0.0 <= float(lik) <= 1.0:
            raise KnowledgeSeedError(f"likelihood_overrides[{i}] has invalid likelihood")


class KnowledgeSeedService:
    def __init__(self, repo: GameRepository):
        self.repo = repo

    async def validate_against_database(self, data: dict[str, Any]) -> None:
        validate_seed_payload(data)

        char_names = [c["name"] for c in data["characters"]]
        question_texts = [q["text"] for q in data["questions"]]
        aliases = [
            a
            for c in data["characters"]
            for a in (c.get("aliases") or [])
        ]

        existing_chars = await self.repo.find_characters_by_names(char_names)
        if existing_chars:
            names = ", ".join(sorted({c.name for c in existing_chars}))
            raise KnowledgeSeedError(f"Characters already exist: {names}", 409)

        # Aliases must not collide with existing character names either
        existing_as_chars = await self.repo.find_characters_by_names(aliases)
        if existing_as_chars:
            names = ", ".join(sorted({c.name for c in existing_as_chars}))
            raise KnowledgeSeedError(
                f"Aliases collide with existing characters: {names}", 409
            )

        existing_aliases = await self.repo.find_aliases_by_values(
            aliases + char_names
        )
        if existing_aliases:
            vals = ", ".join(sorted({a.alias for a in existing_aliases}))
            raise KnowledgeSeedError(f"Aliases already exist: {vals}", 409)

        existing_questions = await self.repo.find_questions_by_texts(question_texts)
        if existing_questions:
            texts = ", ".join(sorted({q.text for q in existing_questions}))
            raise KnowledgeSeedError(f"Questions already exist: {texts}", 409)

    async def import_seed(
        self,
        data: dict[str, Any],
        *,
        dry_run: bool = False,
    ) -> dict[str, int]:
        await self.validate_against_database(data)
        if dry_run:
            return {
                "characters": len(data["characters"]),
                "aliases": sum(len(c.get("aliases") or []) for c in data["characters"]),
                "questions": len(data["questions"]),
                "likelihoods": self._estimate_likelihood_count(data),
                "dry_run": 1,
            }

        try:
            return await self._persist(data)
        except Exception:
            await self.repo.db.rollback()
            raise

    def _estimate_likelihood_count(self, data: dict[str, Any]) -> int:
        """Count distinct (character, question) pairs that rules/overrides would write."""
        rules = data.get("likelihood_rules") or []
        overrides = data.get("likelihood_overrides") or []
        by_cat: dict[str, set[str]] = {}
        for rule in rules:
            by_cat.setdefault(_norm(rule["category"]), set()).add(_norm(rule["question"]))
        pairs: set[tuple[str, str]] = set()
        for c in data["characters"]:
            for q in by_cat.get(_norm(c["category"]), ()):
                pairs.add((_norm(c["name"]), q))
        for ov in overrides:
            pairs.add((_norm(ov["character"]), _norm(ov["question"])))
        return len(pairs)

    async def _persist(self, data: dict[str, Any]) -> dict[str, int]:
        char_by_name: dict[str, Any] = {}
        alias_count = 0
        for item in data["characters"]:
            character = await self.repo.create_character(
                name=item["name"].strip(),
                category=item["category"].strip(),
                image_url=item.get("image_url"),
                is_active=bool(item.get("is_active", True)),
                popularity_score=int(item.get("popularity_score", 0) or 0),
            )
            char_by_name[_norm(character.name)] = character
            for alias in item.get("aliases") or []:
                await self.repo.create_alias(character.id, alias.strip())
                alias_count += 1

        q_by_text: dict[str, Any] = {}
        for item in data["questions"]:
            ig = item.get("avg_information_gain", item.get("initial_information_gain"))
            question = await self.repo.create_question(
                text=item["text"].strip(),
                category=str(item["category"]).strip(),
                is_active=bool(item.get("is_active", True)),
                times_asked=int(item.get("times_asked", 0)),
                avg_information_gain=float(ig) if ig is not None else None,
            )
            q_by_text[_norm(question.text)] = question

        default_sample = int(data.get("default_sample_size", 10))
        written_pairs: set[tuple[str, str]] = set()

        # category -> question_norm -> (likelihood, sample_size)
        rules_index: dict[str, dict[str, tuple[float, int]]] = {}
        for rule in data.get("likelihood_rules") or []:
            cat = _norm(rule["category"])
            q = _norm(rule["question"])
            sample = int(rule.get("sample_size", default_sample))
            rules_index.setdefault(cat, {})[q] = (float(rule["likelihood"]), sample)

        for item in data["characters"]:
            character = char_by_name[_norm(item["name"])]
            for q_norm, (lik, sample) in rules_index.get(
                _norm(item["category"]), {}
            ).items():
                question = q_by_text[q_norm]
                await self.repo.upsert_character_answer(
                    character.id, question.id, lik, sample
                )
                written_pairs.add((_norm(character.name), q_norm))

        for ov in data.get("likelihood_overrides") or []:
            character = char_by_name[_norm(ov["character"])]
            question = q_by_text[_norm(ov["question"])]
            sample = int(ov.get("sample_size", default_sample))
            await self.repo.upsert_character_answer(
                character.id, question.id, float(ov["likelihood"]), sample
            )
            written_pairs.add((_norm(character.name), _norm(ov["question"])))

        await self.repo.db.commit()
        return {
            "characters": len(char_by_name),
            "aliases": alias_count,
            "questions": len(q_by_text),
            "likelihoods": len(written_pairs),
            "dry_run": 0,
        }

    async def sync_active_likelihoods(
        self,
        data: dict[str, Any],
        *,
        align_categories: bool = True,
        dry_run: bool = False,
    ) -> dict[str, int]:
        """Upsert seed likelihoods for active DB characters × active questions.

        Uses existing ``likelihood_rules`` / ``likelihood_overrides`` from the
        knowledge seed. Does not create/delete characters or questions, and does
        not recreate the database. Optionally realigns character categories to
        match the seed so category rules apply to production icons.
        """
        from sqlalchemy import select

        from app.db.models import Character, Question

        validate_seed_payload(data)

        characters = list(
            (
                await self.repo.db.execute(
                    select(Character).where(Character.is_active.is_(True))
                )
            )
            .scalars()
            .all()
        )
        questions = list(
            (
                await self.repo.db.execute(
                    select(Question).where(Question.is_active.is_(True))
                )
            )
            .scalars()
            .all()
        )
        if not characters:
            raise KnowledgeSeedError("No active characters in database")
        if not questions:
            raise KnowledgeSeedError("No active questions in database")

        seed_category_by_name = {
            _norm(item["name"]): item["category"].strip()
            for item in data["characters"]
        }
        categories_aligned = 0
        effective_category: dict[Any, str] = {}
        for character in characters:
            want = (
                seed_category_by_name.get(_norm(character.name))
                if align_categories
                else None
            )
            if want and character.category != want:
                categories_aligned += 1
                if not dry_run:
                    character.category = want
                effective_category[character.id] = want
            else:
                effective_category[character.id] = character.category

        if categories_aligned and not dry_run:
            await self.repo.db.flush()

        q_by_text = {_norm(q.text): q for q in questions}
        active_q_norms = set(q_by_text)
        default_sample = int(data.get("default_sample_size", 10))

        rules_index: dict[str, dict[str, tuple[float, int]]] = {}
        for rule in data.get("likelihood_rules") or []:
            q_norm = _norm(rule["question"])
            if q_norm not in active_q_norms:
                continue
            cat = _norm(rule["category"])
            sample = int(rule.get("sample_size", default_sample))
            rules_index.setdefault(cat, {})[q_norm] = (
                float(rule["likelihood"]),
                sample,
            )

        # character_id -> question_id -> (likelihood, sample_size)
        pair_values: dict[tuple[Any, Any], tuple[float, int]] = {}
        for character in characters:
            cat_key = _norm(effective_category[character.id])
            for q_norm, (lik, sample) in rules_index.get(cat_key, {}).items():
                question = q_by_text[q_norm]
                pair_values[(character.id, question.id)] = (lik, sample)

        overrides_applied = 0
        char_by_name = {_norm(c.name): c for c in characters}
        for ov in data.get("likelihood_overrides") or []:
            character = char_by_name.get(_norm(ov["character"]))
            question = q_by_text.get(_norm(ov["question"]))
            if character is None or question is None:
                continue
            sample = int(ov.get("sample_size", default_sample))
            pair_values[(character.id, question.id)] = (
                float(ov["likelihood"]),
                sample,
            )
            overrides_applied += 1

        rows = [
            (cid, qid, lik, sample)
            for (cid, qid), (lik, sample) in pair_values.items()
        ]

        if dry_run:
            return {
                "active_characters": len(characters),
                "active_questions": len(questions),
                "categories_aligned": categories_aligned,
                "overrides_applied": overrides_applied,
                "created": 0,
                "updated": 0,
                "written": len(rows),
                "dry_run": 1,
            }

        counts = await self.repo.bulk_upsert_character_answers(rows)
        await self.repo.db.commit()
        from app.services.playable_catalog import invalidate_playable_catalog

        invalidate_playable_catalog()
        return {
            "active_characters": len(characters),
            "active_questions": len(questions),
            "categories_aligned": categories_aligned,
            "overrides_applied": overrides_applied,
            "created": counts["created"],
            "updated": counts["updated"],
            "written": counts["written"],
            "dry_run": 0,
        }
