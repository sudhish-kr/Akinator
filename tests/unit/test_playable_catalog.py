"""Unit tests for process-level playable catalog cache."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.engine.models import LikelihoodEntry, QuestionRef
from app.services import playable_catalog as mod
from app.services.playable_catalog import PlayableCatalog, invalidate_playable_catalog, peek_likelihoods


@pytest.fixture(autouse=True)
def _reset():
    mod._catalog = None
    yield
    mod._catalog = None


def test_peek_likelihoods_none_until_warmed():
    assert peek_likelihoods() is None


def test_invalidate_clears_catalog():
    cid, qid = uuid4(), uuid4()
    mod._catalog = PlayableCatalog(
        character_ids=[cid],
        question_ids=[qid],
        likelihoods={(cid, qid): LikelihoodEntry(0.9, 10)},
        question_refs={qid: QuestionRef(id=qid, text="Alive?", category="Age")},
        character_names={cid: "Test"},
        character_categories={cid: "Sports"},
        character_popularity={cid: 1},
        character_count=1,
        question_count=1,
        likelihood_count=1,
    )
    assert peek_likelihoods() is not None
    invalidate_playable_catalog()
    assert peek_likelihoods() is None
