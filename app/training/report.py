"""Export training simulation reports (JSON). Never writes to the game database."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.training.simulator import TrainingResult, TrainingSnapshot


def training_report_to_dict(
    result: TrainingResult,
    snapshot: TrainingSnapshot,
) -> dict[str, Any]:
    metrics = result.metrics
    question_names = {qid: ref.text for qid, ref in snapshot.question_refs.items()}
    weak_qs = metrics.weak_questions(question_names)
    # Evaluate weak mappings against the *final* learned table
    weak_maps = metrics.weak_mappings(
        result.final_likelihoods,
        snapshot.character_names,
        question_names,
    )
    windows = metrics.accuracy_windows(result.window_size)
    improvement = metrics.accuracy_improvement(result.window_size)

    return {
        "version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_games": result.n_games,
        "seed": result.seed,
        "window_size": result.window_size,
        "production_data_modified": False,
        "notes": result.notes,
        "summary": {
            "overall_accuracy": round(metrics.overall_accuracy(), 4),
            "avg_questions_per_game": round(metrics.avg_questions(), 4),
            "learned_updates": result.learned_updates,
            "accuracy_improvement": improvement,
        },
        "accuracy_by_window": [
            {
                "window_index": w.window_index,
                "start_game": w.start_game,
                "end_game": w.end_game,
                "games": w.games,
                "correct": w.correct,
                "accuracy": round(w.accuracy, 4),
                "avg_questions": round(w.avg_questions, 4),
            }
            for w in windows
        ],
        "weak_questions": [
            {
                "question_id": str(q.question_id),
                "text": q.text,
                "times_asked": q.times_asked,
                "times_in_wrong_games": q.times_in_wrong_games,
                "wrong_rate": round(q.wrong_rate, 4),
                "avg_abs_likelihood_error": round(q.avg_abs_likelihood_error, 4),
            }
            for q in weak_qs
        ],
        "weak_probability_mappings": [
            {
                "character_id": str(m.character_id),
                "character_name": m.character_name,
                "question_id": str(m.question_id),
                "question_text": m.question_text,
                "stored_likelihood": round(m.stored_likelihood, 4),
                "observed_mean_weight": round(m.observed_mean_weight, 4),
                "abs_error": round(m.abs_error, 4),
                "samples": m.samples,
            }
            for m in weak_maps
        ],
        "knowledge_size": {
            "characters": len(snapshot.character_ids),
            "questions": len(snapshot.question_ids),
            "likelihood_entries": len(snapshot.likelihoods),
        },
    }


def export_training_report(
    result: TrainingResult,
    snapshot: TrainingSnapshot,
    path: Path | str,
) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = training_report_to_dict(result, snapshot)
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return out
