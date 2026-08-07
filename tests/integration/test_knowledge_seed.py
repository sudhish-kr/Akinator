"""Tests for knowledge-base seed validation and import."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, Character, CharacterAlias, CharacterAnswer, Question
from app.db.repositories.game_repository import GameRepository
from app.services.knowledge_seed import (
    KnowledgeSeedError,
    KnowledgeSeedService,
    load_seed_file,
    validate_seed_payload,
)

ROOT = Path(__file__).resolve().parents[2]
SEED_PATH = ROOT / "data" / "knowledge" / "seed_v1.json"
GENERATE_SCRIPT = ROOT / "scripts" / "generate_knowledge_seed.py"


def _load_build_seed():
    spec = importlib.util.spec_from_file_location("generate_knowledge_seed", GENERATE_SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_seed


def _mini_seed(**overrides) -> dict:
    data = {
        "version": 1,
        "categories": ["Scientists", "Sports"],
        "characters": [
            {
                "name": "Ada Lovelace",
                "category": "Scientists",
                "aliases": ["Lovelace"],
                "is_active": True,
            },
            {
                "name": "Lionel Messi",
                "category": "Sports",
                "aliases": ["Messi"],
                "is_active": True,
            },
        ],
        "questions": [
            {
                "text": "Is this a scientist or inventor?",
                "category": "domain",
                "is_active": True,
            },
            {
                "text": "Is this an athlete or sports figure?",
                "category": "domain",
                "is_active": True,
            },
        ],
        "likelihood_rules": [
            {
                "category": "Scientists",
                "question": "Is this a scientist or inventor?",
                "likelihood": 0.95,
                "sample_size": 40,
            },
            {
                "category": "Sports",
                "question": "Is this an athlete or sports figure?",
                "likelihood": 0.97,
                "sample_size": 40,
            },
        ],
        "likelihood_overrides": [
            {
                "character": "Ada Lovelace",
                "question": "Is this a scientist or inventor?",
                "likelihood": 0.99,
                "sample_size": 100,
            }
        ],
        "default_likelihood": 0.5,
        "default_sample_size": 10,
    }
    data.update(overrides)
    return data


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as session:
        yield session
    await engine.dispose()


def test_validate_rejects_duplicate_character_names():
    data = _mini_seed()
    data["characters"].append(
        {"name": "ada lovelace", "category": "Scientists", "aliases": []}
    )
    with pytest.raises(KnowledgeSeedError, match="Duplicate characters"):
        validate_seed_payload(data)


def test_validate_rejects_duplicate_aliases():
    data = _mini_seed()
    data["characters"][1]["aliases"] = ["Lovelace"]
    with pytest.raises(KnowledgeSeedError, match="Duplicate aliases"):
        validate_seed_payload(data)


def test_validate_rejects_alias_matching_character_name():
    data = _mini_seed()
    data["characters"][1]["aliases"] = ["Ada Lovelace"]
    with pytest.raises(KnowledgeSeedError, match="Aliases collide with character names"):
        validate_seed_payload(data)


def test_validate_rejects_duplicate_questions():
    data = _mini_seed()
    data["questions"].append(
        {"text": "Is this a scientist or inventor?", "category": "domain"}
    )
    with pytest.raises(KnowledgeSeedError, match="Duplicate questions"):
        validate_seed_payload(data)


def test_generated_seed_has_500_plus_characters_and_validates():
    seed = _load_build_seed()()
    assert len(seed["characters"]) >= 500
    assert len(seed["categories"]) >= 6
    assert {"Movies", "Anime", "Sports", "Scientists", "Historical", "Gaming"} <= set(
        seed["categories"]
    )
    validate_seed_payload(seed)
    assert any(c.get("aliases") for c in seed["characters"])
    assert seed["likelihood_rules"]
    assert seed["likelihood_overrides"]


def test_seed_v1_file_exists_and_is_valid():
    assert SEED_PATH.exists(), "Run scripts/generate_knowledge_seed.py to create seed_v1.json"
    data = load_seed_file(SEED_PATH)
    assert len(data["characters"]) >= 500
    validate_seed_payload(data)


@pytest.mark.asyncio
async def test_import_rejects_existing_character(db: AsyncSession):
    db.add(Character(name="Ada Lovelace", category="Scientists"))
    await db.commit()

    service = KnowledgeSeedService(GameRepository(db))
    with pytest.raises(KnowledgeSeedError, match="Characters already exist"):
        await service.import_seed(_mini_seed())


@pytest.mark.asyncio
async def test_import_rejects_existing_alias(db: AsyncSession):
    character = Character(name="Someone Else", category="Sports")
    db.add(character)
    await db.flush()
    db.add(CharacterAlias(character_id=character.id, alias="Messi"))
    await db.commit()

    service = KnowledgeSeedService(GameRepository(db))
    with pytest.raises(KnowledgeSeedError, match="Aliases already exist"):
        await service.import_seed(_mini_seed())


@pytest.mark.asyncio
async def test_import_persists_characters_aliases_and_likelihoods(db: AsyncSession):
    service = KnowledgeSeedService(GameRepository(db))
    result = await service.import_seed(_mini_seed())

    assert result["characters"] == 2
    assert result["aliases"] == 2
    assert result["questions"] == 2
    assert result["likelihoods"] == 2
    assert result["dry_run"] == 0

    chars = (await db.execute(select(Character))).scalars().all()
    assert {c.name for c in chars} == {"Ada Lovelace", "Lionel Messi"}

    aliases = (await db.execute(select(CharacterAlias))).scalars().all()
    assert {a.alias for a in aliases} == {"Lovelace", "Messi"}

    answers = (await db.execute(select(CharacterAnswer))).scalars().all()
    assert len(answers) == 2

    ada = next(c for c in chars if c.name == "Ada Lovelace")
    scientist_q = (
        await db.execute(
            select(Question).where(Question.text == "Is this a scientist or inventor?")
        )
    ).scalar_one()
    ada_answer = next(
        a
        for a in answers
        if a.character_id == ada.id and a.question_id == scientist_q.id
    )
    assert ada_answer.likelihood == pytest.approx(0.99)


@pytest.mark.asyncio
async def test_dry_run_does_not_write(db: AsyncSession):
    service = KnowledgeSeedService(GameRepository(db))
    result = await service.import_seed(_mini_seed(), dry_run=True)
    assert result["dry_run"] == 1
    assert result["characters"] == 2
    chars = (await db.execute(select(Character))).scalars().all()
    assert chars == []
