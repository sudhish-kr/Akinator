"""Admin knowledge base import/export (characters + questions JSON)."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone

from app.db.repositories.game_repository import GameRepository


class KnowledgeIOError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


def _norm(value: str) -> str:
    return value.strip().casefold()


def _duplicate_keys(values: list[str]) -> list[str]:
    counts = Counter(_norm(v) for v in values if v and v.strip())
    return sorted(key for key, n in counts.items() if n > 1)


class KnowledgeIOService:
    def __init__(self, repo: GameRepository):
        self.repo = repo

    async def export_knowledge(self) -> dict:
        characters = await self.repo.list_all_characters()
        questions = await self.repo.list_all_questions()
        return {
            "version": 1,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "characters": [
                {
                    "name": c.name,
                    "category": c.category,
                    "image_url": c.image_url,
                    "is_active": c.is_active,
                }
                for c in characters
            ],
            "questions": [
                {
                    "text": q.text,
                    "category": q.category,
                    "is_active": q.is_active,
                }
                for q in questions
            ],
        }

    async def import_knowledge(
        self,
        *,
        characters: list[dict],
        questions: list[dict],
    ) -> dict:
        char_names = [c["name"] for c in characters]
        question_texts = [q["text"] for q in questions]

        dup_chars = _duplicate_keys(char_names)
        if dup_chars:
            raise KnowledgeIOError(
                f"Duplicate characters in import: {', '.join(dup_chars)}",
                400,
            )
        dup_questions = _duplicate_keys(question_texts)
        if dup_questions:
            raise KnowledgeIOError(
                f"Duplicate questions in import: {', '.join(dup_questions)}",
                400,
            )

        existing_chars = await self.repo.find_characters_by_names(char_names)
        if existing_chars:
            names = ", ".join(sorted({c.name for c in existing_chars}))
            raise KnowledgeIOError(f"Characters already exist: {names}", 409)

        existing_questions = await self.repo.find_questions_by_texts(question_texts)
        if existing_questions:
            texts = ", ".join(sorted({q.text for q in existing_questions}))
            raise KnowledgeIOError(f"Questions already exist: {texts}", 409)

        try:
            for item in characters:
                await self.repo.create_character(
                    name=item["name"].strip(),
                    category=item["category"].strip(),
                    image_url=item.get("image_url"),
                    is_active=bool(item.get("is_active", True)),
                )
            for item in questions:
                await self.repo.create_question(
                    text=item["text"].strip(),
                    category=item.get("category"),
                    is_active=bool(item.get("is_active", True)),
                )
            await self.repo.commit()
        except Exception:
            await self.repo.rollback()
            raise

        return {
            "status": "imported",
            "characters_imported": len(characters),
            "questions_imported": len(questions),
        }
