"""Integration tests for worker monitoring endpoint and job enqueue from learn."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, Character, CharacterAnswer, Question
from app.db.session import get_db
from app.main import app


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as db:
        q = Question(id=uuid.uuid4(), text="Is this a scientist?", is_active=True)
        c = Character(
            id=uuid.uuid4(), name="Albert Einstein", category="real_person", is_active=True
        )
        db.add_all([q, c])
        await db.flush()
        db.add(
            CharacterAnswer(
                character_id=c.id, question_id=q.id, likelihood=0.95, sample_size=50
            )
        )
        await db.commit()

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_health_workers_endpoint(client: AsyncClient):
    resp = await client.get("/health/workers")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["eager"] is True


@pytest.mark.asyncio
async def test_learn_queues_jobs_and_returns_fast(client: AsyncClient):
    start = (await client.post("/game/start")).json()
    session_id = start["session_id"]
    question = start["question"]

    await client.post(
        "/game/answer",
        json={"session_id": session_id, "question_id": question["id"], "answer": "yes"},
    )
    guess = (await client.get(f"/game/guess/{session_id}")).json()
    character_id = guess["character"]["id"]

    with patch(
        "app.workers.queue.enqueue_post_game",
        return_value={
            "learning_job_id": "job-learn",
            "analytics_job_id": "job-analytics",
        },
    ) as enqueue:
        learn = await client.post(
            "/game/learn",
            json={"session_id": session_id, "character_id": character_id},
        )

    assert learn.status_code == 200
    body = learn.json()
    assert body["status"] == "learned"
    assert body["updates"] == 0
    assert body["learning_job_id"] == "job-learn"
    assert body["analytics_job_id"] == "job-analytics"
    enqueue.assert_called_once()
