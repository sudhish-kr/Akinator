"""Integration tests — Redis-backed SessionStore (shared across instances)."""

from __future__ import annotations

import time
from uuid import uuid4

import fakeredis
import pytest

from app.cache.redis_cache import RedisCache
from app.cache.session_codec import decode_live_session, encode_live_session
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import create_initial_state
from app.services import playable_catalog as playable_catalog_mod
from app.services.live_session import LiveSession, StoredAnswer
from app.services.playable_catalog import PlayableCatalog
from app.services.session_store import SessionStore


def _live_session() -> LiveSession:
    c1, c2 = uuid4(), uuid4()
    q1, q2 = uuid4(), uuid4()
    likelihoods = {
        (c1, q1): LikelihoodEntry(0.9, 20),
        (c2, q1): LikelihoodEntry(0.1, 20),
        (c1, q2): LikelihoodEntry(0.2, 20),
        (c2, q2): LikelihoodEntry(0.8, 20),
    }
    engine = create_initial_state([c1, c2], likelihoods)
    engine.questions_asked = 1
    engine.used_question_ids.add(q1)
    return LiveSession(
        session_id=uuid4(),
        engine=engine,
        question_refs={
            q1: QuestionRef(id=q1, text="Scientist?", category="science"),
            q2: QuestionRef(id=q2, text="Athlete?", category="sports"),
        },
        character_names={c1: "Einstein", c2: "Messi"},
        character_categories={c1: "Scientists", c2: "Sports"},
        all_question_ids=[q1, q2],
        pending_question_id=q2,
        last_answered_question_id=q1,
        awaiting_guess=False,
        answers=[StoredAnswer(question_id=q1, answer="yes")],
    )


def _warm_catalog(live: LiveSession) -> None:
    """Likelihoods are process-cached, not Redis-cached."""
    playable_catalog_mod._catalog = PlayableCatalog(
        character_ids=list(live.engine.character_ids),
        question_ids=list(live.all_question_ids),
        likelihoods=dict(live.engine.likelihoods),
        question_refs=dict(live.question_refs),
        character_names=dict(live.character_names),
        character_categories=dict(live.character_categories),
        character_popularity=dict(live.character_popularity),
        character_count=len(live.engine.character_ids),
        question_count=len(live.all_question_ids),
        likelihood_count=len(live.engine.likelihoods),
    )


@pytest.fixture(autouse=True)
def _clear_catalog():
    playable_catalog_mod._catalog = None
    yield
    playable_catalog_mod._catalog = None


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def redis_cache(redis_client):
    return RedisCache(url="redis://fake", client=redis_client, key_prefix="test:")


def test_codec_roundtrip_preserves_engine_state():
    live = _live_session()
    live.character_categories = {
        next(iter(live.character_names)): "Scientists",
        list(live.character_names)[1]: "Sports",
    }
    restored = decode_live_session(encode_live_session(live))
    assert restored.session_id == live.session_id
    assert restored.pending_question_id == live.pending_question_id
    assert restored.engine.questions_asked == 1
    assert restored.answers[0].answer == "yes"
    assert set(restored.character_names.values()) == {"Einstein", "Messi"}
    assert restored.character_categories == live.character_categories
    assert len(restored.engine.likelihoods) == 4


def test_session_store_save_get_delete(redis_cache):
    store = SessionStore(cache=redis_cache, ttl_seconds=60)
    live = _live_session()
    _warm_catalog(live)
    before_probs = dict(live.engine.probabilities)
    store.save(live)

    loaded = store.get(live.session_id)
    assert loaded is not None
    assert loaded.session_id == live.session_id
    assert loaded.pending_question_id == live.pending_question_id
    assert loaded.engine.questions_asked == live.engine.questions_asked
    assert len(loaded.engine.likelihoods) == 4
    assert loaded.engine.probabilities == pytest.approx(before_probs)

    store.delete(live.session_id)
    assert store.get(live.session_id) is None


def test_compact_save_reattaches_likelihoods_from_catalog(redis_cache):
    """Per-turn saves omit likelihood blobs; catalog reattaches on get."""
    store = SessionStore(cache=redis_cache, ttl_seconds=60)
    live = _live_session()
    _warm_catalog(live)
    store.save(live)
    loaded = store.get(live.session_id)
    assert loaded is not None
    loaded.engine.questions_asked = 2
    store.save(loaded)
    again = store.get(live.session_id)
    assert again is not None
    assert len(again.engine.likelihoods) == 4
    assert again.engine.questions_asked == 2
    assert again.question_refs == live.question_refs
    assert again.character_names == live.character_names


def test_multiple_backend_instances_share_sessions(redis_client):
    """Two SessionStore instances (two API workers) see the same Redis data."""
    cache_a = RedisCache(url="redis://fake", client=redis_client, key_prefix="mg:")
    cache_b = RedisCache(url="redis://fake", client=redis_client, key_prefix="mg:")
    store_a = SessionStore(cache=cache_a, ttl_seconds=120)
    store_b = SessionStore(cache=cache_b, ttl_seconds=120)

    live = _live_session()
    _warm_catalog(live)
    store_a.save(live)

    from_b = store_b.get(live.session_id)
    assert from_b is not None
    assert from_b.character_names == live.character_names
    assert from_b.answers[0].answer == "yes"

    from_b.awaiting_guess = True
    store_b.save(from_b)

    from_a = store_a.get(live.session_id)
    assert from_a is not None
    assert from_a.awaiting_guess is True


def test_automatic_session_expiration(redis_cache):
    store = SessionStore(cache=redis_cache, ttl_seconds=1)
    live = _live_session()
    store.save(live)
    assert store.get(live.session_id) is not None
    assert redis_cache.ttl(f"session:{live.session_id}") >= 1

    time.sleep(1.1)
    assert store.get(live.session_id) is None


def test_redis_cache_purge_expired_is_noop(redis_cache):
    assert redis_cache.purge_expired() == 0


def test_session_manager_api_unchanged_with_redis_store(redis_cache):
    """GameSessionManager still works; store only persists LiveSession objects."""
    from app.services.session_manager import GameSessionManager

    mgr = GameSessionManager(min_samples=1)
    c1, c2 = uuid4(), uuid4()
    q1, q2 = uuid4(), uuid4()
    live = mgr.start(
        session_id=uuid4(),
        character_ids=[c1, c2],
        likelihoods={
            (c1, q1): LikelihoodEntry(0.95, 50),
            (c2, q1): LikelihoodEntry(0.05, 50),
            (c1, q2): LikelihoodEntry(0.9, 50),
            (c2, q2): LikelihoodEntry(0.1, 50),
        },
        question_ids=[q1, q2],
        question_refs={
            q1: QuestionRef(id=q1, text="Scientist?"),
            q2: QuestionRef(id=q2, text="Alive?"),
        },
        character_names={c1: "Einstein", c2: "Messi"},
    )
    store = SessionStore(cache=redis_cache, ttl_seconds=60)
    _warm_catalog(live)
    store.save(live)
    restored = store.get(live.session_id)
    assert restored is not None
    assert restored.pending_question_id == live.pending_question_id
    assert restored.engine.likelihoods
    turn = mgr.submit_answer(restored, restored.pending_question_id, "yes")
    assert turn.status in {"asking", "ready_to_guess"}
    store.save(restored)
    assert store.get(live.session_id) is not None
