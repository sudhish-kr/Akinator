"""Normalize DATABASE_URL for SQLAlchemy AsyncEngine + asyncpg.

Render / Neon URLs commonly include libpq query params such as
``sslmode=require`` and ``channel_binding=require``. asyncpg.Connection
rejects those keywords (``connect() got an unexpected keyword argument
'sslmode'``). SSL is preserved via asyncpg's ``ssl=True``.
"""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

_SSL_DISABLE = frozenset({"disable", "false", "0", "off"})
_LIBPQ_STRIP = frozenset(
    {
        "sslmode",
        "ssl",
        "channel_binding",
        "channelbinding",
        "gssencmode",
    }
)


def normalize_asyncpg_url(url: str) -> tuple[str, dict[str, Any]]:
    """Return ``(sqlalchemy_async_url, connect_args)`` for ``create_async_engine``.

    * ``postgres://`` and ``postgresql://`` become ``postgresql+asyncpg://``
    * libpq-only query params are dropped (asyncpg does not accept them)
    * Neon / ``sslmode=require`` still enables TLS via ``connect_args['ssl']``
    * Neon pooler hosts disable asyncpg's prepared-statement cache
    """
    connect_args: dict[str, Any] = {}
    if not url:
        return url, connect_args

    if url.startswith("sqlite"):
        return url, {"timeout": 30}

    raw = url
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    if raw.startswith("postgresql://"):
        raw = "postgresql+asyncpg://" + raw[len("postgresql://") :]

    if not raw.startswith("postgresql+asyncpg://"):
        return url, connect_args

    parsed = urlparse(raw)
    kept: list[tuple[str, str]] = []
    ssl_mode: str | None = None
    for key, value in parse_qsl(parsed.query, keep_blank_values=True):
        lowered = key.casefold()
        if lowered in {"sslmode", "ssl"}:
            ssl_mode = (value or "").casefold()
            continue
        if lowered in _LIBPQ_STRIP:
            continue
        kept.append((key, value))

    host = (parsed.hostname or "").casefold()
    if ssl_mode is not None:
        if ssl_mode not in _SSL_DISABLE:
            connect_args["ssl"] = True
    elif "neon.tech" in host:
        connect_args["ssl"] = True

    if "pooler" in host:
        connect_args["statement_cache_size"] = 0

    rebuilt = parsed._replace(query=urlencode(kept))
    return urlunparse(rebuilt), connect_args
