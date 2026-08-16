"""Worker / queue monitoring for ops dashboards."""

from __future__ import annotations

from typing import Any

from app.config import settings
from app.workers.celery_app import celery_app


def get_worker_status(*, ping_timeout: float = 1.0) -> dict[str, Any]:
    """
    Snapshot of Celery worker health for GET /health/workers.

    Never raises — degraded states are reported in the payload.
    """
    broker = settings.celery_broker_url or settings.redis_url
    payload: dict[str, Any] = {
        "status": "unknown",
        "broker": broker,
        "eager": settings.celery_task_always_eager,
        "workers": [],
        "active_tasks": 0,
        "reserved_tasks": 0,
        "scheduled_tasks": 0,
        "stats": {},
        "error": None,
    }

    if settings.celery_task_always_eager:
        payload["status"] = "ok"
        payload["workers"] = ["eager-in-process"]
        return payload

    try:
        inspector = celery_app.control.inspect(timeout=ping_timeout)
        ping = inspector.ping() or {}
        workers = sorted(ping.keys())
        payload["workers"] = workers
        if not workers:
            payload["status"] = "degraded"
            payload["error"] = "No Celery workers responded to ping"
            return payload

        active = inspector.active() or {}
        reserved = inspector.reserved() or {}
        scheduled = inspector.scheduled() or {}
        stats = inspector.stats() or {}

        payload["active_tasks"] = sum(len(v or []) for v in active.values())
        payload["reserved_tasks"] = sum(len(v or []) for v in reserved.values())
        payload["scheduled_tasks"] = sum(len(v or []) for v in scheduled.values())
        payload["stats"] = {
            name: {
                "pool": (info or {}).get("pool", {}).get("implementation"),
                "total": (info or {}).get("total"),
            }
            for name, info in stats.items()
        }
        payload["status"] = "ok"
    except Exception as exc:  # noqa: BLE001 — monitoring must not crash the API
        payload["status"] = "unavailable"
        payload["error"] = str(exc)

    return payload
