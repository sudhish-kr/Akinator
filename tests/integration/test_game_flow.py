"""Integration tests — full game flow over the HTTP API with a fresh SQLite DB."""

import uuid

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
    "Elon Musk": {"alive": 0.95, "scientist": 0.55},
    "Cristiano Ronaldo": {"alive": 0.95, "scientist": 0.02},
}

QUESTIONS = {
    "alive": "Is this person alive today?",
    "scientist": "Is this person a scientist?",
}


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as db:
        q_ids = {}
        for key, text in QUESTIONS.items():
            q = Question(id=uuid.uuid4(), text=text, is_active=True)
            db.add(q)
            q_ids[key] = q.id

        for name, likelihoods in CHARACTERS.items():
            c = Character(id=uuid.uuid4(), name=name, category="real_person", is_active=True)
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


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient) -> str:
    """Register a user, then promote to admin directly in the test DB."""
    from sqlalchemy import update

    from app.db.models import User
    from app.main import app

    reg = await client.post(
        "/auth/register",
        json={"email": "admin@example.com", "username": "admin", "password": "adminpass123"},
    )
    token = reg.json()["access_token"]

    override = app.dependency_overrides[get_db]
    async for db in override():
        await db.execute(
            update(User).where(User.email == "admin@example.com").values(is_admin=True)
        )
        await db.commit()
    return token


