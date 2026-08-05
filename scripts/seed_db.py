"""
Seed development database with TDD Section 2.6 worked-example characters.

Usage:
    docker compose up -d db
    alembic upgrade head
    python scripts/seed_db.py
"""

import asyncio
import uuid

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings
from app.db.models import Base, Character, CharacterAnswer, Question

# Worked-example characters (TDD v1.1 Section 2.6)
CHARACTERS = [
    ("Albert Einstein", "real_person"),
    ("Lionel Messi", "real_person"),
    ("Elon Musk", "real_person"),
    ("Cristiano Ronaldo", "real_person"),
]

QUESTIONS = [
    ("Is this person a scientist?", "science"),
    ("Did this person win a Nobel Prize?", "science"),
    ("Is this person an athlete?", "sports"),
    ("Is this person alive today?", "general"),
    ("Is this person known for technology or business?", "general"),
]

# L(C, Q) for scientist question — TDD Section 2.6
SCIENTIST_LIKELIHOODS = {
    "Albert Einstein": 0.95,
    "Lionel Messi": 0.02,
    "Elon Musk": 0.55,
    "Cristiano Ronaldo": 0.02,
}


async def seed() -> None:
    engine = create_async_engine(settings.database_url, echo=True)
    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as db:
        char_map: dict[str, uuid.UUID] = {}
        for name, category in CHARACTERS:
            character = Character(id=uuid.uuid4(), name=name, category=category, is_active=True)
            db.add(character)
            char_map[name] = character.id

        q_map: dict[str, uuid.UUID] = {}
        for text, category in QUESTIONS:
            question = Question(id=uuid.uuid4(), text=text, category=category, is_active=True)
            db.add(question)
            q_map[text] = question.id

        await db.flush()

        scientist_q = q_map["Is this person a scientist?"]
        for name, likelihood in SCIENTIST_LIKELIHOODS.items():
            db.add(
                CharacterAnswer(
                    character_id=char_map[name],
                    question_id=scientist_q,
                    likelihood=likelihood,
                    sample_size=100,
                )
            )

        # Default neutral likelihoods for other question/character pairs
        for name, cid in char_map.items():
            for text, qid in q_map.items():
                if text == "Is this person a scientist?":
                    continue
                defaults = {
                    "Did this person win a Nobel Prize?": {
                        "Albert Einstein": 0.95,
                        "Elon Musk": 0.05,
                    },
                    "Is this person an athlete?": {
                        "Lionel Messi": 0.98,
                        "Cristiano Ronaldo": 0.98,
                    },
                    "Is this person alive today?": {
                        "Albert Einstein": 0.0,
                        "Lionel Messi": 0.95,
                        "Elon Musk": 0.95,
                        "Cristiano Ronaldo": 0.95,
                    },
                    "Is this person known for technology or business?": {
                        "Elon Musk": 0.95,
                    },
                }
                likelihood = defaults.get(text, {}).get(name, 0.5)
                db.add(
                    CharacterAnswer(
                        character_id=cid,
                        question_id=qid,
                        likelihood=likelihood,
                        sample_size=50,
                    )
                )

        await db.commit()
        print("Seed complete: 4 characters, 5 questions, likelihood matrix populated.")


if __name__ == "__main__":
    asyncio.run(seed())
