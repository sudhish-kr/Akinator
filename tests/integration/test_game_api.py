"""Minimal API tests for the Game REST endpoints."""

import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, Character, CharacterAnswer, Question
from app.db.session import get_db
from app.main import app

CHARACTERS = {
    "Albert Einstein": {"alive": 0.0, "scientist": 0.95},
    "Lionel Messi": {"alive": 0.95, "scientist": 0.02},
}
QUESTIONS = {
    "alive": ("Is this person alive today?", "Age"),
    "scientist": ("Is this person a scientist?", "Science"),
}


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as db:
        q_ids = {}
        for key, (text, category) in QUESTIONS.items():
            q = Question(id=uuid.uuid4(), text=text, category=category, is_active=True)
            db.add(q)
            q_ids[key] = q.id
        for name, likelihoods in CHARACTERS.items():
            c = Character(
                id=uuid.uuid4(),
                name=name,
                category="Scientists" if name == "Albert Einstein" else "Sports",
                is_active=True,
                popularity_score=90,
            )
            db.add(c)
            for key, value in likelihoods.items():
                db.add(
                    CharacterAnswer(
                        character_id=c.id,
                        question_id=q_ids[key],
                        likelihood=value,
                        sample_size=100,
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
async def test_post_game_start(client: AsyncClient):
    resp = await client.post("/game/start")
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "id" in data["question"] and "text" in data["question"]
    assert "top_confidence" in data
    assert data["top_confidence"] > 0


@pytest.mark.asyncio
async def test_post_answer_and_get_state(client: AsyncClient):
    start = (await client.post("/game/start")).json()
    session_id = start["session_id"]
    start_conf = start["top_confidence"]

    state = await client.get(f"/game/state/{session_id}")
    assert state.status_code == 200
    assert state.json()["status"] == "asking"
    assert state.json()["next_question"]["id"] == start["question"]["id"]
    assert state.json()["top_confidence"] > 0

    answer = await client.post(
        "/game/answer",
        json={
            "session_id": session_id,
            "question_id": start["question"]["id"],
            "answer": "yes",
        },
    )
    assert answer.status_code == 200
    body = answer.json()
    assert body["status"] in {"asking", "ready_to_guess"}
    assert "top_confidence" in body
    assert body["top_confidence"] != pytest.approx(start_conf, abs=1e-9) or body[
        "status"
    ] == "ready_to_guess"

@pytest.mark.asyncio
async def test_get_guess_and_post_learn(client: AsyncClient):
    start = (await client.post("/game/start")).json()
    session_id = start["session_id"]
    question = start["question"]

    # Exhaustive dont_know → ready_to_guess
    for _ in range(10):
        resp = await client.post(
            "/game/answer",
            json={"session_id": session_id, "question_id": question["id"], "answer": "dont_know"},
        )
        data = resp.json()
        if data["status"] == "ready_to_guess":
            break
        question = data["next_question"]

    guess = await client.get(f"/game/guess/{session_id}")
    assert guess.status_code == 200
    body = guess.json()
    assert body["character"]["name"]
    assert 0.0 <= body["confidence"] <= 1.0
    assert 0.0 <= body["confidence_percent"] <= 100.0
    assert isinstance(body["summary"], str) and body["summary"]
    assert isinstance(body["top_candidates"], list)
    assert 1 <= len(body["top_candidates"]) <= 5
    assert isinstance(body["influential_questions"], list)
    assert len(body["influential_questions"]) <= 5
    assert body["top_candidates"][0]["id"] == body["character"]["id"]

    learn = await client.post(
        "/game/learn",
        json={"session_id": session_id, "character_id": body["character"]["id"]},
    )
    assert learn.status_code == 200
    assert learn.json()["status"] == "learned"
    assert learn.json()["updates"] >= 0


@pytest.mark.asyncio
async def test_yes_you_got_it_confirm_accepts_null_actual_character_id(client: AsyncClient):
    """Frontend Yes button historically sent actual_character_id: null."""
    start = (await client.post("/game/start")).json()
    session_id = start["session_id"]
    question = start["question"]
    for _ in range(12):
        resp = await client.post(
            "/game/answer",
            json={"session_id": session_id, "question_id": question["id"], "answer": "dont_know"},
        )
        data = resp.json()
        if data["status"] == "ready_to_guess":
            break
        question = data["next_question"]

    guess = await client.get(f"/game/guess/{session_id}")
    assert guess.status_code == 200
    character_id = guess.json()["character"]["id"]

    confirm = await client.post(
        "/game/guess/confirm",
        json={"session_id": session_id, "correct": True, "actual_character_id": None},
    )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["status"] == "guessed_correct"

    again = await client.post(
        "/game/guess/confirm",
        json={
            "session_id": session_id,
            "correct": True,
            "actual_character_id": character_id,
        },
    )
    assert again.status_code in {200, 409}


@pytest.mark.asyncio
async def test_yes_you_got_it_survives_post_game_job_failure(client: AsyncClient):
    """Confirm must return 200 even if Celery/asyncpg post-game jobs explode."""
    start = (await client.post("/game/start")).json()
    session_id = start["session_id"]
    question = start["question"]
    for _ in range(12):
        resp = await client.post(
            "/game/answer",
            json={"session_id": session_id, "question_id": question["id"], "answer": "dont_know"},
        )
        data = resp.json()
        if data["status"] == "ready_to_guess":
            break
        question = data["next_question"]

    guess = await client.get(f"/game/guess/{session_id}")
    assert guess.status_code == 200

    with patch(
        "app.workers.queue.enqueue_post_game",
        side_effect=RuntimeError("Task got Future attached to a different loop"),
    ):
        confirm = await client.post(
            "/game/guess/confirm",
            json={"session_id": session_id, "correct": True, "actual_character_id": None},
        )
    assert confirm.status_code == 200, confirm.text
    assert confirm.json()["status"] == "guessed_correct"
