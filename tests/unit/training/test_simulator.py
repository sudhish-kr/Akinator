"""Unit tests for the AI training simulator."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.engine.constants import Answer
from app.engine.models import LikelihoodEntry, QuestionRef
from app.training.oracle import closest_answer, oracle_answer
from app.training.report import export_training_report, training_report_to_dict
from app.training.simulator import (
    TrainingSimulator,
    TrainingSnapshot,
    snapshot_from_seed_dict,
)

ROOT = Path(__file__).resolve().parents[3]


def _tiny_snapshot() -> TrainingSnapshot:
    """4 characters × 3 questions with separable likelihoods."""
    e, m, x, r = uuid4(), uuid4(), uuid4(), uuid4()
    q1, q2, q3 = uuid4(), uuid4(), uuid4()
    names = {
        e: "Einstein",
        m: "Messi",
        x: "Musk",
        r: "Ronaldo",
    }
    refs = {
        q1: QuestionRef(id=q1, text="Is this a scientist?", category="science"),
        q2: QuestionRef(id=q2, text="Is this an athlete?", category="sports"),
        q3: QuestionRef(id=q3, text="Is this alive today?", category="bio"),
    }
    # Distinctive L matrix
    L = {
        (e, q1): LikelihoodEntry(0.95, 100),
        (m, q1): LikelihoodEntry(0.05, 100),
        (x, q1): LikelihoodEntry(0.55, 100),
        (r, q1): LikelihoodEntry(0.05, 100),
        (e, q2): LikelihoodEntry(0.05, 100),
        (m, q2): LikelihoodEntry(0.95, 100),
        (x, q2): LikelihoodEntry(0.15, 100),
        (r, q2): LikelihoodEntry(0.95, 100),
        (e, q3): LikelihoodEntry(0.0, 100),
        (m, q3): LikelihoodEntry(0.95, 100),
        (x, q3): LikelihoodEntry(0.95, 100),
        (r, q3): LikelihoodEntry(0.95, 100),
    }
    return TrainingSnapshot(
        character_ids=[e, m, x, r],
        character_names=names,
        character_categories={
            e: "Scientists",
            m: "Sports",
            x: "Business",
            r: "Sports",
        },
        question_ids=[q1, q2, q3],
        question_refs=refs,
        likelihoods=L,
    )


class TestOracle:
    def test_closest_answer_extremes(self):
        assert closest_answer(1.0) == Answer.YES
        assert closest_answer(0.0) == Answer.NO
        assert closest_answer(0.5) == Answer.DONT_KNOW

    def test_oracle_answer_is_valid(self):
        snap = _tiny_snapshot()
        cid = snap.character_ids[0]
        qid = snap.question_ids[0]
        import random

        rng = random.Random(0)
        for _ in range(20):
            ans = oracle_answer(snap.likelihoods, cid, qid, rng, noise=0.05)
            assert ans in {a.value for a in Answer}


class TestTrainingSimulator:
    def test_runs_requested_game_count(self):
        snap = _tiny_snapshot()
        result = TrainingSimulator(snap, seed=1).run(50, window_size=10)
        assert result.n_games == 50
        assert len(result.metrics.outcomes) == 50
        assert result.metrics.overall_accuracy() >= 0.0

    def test_does_not_mutate_original_snapshot_likelihoods(self):
        snap = _tiny_snapshot()
        before = {
            k: (v.likelihood, v.sample_size) for k, v in snap.likelihoods.items()
        }
        TrainingSimulator(snap, seed=2, apply_learning=True).run(30, window_size=10)
        after = {
            k: (v.likelihood, v.sample_size) for k, v in snap.likelihoods.items()
        }
        assert before == after

    def test_learning_changes_working_copy(self):
        snap = _tiny_snapshot()
        result = TrainingSimulator(snap, seed=3, apply_learning=True).run(
            40, window_size=10
        )
        assert result.learned_updates > 0
        # At least one entry should differ from the original snapshot
        changed = False
        for key, entry in result.final_likelihoods.items():
            orig = snap.likelihoods[key]
            if (
                abs(entry.likelihood - orig.likelihood) > 1e-9
                or entry.sample_size != orig.sample_size
            ):
                changed = True
                break
        assert changed

    def test_accuracy_windows_and_improvement_shape(self):
        snap = _tiny_snapshot()
        result = TrainingSimulator(snap, seed=4).run(40, window_size=10)
        windows = result.metrics.accuracy_windows(10)
        assert len(windows) == 4
        improvement = result.metrics.accuracy_improvement(10)
        assert "delta" in improvement
        assert "first_window_accuracy" in improvement
        assert "last_window_accuracy" in improvement

    def test_identifies_weak_questions_and_mappings(self):
        snap = _tiny_snapshot()
        result = TrainingSimulator(snap, seed=5, oracle_noise=0.2).run(
            80, window_size=20
        )
        qnames = {qid: ref.text for qid, ref in snap.question_refs.items()}
        weak_q = result.metrics.weak_questions(qnames, min_asks=1, limit=5)
        assert weak_q
        weak_m = result.metrics.weak_mappings(
            result.final_likelihoods,
            snap.character_names,
            qnames,
            min_samples=1,
            limit=5,
        )
        assert weak_m

    def test_export_report_marks_production_unmodified(self, tmp_path: Path):
        snap = _tiny_snapshot()
        result = TrainingSimulator(snap, seed=6).run(20, window_size=10)
        path = export_training_report(result, snap, tmp_path / "report.json")
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["production_data_modified"] is False
        assert payload["summary"]["overall_accuracy"] >= 0.0
        assert "weak_questions" in payload
        assert "weak_probability_mappings" in payload
        assert "accuracy_by_window" in payload
        # training_report_to_dict consistency
        assert training_report_to_dict(result, snap)["n_games"] == 20


class TestSnapshotFromSeed:
    def test_builds_from_mini_seed(self):
        data = {
            "characters": [
                {"name": "Ada", "category": "Scientists", "aliases": []},
                {"name": "Messi", "category": "Sports", "aliases": []},
            ],
            "questions": [
                {"text": "Is this a scientist or inventor?", "category": "domain"},
                {"text": "Is this an athlete or sports figure?", "category": "domain"},
            ],
            "likelihood_rules": [
                {
                    "category": "Scientists",
                    "question": "Is this a scientist or inventor?",
                    "likelihood": 0.95,
                    "sample_size": 40,
                },
                {
                    "category": "Sports",
                    "question": "Is this an athlete or sports figure?",
                    "likelihood": 0.97,
                    "sample_size": 40,
                },
            ],
            "likelihood_overrides": [],
            "default_likelihood": 0.5,
            "default_sample_size": 10,
        }
        snap = snapshot_from_seed_dict(data)
        assert len(snap.character_ids) == 2
        assert len(snap.question_ids) == 2
        # Full matrix filled
        assert len(snap.likelihoods) == 4

    def test_seed_v1_loads_when_present(self):
        path = ROOT / "data" / "knowledge" / "seed_v1.json"
        if not path.exists():
            pytest.skip("seed_v1.json not present")
        data = json.loads(path.read_text(encoding="utf-8"))
        snap = snapshot_from_seed_dict(data, max_characters=20)
        assert len(snap.character_ids) == 20
        assert len(snap.question_ids) >= 1
