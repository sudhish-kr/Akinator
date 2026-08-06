"""Essential authentication tests — JWT, bcrypt, refresh, logout, RBAC."""

import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base, Character, User
from app.db.session import get_db
from app.main import app
from app.services.auth_service import hash_password, verify_password


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with factory() as db:
        db.add(
            Character(
                id=uuid.uuid4(),
                name="Test Char",
                category="real_person",
                is_active=True,
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


def test_bcrypt_password_hashing():
    hashed = hash_password("secretpass1")
    assert hashed != "secretpass1"
    assert verify_password("secretpass1", hashed)
    assert not verify_password("wrong", hashed)


@pytest.mark.asyncio
async def test_register_login_returns_jwt_pair(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"email": "a@example.com", "username": "alice", "password": "password12"},
    )
    assert reg.status_code == 201, reg.text
    body = reg.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["role"] == "user"

    login = await client.post(
        "/auth/login",
        json={"email": "a@example.com", "password": "password12"},
    )
    assert login.status_code == 200
    assert login.json()["refresh_token"]


@pytest.mark.asyncio
async def test_refresh_and_logout(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"email": "b@example.com", "username": "bob", "password": "password12"},
    )
    access = reg.json()["access_token"]
    refresh = reg.json()["refresh_token"]

    refreshed = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert refreshed.status_code == 200
    new_refresh = refreshed.json()["refresh_token"]
    assert new_refresh != refresh

    # Old refresh is rotated away
    stale = await client.post("/auth/refresh", json={"refresh_token": refresh})
    assert stale.status_code == 401

    logout = await client.post(
        "/auth/logout",
        json={"refresh_token": new_refresh},
        headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
    )
    assert logout.status_code == 200
    assert logout.json()["status"] == "logged_out"

    # Access token revoked after logout
    denied = await client.post(
        "/admin/characters",
        json={"name": "X", "category": "y"},
        headers={"Authorization": f"Bearer {refreshed.json()['access_token']}"},
    )
    assert denied.status_code in {401, 403}


@pytest.mark.asyncio
async def test_admin_apis_require_admin_role(client: AsyncClient):
    reg = await client.post(
        "/auth/register",
        json={"email": "u@example.com", "username": "user", "password": "password12"},
    )
    user_token = reg.json()["access_token"]

    forbidden = await client.post(
        "/admin/characters",
        json={"name": "Newton", "category": "real_person"},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert forbidden.status_code == 403

    unauth = await client.post(
        "/admin/characters",
        json={"name": "Newton", "category": "real_person"},
    )
    assert unauth.status_code == 401

    # Promote to admin
    override = app.dependency_overrides[get_db]
    async for db in override():
        await db.execute(
            update(User).where(User.email == "u@example.com").values(is_admin=True)
        )
        await db.commit()

    login = await client.post(
        "/auth/login",
        json={"email": "u@example.com", "password": "password12"},
    )
    admin_token = login.json()["access_token"]
    assert login.json()["user"]["role"] == "admin"

    created = await client.post(
        "/admin/characters",
        json={"name": "Newton", "category": "real_person"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert created.status_code == 201, created.text
