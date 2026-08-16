"""Health checks with database latency measurement."""

from __future__ import annotations

import time
from typing import Any

from sqlalchemy import text

from app.config import settings
from app.db.session import async_session_factory
from app.monitoring.metrics import DB_HEALTH_LATENCY, DB_QUERY_LATENCY


async def check_database() -> dict[str, Any]:
    """Ping the database and record latency gauges/histograms."""
    start = time.perf_counter()
    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        latency = time.perf_counter() - start
        DB_HEALTH_LATENCY.set(latency)
        DB_QUERY_LATENCY.labels(operation="healthcheck").observe(latency)
        return {"status": "ok", "latency_seconds": round(latency, 6)}
    except Exception as exc:  # noqa: BLE001
        latency = time.perf_counter() - start
        DB_HEALTH_LATENCY.set(latency)
        DB_QUERY_LATENCY.labels(operation="healthcheck").observe(latency)
        return {
            "status": "error",
            "latency_seconds": round(latency, 6),
            "error": str(exc),
        }


async def build_health_report(*, include_workers: bool = False) -> dict[str, Any]:
    """Aggregate liveness-style health for GET /health."""
    db = await check_database()
    workers = None
    if include_workers:
        from app.workers.monitoring import get_worker_status

        workers = get_worker_status()
    overall = "ok"
    if db["status"] != "ok":
        overall = "degraded"
    elif workers and workers.get("status") not in {"ok", "unknown"} and not settings.celery_task_always_eager:
        # Workers degraded should not fail bare liveness, but surface in report
        overall = "degraded" if workers.get("status") == "degraded" else overall

    report: dict[str, Any] = {
        "status": overall,
        "environment": settings.environment,
        "app": settings.app_name,
        "checks": {
            "database": db,
        },
    }
    if workers is not None:
        report["checks"]["workers"] = {
            "status": workers.get("status"),
            "workers": workers.get("workers"),
            "active_tasks": workers.get("active_tasks"),
            "error": workers.get("error"),
        }
    return report
