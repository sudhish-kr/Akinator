"""Prometheus-compatible application metrics."""

from __future__ import annotations

from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Gauge,
    Histogram,
    generate_latest,
)

# Isolated registry so tests can reset cleanly if needed
REGISTRY = CollectorRegistry()

REQUEST_COUNT = Counter(
    "mindguess_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"],
    registry=REGISTRY,
)

REQUEST_LATENCY = Histogram(
    "mindguess_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
    registry=REGISTRY,
)

ERROR_COUNT = Counter(
    "mindguess_errors_total",
    "Tracked application errors",
    ["type", "endpoint"],
    registry=REGISTRY,
)

DB_QUERY_LATENCY = Histogram(
    "mindguess_db_query_duration_seconds",
    "Database query / statement latency in seconds",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
    registry=REGISTRY,
)

DB_HEALTH_LATENCY = Gauge(
    "mindguess_db_healthcheck_latency_seconds",
    "Last database health-check round-trip latency in seconds",
    registry=REGISTRY,
)

AI_INFERENCE_LATENCY = Histogram(
    "mindguess_ai_inference_duration_seconds",
    "AI engine inference latency (question selection / Bayesian update / guess)",
    ["operation"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)

AI_INFERENCE_COUNT = Counter(
    "mindguess_ai_inference_total",
    "AI engine inference invocations",
    ["operation"],
    registry=REGISTRY,
)

APP_INFO = Gauge(
    "mindguess_app_info",
    "Application info (value always 1)",
    ["app", "environment", "version"],
    registry=REGISTRY,
)


def render_prometheus_metrics() -> tuple[bytes, str]:
    """Return (body, content_type) for the Prometheus scrape endpoint."""
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
