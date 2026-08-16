"""Tests for rate limiting (auth/game, per-IP / per-user, admin config)."""

from __future__ import annotations

import uuid
from unittest.mock import patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, Character, CharacterAnswer, Question, User
from app.db.session import get_db
from app.main import app
from app.security.middleware import resolve_scope
from app.security.rate_limit_backend import MemoryRateLimitBackend
from app.security.rate_limit_policy import RateLimitPolicy
from app.security.rate_limiter import RateLimiter
from app.services.auth_service import hash_password


@pytest.fixture
def memory_limiter():
    backend = MemoryRateLimitBackend()
    policy = RateLimitPolicy(
        enabled=True,
        auth_ip_limit=3,
        auth_ip_window_seconds=60,
        auth_user_limit=5,
        auth_user_window_seconds=60,
        game_ip_limit=3,
        game_ip_window_seconds=60,
        game_user_limit=5,
        game_user_window_seconds=60,
    )
    return RateLimiter(backend=backend, policy=policy)


def test_resolve_scope():
    assert resolve_scope("/auth/login") == "auth"
    assert resolve_scope("/game/start") == "game"
    assert resolve_scope("/health") is None
    assert resolve_scope("/admin/rate-limits") is None


def test_per_ip_limit_blocks(memory_limiter: RateLimiter):
    for _ in range(3):
        assert memory_limiter.check(scope="auth", client_ip="1.2.3.4").allowed
    blocked = memory_limiter.check(scope="auth", client_ip="1.2.3.4")
    assert blocked.allowed is False
    assert blocked.limiting_scope == "ip"
    assert blocked.retry_after_seconds >= 1


def test_per_user_limit_blocks(memory_limiter: RateLimiter):
    for i in range(5):
        d = memory_limiter.check(scope="game", client_ip=f"10.0.0.{i}", user_id="user-1")
        assert d.allowed
    blocked = memory_limiter.check(scope="game", client_ip="10.0.0.99", user_id="user-1")
    assert blocked.allowed is False
    assert blocked.limiting_scope == "user"


def test_admin_policy_override(memory_limiter: RateLimiter):
    memory_limiter.set_policy(
        RateLimitPolicy(
            enabled=True,
            auth_ip_limit=1,
            auth_ip_window_seconds=60,
            auth_user_limit=100,
            auth_user_window_seconds=60,
            game_ip_limit=100,
            game_ip_window_seconds=60,
            game_user_limit=100,
            game_user_window_seconds=60,
        )
    )
    assert memory_limiter.check(scope="auth", client_ip="9.9.9.9").allowed
    assert memory_limiter.check(scope="auth", client_ip="9.9.9.9").allowed is False


def test_disabled_policy_allows_all(memory_limiter: RateLimiter):
    memory_limiter.set_policy(RateLimitPolicy(enabled=False))
    for _ in range(20):
        assert memory_limiter.check(scope="auth", client_ip="1.1.1.1").allowed


@pytest_asyncio.fixture
async def client(memory_limiter: RateLimiter):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as db:
        q = Question(id=uuid.uuid4(), text="Is this a scientist?", is_active=True)
        c = Character(
            id=uuid.uuid4(), name="Albert Einstein", category="real_person", is_active=True
        )
        admin = User(
            id=uuid.uuid4(),
            email="admin@example.com",
            username="admin",
            password_hash=hash_password("adminpass123"),
            is_admin=True,
        )
        db.add_all([q, c, admin])
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

    with (
        patch("app.security.middleware.rate_limiter", memory_limiter),
        patch("app.api.routes.admin.rate_limiter", memory_limiter),
    ):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac, memory_limiter

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_auth_endpoint_rate_limited(client):
    ac, _limiter = client
    for _ in range(3):
        resp = await ac.post(
            "/auth/login",
            json={"email": "nobody@example.com", "password": "wrongpassword1"},
        )
        assert resp.status_code in {401, 422, 429}
    resp = await ac.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "wrongpassword1"},
    )
    assert resp.status_code == 429
    assert resp.headers.get("Retry-After")
    assert resp.json()["detail"] == "Rate limit exceeded"


@pytest.mark.asyncio
async def test_game_endpoint_rate_limited(client):
    ac, limiter = client
    limiter._backend.clear()
    for _ in range(3):
        resp = await ac.post("/game/start")
        assert resp.status_code == 200
        assert "X-RateLimit-Remaining" in resp.headers
    resp = await ac.post("/game/start")
    assert resp.status_code == 429


@pytest.mark.asyncio
async def test_options_preflight_does_not_consume_game_limit(client):
    ac, limiter = client
    limiter._backend.clear()
    for _ in range(5):
        await ac.options(
            "/game/start",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "POST",
            },
        )
    resp = await ac.post("/game/start")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_admin_can_configure_rate_limits(client):
    ac, limiter = client
    limiter._backend.clear()
    login = await ac.post(
        "/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    current = await ac.get("/admin/rate-limits", headers=headers)
    assert current.status_code == 200
    assert current.json()["auth_ip_limit"] == 3

    updated = await ac.put(
        "/admin/rate-limits",
        headers=headers,
        json={"auth_ip_limit": 50, "game_ip_limit": 50},
    )
    assert updated.status_code == 200
    assert updated.json()["auth_ip_limit"] == 50
    assert updated.json()["game_ip_limit"] == 50
    assert limiter.get_policy().auth_ip_limit == 50
