"""HTTP request timing, error tracking, and Prometheus labels."""

from __future__ import annotations

import logging
import time
import uuid

from starlette.requests import Request

from app.core.logging import access_logger, request_id_var
from app.monitoring.metrics import ERROR_COUNT, REQUEST_COUNT, REQUEST_LATENCY

logger = logging.getLogger("mindguess.monitoring")


def _endpoint_label(request: Request) -> str:
    route = request.scope.get("route")
    if route is not None and getattr(route, "path", None):
        return route.path
    path = request.url.path
    # Avoid high-cardinality UUIDs in metric labels
    parts = []
    for part in path.split("/"):
        if len(part) == 36 and part.count("-") == 4:
            parts.append("{id}")
        else:
            parts.append(part)
    return "/".join(parts) or "/"


async def monitoring_middleware(request: Request, call_next):
    """Record request timing + errors; preserve request-id logging behavior."""
    rid = uuid.uuid4().hex[:12]
    request_id_var.set(rid)
    endpoint = _endpoint_label(request)
    method = request.method
    start = time.perf_counter()
    status_code = 500

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as exc:
        elapsed = time.perf_counter() - start
        REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)
        REQUEST_COUNT.labels(
            method=method, endpoint=endpoint, status_code="500"
        ).inc()
        ERROR_COUNT.labels(type=type(exc).__name__, endpoint=endpoint).inc()
        logger.exception(
            "Unhandled error on %s %s",
            method,
            endpoint,
            extra={"method": method, "path": endpoint, "status_code": 500},
        )
        raise

    elapsed = time.perf_counter() - start
    duration_ms = round(elapsed * 1000, 1)
    REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(elapsed)
    REQUEST_COUNT.labels(
        method=method, endpoint=endpoint, status_code=str(status_code)
    ).inc()

    if status_code >= 500:
        ERROR_COUNT.labels(type="http_5xx", endpoint=endpoint).inc()
    elif status_code >= 400:
        ERROR_COUNT.labels(type="http_4xx", endpoint=endpoint).inc()

    access_logger.info(
        "%s %s -> %s",
        method,
        request.url.path,
        status_code,
        extra={
            "method": method,
            "path": request.url.path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        },
    )
    response.headers["X-Request-ID"] = rid
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    return response
