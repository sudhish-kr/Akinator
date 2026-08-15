"""SQLAlchemy engine hooks for database query latency metrics."""

from __future__ import annotations

import logging
import time

from sqlalchemy import event

from app.monitoring.metrics import DB_QUERY_LATENCY

logger = logging.getLogger("mindguess.db")

_QUERY_START: dict[int, float] = {}


def _before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    _QUERY_START[id(cursor)] = time.perf_counter()


def _after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    start = _QUERY_START.pop(id(cursor), None)
    if start is None:
        return
    elapsed = time.perf_counter() - start
    op = "executemany" if executemany else "execute"
    # Cheap classification from SQL prefix
    sql = (statement or "").lstrip().split(None, 1)
    kind = sql[0].upper() if sql else "OTHER"
    if kind not in {"SELECT", "INSERT", "UPDATE", "DELETE", "BEGIN", "COMMIT", "ROLLBACK"}:
        kind = "OTHER"
    DB_QUERY_LATENCY.labels(operation=f"{op}:{kind}").observe(elapsed)


def instrument_engine(async_engine) -> None:
    """Attach before/after cursor listeners to an AsyncEngine's sync engine."""
    sync_engine = async_engine.sync_engine
    # Avoid double-registration on reload
    if getattr(sync_engine, "_mindguess_metrics_instrumented", False):
        return
    event.listen(sync_engine, "before_cursor_execute", _before_cursor_execute)
    event.listen(sync_engine, "after_cursor_execute", _after_cursor_execute)
    sync_engine._mindguess_metrics_instrumented = True  # type: ignore[attr-defined]
    logger.debug("Database query latency instrumentation enabled")
