"""Asyncpg DATABASE_URL / SSL normalization."""

from __future__ import annotations

from sqlalchemy.engine.url import make_url

from app.db.url import normalize_asyncpg_url

NEON_RENDER = (
    "postgresql://owner:secret@ep-x-pooler.us-east-2.aws.neon.tech/neondb"
    "?sslmode=require&channel_binding=require"
)


def test_neon_render_url_drops_libpq_params_and_keeps_tls():
    url, args = normalize_asyncpg_url(NEON_RENDER)
    parsed = make_url(url)
    assert parsed.drivername == "postgresql+asyncpg"
    assert "sslmode" not in parsed.query
    assert "channel_binding" not in parsed.query
    assert "sslmode" not in url
    assert "channel_binding" not in url
    assert args.get("ssl") is True
    assert args.get("statement_cache_size") == 0
    assert parsed.password == "secret"


def test_postgres_scheme_and_existing_asyncpg_sslmode():
    url, args = normalize_asyncpg_url(
        "postgres://u:p@ep-demo.neon.tech/db?sslmode=require"
    )
    assert url.startswith("postgresql+asyncpg://")
    assert "sslmode" not in url
    assert args["ssl"] is True

    url2, args2 = normalize_asyncpg_url(
        "postgresql+asyncpg://u:p@ep-demo.neon.tech/db?sslmode=verify-full&ssl=true"
    )
    assert "sslmode" not in url2
    assert args2["ssl"] is True


def test_local_postgres_has_no_forced_ssl():
    local = "postgresql+asyncpg://mindguess:mindguess@localhost:5432/mindguess"
    url, args = normalize_asyncpg_url(local)
    assert url == local
    assert "ssl" not in args


def test_sslmode_disable_does_not_enable_tls():
    url, args = normalize_asyncpg_url(
        "postgresql://mindguess:mindguess@localhost:5432/mindguess?sslmode=disable"
    )
    assert url.startswith("postgresql+asyncpg://")
    assert "sslmode" not in url
    assert "ssl" not in args


def test_sqlite_keeps_timeout_connect_args():
    url, args = normalize_asyncpg_url("sqlite+aiosqlite:///./mindguess_dev.db")
    assert url.startswith("sqlite")
    assert args == {"timeout": 30}
