"""Unit tests for Celery background workers / enqueue helpers."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from app.workers.monitoring import get_worker_status
from app.workers.queue import enqueue_analytics, enqueue_learning, enqueue_post_game


@pytest.fixture(autouse=True)
def _eager_celery(monkeypatch):
    monkeypatch.setattr("app.workers.celery_app.celery_app.conf.task_always_eager", True)
    monkeypatch.setattr("app.config.settings.celery_task_always_eager", True)


def test_enqueue_learning_returns_async_result():
    sid, cid = uuid4(), uuid4()
    with patch("app.workers.queue.process_learning") as task:
        task.delay.return_value = MagicMock(id="learn-1")
        result = enqueue_learning(sid, cid, wrong_guess=False)
        task.delay.assert_called_once()
        assert result.id == "learn-1"
        kwargs = task.delay.call_args
        assert kwargs.args[0] == str(sid)
        assert kwargs.args[1] == str(cid)


def test_enqueue_analytics_returns_async_result():
    sid = uuid4()
    with patch("app.workers.queue.process_analytics") as task:
        task.delay.return_value = MagicMock(id="analytics-1")
        result = enqueue_analytics(sid, correct=True, guessed_character_id=uuid4())
        task.delay.assert_called_once()
        assert result.id == "analytics-1"


def test_enqueue_post_game_queues_both_jobs():
    sid, cid = uuid4(), uuid4()
    with (
        patch("app.workers.queue.enqueue_learning") as learn,
        patch("app.workers.queue.enqueue_analytics") as analytics,
    ):
        learn.return_value = MagicMock(id="L")
        analytics.return_value = MagicMock(id="A")
        jobs = enqueue_post_game(sid, cid, wrong_guess=True, guessed_character_id=uuid4())
        assert jobs == {"learning_job_id": "L", "analytics_job_id": "A"}
        learn.assert_called_once()
        analytics.assert_called_once()
        assert analytics.call_args.kwargs["update_question_ig"] is True


def test_enqueue_uses_inline_apply_when_broker_unreachable(monkeypatch):
    """Missing Redis must not hang HTTP confirm/learn — fall back to apply()."""
    monkeypatch.setattr("app.config.settings.celery_task_always_eager", False)
    monkeypatch.setattr("app.workers.queue._broker_reachable", lambda timeout=0.4: False)

    sid, cid = uuid4(), uuid4()
    with patch("app.workers.queue.process_learning") as task:
        task.apply.return_value = MagicMock(id="inline-learn")
        result = enqueue_learning(sid, cid, wrong_guess=False)
        task.delay.assert_not_called()
        task.apply.assert_called_once()
        assert result.id == "inline-learn"


def test_enqueue_post_game_correct_path_survives_broker_outage(monkeypatch):
    monkeypatch.setattr("app.config.settings.celery_task_always_eager", False)
    monkeypatch.setattr("app.workers.queue._broker_reachable", lambda timeout=0.4: False)

    sid, cid = uuid4(), uuid4()
    with (
        patch("app.workers.queue.process_learning") as learn_task,
        patch("app.workers.queue.process_analytics") as analytics_task,
    ):
        learn_task.apply.return_value = MagicMock(id="L")
        analytics_task.apply.return_value = MagicMock(id="A")
        jobs = enqueue_post_game(sid, cid, wrong_guess=False, guessed_character_id=cid)
        assert jobs == {"learning_job_id": "L", "analytics_job_id": "A"}
        learn_task.delay.assert_not_called()
        analytics_task.delay.assert_not_called()
        assert analytics_task.apply.call_args.kwargs["kwargs"]["update_question_ig"] is False


def test_process_learning_task_retries_configured():
    from app.workers.tasks import process_learning

    assert process_learning.max_retries == 5
    assert Exception in (process_learning.autoretry_for or ())


def test_process_analytics_task_retries_configured():
    from app.workers.tasks import process_analytics

    assert process_analytics.max_retries == 5


def test_worker_monitoring_eager_mode():
    status = get_worker_status()
    assert status["status"] == "ok"
    assert status["eager"] is True
    assert "eager-in-process" in status["workers"]


def test_worker_monitoring_reports_unavailable_on_inspect_error(monkeypatch):
    monkeypatch.setattr("app.config.settings.celery_task_always_eager", False)

    class Boom:
        def ping(self):
            raise RuntimeError("broker down")

        def active(self):
            return {}

        def reserved(self):
            return {}

        def scheduled(self):
            return {}

        def stats(self):
            return {}

    monkeypatch.setattr(
        "app.workers.monitoring.celery_app.control.inspect",
        lambda timeout=1.0: Boom(),
    )
    status = get_worker_status()
    assert status["status"] == "unavailable"
    assert "broker down" in (status["error"] or "")
