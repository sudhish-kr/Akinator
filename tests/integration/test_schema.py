"""Phase 1 schema tests — CHECK constraints and stale-session semantics."""

from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, Character, CharacterAnswer, GameSession, GameSessionStatus, Question
from app.db.repositories.game_repository import GameRepository


@pytest_asyncio.fixture
async def db():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with factory() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_likelihood_out_of_range_rejected(db: AsyncSession):
    character = Character(name="Test", category="real_person")
    question = Question(text="Test question?")
    db.add_all([character, question])
    await db.flush()

    db.add(
        CharacterAnswer(
            character_id=character.id,
            question_id=question.id,
            likelihood=1.5,
            sample_size=1,
        )
    )
    with pytest.raises(IntegrityError):
        await db.flush()


@pytest.mark.asyncio
async def test_negative_sample_size_rejected(db: AsyncSession):
    character = Character(name="Test", category="real_person")
    question = Question(text="Test question?")
    db.add_all([character, question])
    await db.flush()

    db.add(
        CharacterAnswer(
            character_id=character.id,
            question_id=question.id,
            likelihood=0.5,
            sample_size=-1,
        )
    )
    with pytest.raises(IntegrityError):
        await db.flush()


@pytest.mark.asyncio
async def test_stale_cleanup_uses_last_activity_not_start_time(db: AsyncSession):
    """A session started long ago but recently active must NOT be abandoned."""
    repo = GameRepository(db)
    old = datetime.now(timezone.utc) - timedelta(hours=2)

    active_game = GameSession(status=GameSessionStatus.IN_PROGRESS)
    stale_game = GameSession(status=GameSessionStatus.IN_PROGRESS)
    db.add_all([active_game, stale_game])
    await db.flush()

    # Both started 2 hours ago; only one has recent activity
    active_game.started_at = old
    active_game.last_activity_at = datetime.now(timezone.utc)
    stale_game.started_at = old
    stale_game.last_activity_at = old
    await db.flush()

    abandoned = await repo.abandon_stale_sessions(minutes=30)
    assert abandoned == 1
    assert stale_game.status == GameSessionStatus.ABANDONED
    assert active_game.status == GameSessionStatus.IN_PROGRESS
