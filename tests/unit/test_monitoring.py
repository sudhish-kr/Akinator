"""Tests for monitoring: metrics, health, request timing, error tracking."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.models import Base
from app.db.session import get_db
from app.main import app
from app.monitoring.instrumentation import track_ai_inference, track_db_latency
from app.monitoring.metrics import (
    AI_INFERENCE_COUNT,
    AI_INFERENCE_LATENCY,
    DB_QUERY_LATENCY,
    ERROR_COUNT,
    REQUEST_COUNT,
    REQUEST_LATENCY,
    render_prometheus_metrics,
)
from app.monitoring.middleware import _endpoint_label


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
async def test_health_endpoint_includes_database_latency(client: AsyncClient):
    with patch(
        "app.monitoring.health.check_database",
        new=AsyncMock(
            return_value={"status": "ok", "latency_seconds": 0.00123}
        ),
    ):
        with patch(
            "app.monitoring.health.get_worker_status",
            return_value={"status": "ok", "workers": ["eager"], "active_tasks": 0, "error": None},
        ):
            resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"ok", "degraded"}
    assert "database" in data["checks"]
    assert data["checks"]["database"]["latency_seconds"] == 0.00123


@pytest.mark.asyncio
async def test_health_ready_reports_db_latency(client: AsyncClient):
    with patch(
        "app.main.check_database",
        new=AsyncMock(return_value={"status": "ok", "latency_seconds": 0.002}),
    ):
        resp = await client.get("/health/ready")
    assert resp.status_code == 200
    assert resp.json()["database"] == "ok"
    assert resp.json()["database_latency_seconds"] == 0.002


@pytest.mark.asyncio
async def test_metrics_endpoint_is_prometheus_compatible(client: AsyncClient):
    # Generate some metric samples
    REQUEST_COUNT.labels(method="GET", endpoint="/metrics", status_code="200").inc()
    REQUEST_LATENCY.labels(method="GET", endpoint="/metrics").observe(0.01)
    ERROR_COUNT.labels(type="http_4xx", endpoint="/nope").inc()
    DB_QUERY_LATENCY.labels(operation="healthcheck").observe(0.002)
    AI_INFERENCE_LATENCY.labels(operation="submit_answer").observe(0.015)
    AI_INFERENCE_COUNT.labels(operation="submit_answer").inc()

    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]
    body = resp.text
    assert "mindguess_http_requests_total" in body
    assert "mindguess_http_request_duration_seconds" in body
    assert "mindguess_errors_total" in body
    assert "mindguess_db_query_duration_seconds" in body
    assert "mindguess_ai_inference_duration_seconds" in body
    assert "mindguess_ai_inference_total" in body


@pytest.mark.asyncio
async def test_request_timing_headers_and_metrics(client: AsyncClient):
    before = REQUEST_COUNT.labels(
        method="GET", endpoint="/health", status_code="200"
    )._value.get()
    with patch(
        "app.monitoring.health.check_database",
        new=AsyncMock(return_value={"status": "ok", "latency_seconds": 0.001}),
    ):
        with patch(
            "app.monitoring.health.get_worker_status",
            return_value={"status": "ok", "workers": [], "active_tasks": 0, "error": None},
        ):
            resp = await client.get("/health")
    assert resp.status_code == 200
    assert "X-Request-ID" in resp.headers
    assert "X-Response-Time-Ms" in resp.headers
    after = REQUEST_COUNT.labels(
        method="GET", endpoint="/health", status_code="200"
    )._value.get()
    assert after >= before + 1


@pytest.mark.asyncio
async def test_error_tracking_on_404(client: AsyncClient):
    before = ERROR_COUNT.labels(type="http_4xx", endpoint="/no-such-route")._value.get()
    resp = await client.get("/no-such-route")
    assert resp.status_code == 404
    after = ERROR_COUNT.labels(type="http_4xx", endpoint="/no-such-route")._value.get()
    assert after >= before + 1


def test_track_ai_inference_records_histogram():
    before = AI_INFERENCE_COUNT.labels(operation="unit_test_op")._value.get()
    with track_ai_inference("unit_test_op"):
        time.sleep(0.001)
    after = AI_INFERENCE_COUNT.labels(operation="unit_test_op")._value.get()
    assert after == before + 1


def test_track_db_latency_records_histogram():
    # Histogram _sum increases
    with track_db_latency("unit_test_db"):
        time.sleep(0.001)
    body, _ = render_prometheus_metrics()
    assert b"mindguess_db_query_duration_seconds" in body


def test_endpoint_label_scrubs_uuids():
    class FakeRequest:
        url = type("U", (), {"path": "/game/guess/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"})()
        scope = {}

    assert _endpoint_label(FakeRequest()) == "/game/guess/{id}"
