"""Unit tests for process-level playable catalog cache."""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.engine.models import LikelihoodEntry, QuestionRef
from app.services import playable_catalog as mod
from app.services.playable_catalog import (
    PlayableCatalog,
    get_playable_catalog,
    invalidate_playable_catalog,
    peek_likelihoods,
)


class _FakeBind:
    pass


class _FakeDb:
    def __init__(self):
        self._bind = _FakeBind()

    def get_bind(self):
        return self._bind


class _Char:
    def __init__(self, cid, name, category="Sports", popularity=1):
        self.id = cid
        self.name = name
        self.category = category
        self.popularity_score = popularity


class _Question:
    def __init__(self, qid, text, category="Bio"):
        self.id = qid
        self.text = text
        self.category = category


class FakeRepo:
    def __init__(self, characters, questions, rows):
        self.db = _FakeDb()
        self.characters = characters
        self.questions = questions
        self.rows = rows
        self.list_calls = 0
        self.iter_calls = 0

    async def get_active_characters(self):
        return list(self.characters)

    async def get_active_questions(self):
        return list(self.questions)

    async def get_active_likelihood_rows(self):
        self.list_calls += 1
        return list(self.rows)

    async def iter_active_likelihood_rows(self, *, batch_size: int = 5000):
        self.iter_calls += 1
        for row in self.rows:
            yield row


class ListOnlyRepo:
    def __init__(self, characters, questions, rows):
        self.db = _FakeDb()
        self.characters = characters
        self.questions = questions
        self.rows = rows
        self.list_calls = 0

    async def get_active_characters(self):
        return list(self.characters)

    async def get_active_questions(self):
        return list(self.questions)

    async def get_active_likelihood_rows(self):
        self.list_calls += 1
        return list(self.rows)


@pytest.fixture(autouse=True)
def _reset():
    mod._catalog = None
    yield
    mod._catalog = None


def test_peek_likelihoods_none_until_warmed():
    assert peek_likelihoods() is None


def test_invalidate_clears_catalog():
    cid, qid = uuid4(), uuid4()
    mod._catalog = PlayableCatalog(
        character_ids=[cid],
        question_ids=[qid],
        likelihoods={(cid, qid): LikelihoodEntry(0.9, 10)},
        question_refs={qid: QuestionRef(id=qid, text="Alive?", category="Age")},
        character_names={cid: "Test"},
        character_categories={cid: "Sports"},
        character_popularity={cid: 1},
        character_count=1,
        question_count=1,
        likelihood_count=1,
    )
    assert peek_likelihoods() is not None
    invalidate_playable_catalog()
    assert peek_likelihoods() is None


@pytest.mark.asyncio
async def test_catalog_streams_rows_and_interns_uuids():
    cid, qid = uuid4(), uuid4()
    cid_row = UUID(str(cid))
    qid_row = UUID(str(qid))
    assert cid_row == cid and cid_row is not cid

    repo = FakeRepo(
        characters=[_Char(cid, "Virat")],
        questions=[_Question(qid, "Do they play cricket?")],
        rows=[(cid_row, qid_row, 0.92, 12)],
    )
    catalog = await get_playable_catalog(repo, ttl_seconds=60)
    assert repo.iter_calls == 1
    assert repo.list_calls == 0
    assert catalog.character_count == 1
    assert catalog.question_count == 1
    assert catalog.likelihood_count == 1
    stored_cid, stored_qid = next(iter(catalog.likelihoods))
    assert stored_cid is catalog.character_ids[0]
    assert stored_qid is catalog.question_ids[0]
    assert catalog.likelihoods[(cid, qid)].likelihood == 0.92
    assert catalog.question_sample_totals[qid] == 12


@pytest.mark.asyncio
async def test_catalog_does_not_reload_while_fresh():
    cid, qid = uuid4(), uuid4()
    repo = FakeRepo(
        characters=[_Char(cid, "A")],
        questions=[_Question(qid, "Q?")],
        rows=[(cid, qid, 0.4, 8)],
    )
    first = await get_playable_catalog(repo, ttl_seconds=600)
    second = await get_playable_catalog(repo, ttl_seconds=600)
    assert first is second
    assert repo.iter_calls == 1


@pytest.mark.asyncio
async def test_catalog_falls_back_to_list_loader():
    cid, qid = uuid4(), uuid4()
    repo = ListOnlyRepo(
        characters=[_Char(cid, "A")],
        questions=[_Question(qid, "Q?")],
        rows=[(cid, qid, 0.7, 5)],
    )
    catalog = await get_playable_catalog(repo, ttl_seconds=60)
    assert repo.list_calls == 1
    assert catalog.likelihood_count == 1


def test_lifespan_does_not_warm_catalog_at_startup():
    from pathlib import Path

    src = Path(__file__).resolve().parents[2] / "app" / "main.py"
    text = src.read_text(encoding="utf-8")
    assert "_warm_playable_catalog" not in text
    assert "get_playable_catalog" not in text


@pytest.mark.asyncio
async def test_repository_streams_likelihood_rows_in_batches():
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.db.models import Base, Character, CharacterAnswer, Question
    from app.db.repositories.game_repository import GameRepository

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    cid_a, cid_b, qid = uuid4(), uuid4(), uuid4()
    async with factory() as db:
        db.add(Character(id=cid_a, name="A", category="Sports", is_active=True))
        db.add(Character(id=cid_b, name="B", category="Sports", is_active=True))
        db.add(Question(id=qid, text="Q?", category="Bio", is_active=True))
        db.add(
            CharacterAnswer(
                character_id=cid_a, question_id=qid, likelihood=0.8, sample_size=9
            )
        )
        db.add(
            CharacterAnswer(
                character_id=cid_b, question_id=qid, likelihood=0.2, sample_size=11
            )
        )
        await db.commit()

    async with factory() as db:
        repo = GameRepository(db)
        streamed = [
            row async for row in repo.iter_active_likelihood_rows(batch_size=1)
        ]

    await engine.dispose()
    pairs = {(row[0], round(row[2], 2), row[3]) for row in streamed}
    assert len(streamed) == 2
    assert (cid_a, 0.8, 9) in pairs
    assert (cid_b, 0.2, 11) in pairs


@pytest.mark.asyncio
async def test_likelihood_iter_does_not_open_sqlalchemy_stream():
    from unittest.mock import AsyncMock

    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from app.db.models import Base, Character, CharacterAnswer, Question
    from app.db.repositories.game_repository import GameRepository

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    cid, qid = uuid4(), uuid4()
    async with factory() as db:
        db.add(Character(id=cid, name="A", category="Sports", is_active=True))
        db.add(Question(id=qid, text="Q?", category="Bio", is_active=True))
        db.add(
            CharacterAnswer(
                character_id=cid, question_id=qid, likelihood=0.5, sample_size=3
            )
        )
        await db.commit()

    async with factory() as db:
        db.stream = AsyncMock(side_effect=AssertionError("must not use stream()"))
        repo = GameRepository(db)
        rows = [row async for row in repo.iter_active_likelihood_rows(batch_size=1)]

    await engine.dispose()
    assert len(rows) == 1
    assert rows[0][0] == cid
    db.stream.assert_not_called()