async def _play_until_guess(client: AsyncClient, answers_by_text: dict[str, str]) -> dict:
    start = (await client.post("/game/start")).json()
    session_id = start["session_id"]
    question = start["question"]

    for _ in range(30):
        answer = answers_by_text.get(question["text"], "dont_know")
        resp = await client.post(
            "/game/answer",
            json={"session_id": session_id, "question_id": question["id"], "answer": answer},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        if data["status"] == "ready_to_guess":
            return {"session_id": session_id}
        question = data["next_question"]

    raise AssertionError("Game never became ready to guess")


@pytest.mark.asyncio
async def test_full_game_correct_guess(client: AsyncClient):
    """Think of Einstein: dead scientist → engine should guess Einstein."""
    result = await _play_until_guess(
        client,
        {
            "Is this person alive today?": "no",
            "Is this person a scientist?": "yes",
        },
    )

    guess = await client.get(f"/game/guess/{result['session_id']}")
    assert guess.status_code == 200
    assert guess.json()["character"]["name"] == "Albert Einstein"

    confirm = await client.post(
        "/game/guess/confirm",
        json={"session_id": result["session_id"], "correct": True},
    )
    assert confirm.status_code == 200
    assert confirm.json()["status"] == "guessed_correct"


@pytest.mark.asyncio
async def test_guess_before_ready_is_rejected(client: AsyncClient):
    start = (await client.post("/game/start")).json()
    resp = await client.get(f"/game/guess/{start['session_id']}")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_invalid_answer_rejected(client: AsyncClient):
    start = (await client.post("/game/start")).json()
    resp = await client.post(
        "/game/answer",
        json={
            "session_id": start["session_id"],
            "question_id": start["question"]["id"],
            "answer": "maybe",
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_auth_register_and_login(client: AsyncClient):
    register = await client.post(
        "/auth/register",
        json={"email": "ankit@example.com", "username": "ankit", "password": "supersecret1"},
    )
    assert register.status_code == 201, register.text
    token = register.json()["access_token"]
    assert token

    login = await client.post(
        "/auth/login",
        json={"email": "ankit@example.com", "password": "supersecret1"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["username"] == "ankit"

    bad_login = await client.post(
        "/auth/login",
        json={"email": "ankit@example.com", "password": "wrongpassword"},
    )
    assert bad_login.status_code == 401


@pytest.mark.asyncio
async def test_questions_exhausted_forces_guess(client: AsyncClient):
    """Answering every question with 'dont_know' must end in ready_to_guess, not a 500."""
    start = (await client.post("/game/start")).json()
    session_id = start["session_id"]
    question = start["question"]

    final_status = None
    for _ in range(10):
        resp = await client.post(
            "/game/answer",
            json={"session_id": session_id, "question_id": question["id"], "answer": "dont_know"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        final_status = data["status"]
        if final_status == "ready_to_guess":
            break
        question = data["next_question"]

    assert final_status == "ready_to_guess"
    guess = await client.get(f"/game/guess/{session_id}")
    assert guess.status_code == 200
    assert guess.json()["character"]["name"]


@pytest.mark.asyncio
async def test_state_endpoint_resyncs(client: AsyncClient):
    start = (await client.post("/game/start")).json()
    state = await client.get(f"/game/state/{start['session_id']}")
    assert state.status_code == 200
    data = state.json()
    assert data["status"] == "asking"
    assert data["next_question"]["id"] == start["question"]["id"]


@pytest.mark.asyncio
async def test_session_rehydrates_after_cache_loss(client: AsyncClient):
    """Simulates a server restart: cache wiped mid-game, state must rebuild
    from the game_answers log and the game must continue."""
    from app.services.session_store import session_store

    start = (await client.post("/game/start")).json()
    session_id = start["session_id"]
    question = start["question"]

    resp = await client.post(
        "/game/answer",
        json={"session_id": session_id, "question_id": question["id"], "answer": "yes"},
    )
    assert resp.status_code == 200
    next_question = resp.json()["next_question"]

    # Wipe the in-memory session cache (what a restart would do)
    session_store.delete(uuid.UUID(session_id))

    # State endpoint must rehydrate from DB, not 404
    state = await client.get(f"/game/state/{session_id}")
    assert state.status_code == 200
    data = state.json()
    assert data["questions_asked"] == 1

    # And the game continues where it left off
    if data["status"] == "asking":
        resp = await client.post(
            "/game/answer",
            json={
                "session_id": session_id,
                "question_id": data["next_question"]["id"],
                "answer": "no",
            },
        )
        assert resp.status_code == 200


@pytest.mark.asyncio
async def test_rejected_guess_not_reguessed_after_cache_loss(client: AsyncClient):
    """A character rejected by the user must stay excluded even after the
    session cache is wiped and state is rebuilt from the database."""
    from app.services.session_store import session_store

    result = await _play_until_guess(
        client,
        {
            "Is this person alive today?": "no",
            "Is this person a scientist?": "yes",
        },
    )
    session_id = result["session_id"]

    guess = await client.get(f"/game/guess/{session_id}")
    assert guess.status_code == 200
    assert guess.json()["character"]["name"] == "Albert Einstein"

    chars = (await client.get("/characters?is_active=true")).json()["items"]
    musk_id = next(c["id"] for c in chars if c["name"] == "Elon Musk")

    confirm = await client.post(
        "/game/guess/confirm",
        json={"session_id": session_id, "correct": False, "actual_character_id": musk_id},
    )
    assert confirm.status_code == 200

    # Simulate a restart: wipe the cache, forcing DB rehydration
    session_store.delete(uuid.UUID(session_id))

    state = await client.get(f"/game/state/{session_id}")
    assert state.status_code == 200
    data = state.json()

    # Play out any remaining questions, then guess
    for _ in range(10):
        if data["status"] == "ready_to_guess":
            break
        resp = await client.post(
            "/game/answer",
            json={
                "session_id": session_id,
                "question_id": data["next_question"]["id"],
                "answer": "dont_know",
            },
        )
        assert resp.status_code == 200
        data = resp.json()

    guess2 = await client.get(f"/game/guess/{session_id}")
    assert guess2.status_code == 200
    assert guess2.json()["character"]["name"] != "Albert Einstein"


@pytest.mark.asyncio
async def test_admin_crud_requires_admin(client: AsyncClient):
    # Regular user is forbidden
    reg = await client.post(
        "/auth/register",
        json={"email": "user@example.com", "username": "user", "password": "password123"},
    )
    user_token = reg.json()["access_token"]
    resp = await client.post(
        "/admin/characters",
        json={"name": "Newton", "category": "real_person"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert resp.status_code == 403

    # No token at all is unauthorized
    resp = await client.post("/admin/characters", json={"name": "X", "category": "y"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_admin_can_create_and_update(client: AsyncClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}

    created = await client.post(
        "/admin/characters",
        json={"name": "Isaac Newton", "category": "real_person"},
        headers=headers,
    )
    assert created.status_code == 201, created.text
    char_id = created.json()["id"]

    updated = await client.patch(
        f"/admin/characters/{char_id}",
        json={"is_active": False},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["is_active"] is False

    q = await client.post(
        "/admin/questions",
        json={"text": "Did this person live before 1900?", "category": "history"},
        headers=headers,
    )
    assert q.status_code == 201


@pytest.mark.asyncio
async def test_suggest_character_creates_inactive(client: AsyncClient):
    start = (await client.post("/game/start")).json()
    resp = await client.post(
        "/game/suggest-character",
        json={"session_id": start["session_id"], "name": "Nikola Tesla", "category": "real_person"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "submitted_for_review"

    # Suggested character must NOT appear in active play pool
    chars = (await client.get("/characters?is_active=true")).json()
    names = [c["name"] for c in chars["items"]]
    assert "Nikola Tesla" not in names


@pytest.mark.asyncio
async def test_statistics_endpoint(client: AsyncClient):
    resp = await client.get("/statistics")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_games_played" in data
    assert "guess_accuracy_rate" in data
