"""Shared pytest fixtures."""

from __future__ import annotations

import os

# Must run before app.config.Settings is imported by test modules.
os.environ.setdefault("JWT_SECRET", "test-secret-for-pytest-only")
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
os.environ.setdefault("SESSION_CACHE_BACKEND", "memory")

import pytest


@pytest.fixture(autouse=True)
def _celery_eager_mode(monkeypatch):
    """Run Celery tasks in-process during tests (no Redis broker required)."""
    monkeypatch.setattr("app.config.settings.celery_task_always_eager", True)
    try:
        from app.workers.celery_app import celery_app

        monkeypatch.setattr(celery_app.conf, "task_always_eager", True)
        monkeypatch.setattr(celery_app.conf, "task_eager_propagates", True)
    except Exception:
        pass
