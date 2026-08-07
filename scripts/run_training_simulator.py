"""
Run the AI training simulator (virtual games; no production DB writes).

Usage:
    python scripts/run_training_simulator.py
    python scripts/run_training_simulator.py --games 10000 --seed 42
    python scripts/run_training_simulator.py --from-seed data/knowledge/seed_v1.json
    python scripts/run_training_simulator.py --max-characters 80 --games 2000

By default loads the curated seed JSON into memory. Learning updates stay
in-process and are never written back to the database.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.training.report import export_training_report
from app.training.simulator import (
    TrainingSimulator,
    snapshot_from_seed_dict,
)

DEFAULT_SEED = ROOT / "data" / "knowledge" / "seed_v1.json"
DEFAULT_REPORT = ROOT / "reports" / "training_report.json"


def main() -> None:
    parser = argparse.ArgumentParser(description="MindGuess AI training simulator")
    parser.add_argument("--games", type=int, default=10_000, help="Virtual games to simulate")
    parser.add_argument("--window-size", type=int, default=1_000, help="Accuracy window size")
    parser.add_argument("--seed", type=int, default=42, help="RNG seed")
    parser.add_argument(
        "--from-seed",
        type=Path,
        default=DEFAULT_SEED,
        help="Knowledge seed JSON path (loaded into memory only)",
    )
    parser.add_argument(
        "--max-characters",
        type=int,
        default=None,
        help="Optional cap on characters for faster runs",
    )
    parser.add_argument(
        "--no-learning",
        action="store_true",
        help="Disable in-memory learning (baseline accuracy only)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        default=DEFAULT_REPORT,
        help=f"Output report path (default: {DEFAULT_REPORT})",
    )
    parser.add_argument("--oracle-noise", type=float, default=0.08)
    args = parser.parse_args()

    if not args.from_seed.exists():
        print(f"Seed file not found: {args.from_seed}", file=sys.stderr)
        sys.exit(1)

    data = json.loads(args.from_seed.read_text(encoding="utf-8"))
    snapshot = snapshot_from_seed_dict(data, max_characters=args.max_characters)
    print(
        f"Loaded in-memory KB: {len(snapshot.character_ids)} characters, "
        f"{len(snapshot.question_ids)} questions, "
        f"{len(snapshot.likelihoods)} likelihoods."
    )
    print(
        f"Simulating {args.games} games (learning={'off' if args.no_learning else 'in-memory only'})..."
    )

    result = TrainingSimulator(
        snapshot,
        seed=args.seed,
        apply_learning=not args.no_learning,
        oracle_noise=args.oracle_noise,
    ).run(args.games, window_size=args.window_size)

    path = export_training_report(result, snapshot, args.report)
    summary = result.metrics.accuracy_improvement(args.window_size)
    print(
        f"Overall accuracy: {result.metrics.overall_accuracy():.2%} | "
        f"avg questions: {result.metrics.avg_questions():.2f} | "
        f"improvement delta: {summary['delta']:+.2%}"
    )
    print(f"Report written to {path} (production data unmodified).")


if __name__ == "__main__":
    main()
