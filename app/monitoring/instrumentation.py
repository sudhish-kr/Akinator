"""Timing helpers for DB and AI instrumentation."""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager

from app.monitoring.metrics import (
    AI_INFERENCE_COUNT,
    AI_INFERENCE_LATENCY,
    DB_QUERY_LATENCY,
)


@contextmanager
def track_db_latency(operation: str = "query") -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        DB_QUERY_LATENCY.labels(operation=operation).observe(time.perf_counter() - start)


@contextmanager
def track_ai_inference(operation: str) -> Iterator[None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        AI_INFERENCE_LATENCY.labels(operation=operation).observe(elapsed)
        AI_INFERENCE_COUNT.labels(operation=operation).inc()
