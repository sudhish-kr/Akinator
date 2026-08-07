"""Training metrics: accuracy windows, weak questions, weak mappings."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from uuid import UUID

from app.engine.constants import ANSWER_WEIGHTS
from app.engine.models import LikelihoodEntry


@dataclass
class GameOutcome:
    correct: bool
    questions_asked: int
    true_character_id: UUID
    guessed_character_id: UUID | None
    confidence: float
    asked_question_ids: list[UUID]
    # (question_id, answer_value) observed for the true character
    observations: list[tuple[UUID, str]]


@dataclass
class WindowAccuracy:
    window_index: int
    start_game: int
    end_game: int
    games: int
    correct: int
    accuracy: float
    avg_questions: float


@dataclass
class WeakQuestion:
    question_id: UUID
    text: str
    times_asked: int
    times_in_wrong_games: int
    wrong_rate: float
    avg_abs_likelihood_error: float


@dataclass
class WeakMapping:
    character_id: UUID
    character_name: str
    question_id: UUID
    question_text: str
    stored_likelihood: float
    observed_mean_weight: float
    abs_error: float
    samples: int


@dataclass
class TrainingMetrics:
    outcomes: list[GameOutcome] = field(default_factory=list)
    # question_id -> list of |L - answer_weight| when asked for true char
    question_errors: dict[UUID, list[float]] = field(default_factory=lambda: defaultdict(list))
    question_asked: dict[UUID, int] = field(default_factory=lambda: defaultdict(int))
    question_wrong: dict[UUID, int] = field(default_factory=lambda: defaultdict(int))
    # (cid, qid) -> list of observed answer weights
    mapping_obs: dict[tuple[UUID, UUID], list[float]] = field(
        default_factory=lambda: defaultdict(list)
    )

    def record(self, outcome: GameOutcome, likelihoods: dict[tuple, LikelihoodEntry]) -> None:
        self.outcomes.append(outcome)
        for qid in outcome.asked_question_ids:
            self.question_asked[qid] += 1
            if not outcome.correct:
                self.question_wrong[qid] += 1
        for qid, answer in outcome.observations:
            weight = ANSWER_WEIGHTS[answer]
            entry = likelihoods.get((outcome.true_character_id, qid))
            stored = entry.likelihood if entry else 0.5
            err = abs(stored - weight)
            self.question_errors[qid].append(err)
            self.mapping_obs[(outcome.true_character_id, qid)].append(weight)

    def overall_accuracy(self) -> float:
        if not self.outcomes:
            return 0.0
        return sum(1 for o in self.outcomes if o.correct) / len(self.outcomes)

    def avg_questions(self) -> float:
        if not self.outcomes:
            return 0.0
        return sum(o.questions_asked for o in self.outcomes) / len(self.outcomes)

    def accuracy_windows(self, window_size: int) -> list[WindowAccuracy]:
        if window_size <= 0:
            raise ValueError("window_size must be positive")
        windows: list[WindowAccuracy] = []
        n = len(self.outcomes)
        for i, start in enumerate(range(0, n, window_size)):
            chunk = self.outcomes[start : start + window_size]
            correct = sum(1 for o in chunk if o.correct)
            games = len(chunk)
            windows.append(
                WindowAccuracy(
                    window_index=i,
                    start_game=start + 1,
                    end_game=start + games,
                    games=games,
                    correct=correct,
                    accuracy=correct / games if games else 0.0,
                    avg_questions=(
                        sum(o.questions_asked for o in chunk) / games if games else 0.0
                    ),
                )
            )
        return windows

    def accuracy_improvement(self, window_size: int) -> dict:
        windows = self.accuracy_windows(window_size)
        if len(windows) < 2:
            first = windows[0].accuracy if windows else 0.0
            return {
                "first_window_accuracy": first,
                "last_window_accuracy": first,
                "delta": 0.0,
                "improved": False,
            }
        first_a = windows[0].accuracy
        last_a = windows[-1].accuracy
        return {
            "first_window_accuracy": round(first_a, 4),
            "last_window_accuracy": round(last_a, 4),
            "delta": round(last_a - first_a, 4),
            "improved": last_a > first_a,
        }

    def weak_questions(
        self,
        question_names: dict[UUID, str],
        *,
        min_asks: int = 5,
        limit: int = 20,
    ) -> list[WeakQuestion]:
        rows: list[WeakQuestion] = []
        for qid, asked in self.question_asked.items():
            if asked < min_asks:
                continue
            wrong = self.question_wrong.get(qid, 0)
            errs = self.question_errors.get(qid, [])
            rows.append(
                WeakQuestion(
                    question_id=qid,
                    text=question_names.get(qid, str(qid)),
                    times_asked=asked,
                    times_in_wrong_games=wrong,
                    wrong_rate=wrong / asked,
                    avg_abs_likelihood_error=(sum(errs) / len(errs) if errs else 0.0),
                )
            )
        rows.sort(key=lambda r: (r.wrong_rate, r.avg_abs_likelihood_error), reverse=True)
        return rows[:limit]

    def weak_mappings(
        self,
        likelihoods: dict[tuple, LikelihoodEntry],
        character_names: dict[UUID, str],
        question_names: dict[UUID, str],
        *,
        min_samples: int = 3,
        limit: int = 30,
    ) -> list[WeakMapping]:
        rows: list[WeakMapping] = []
        for (cid, qid), weights in self.mapping_obs.items():
            if len(weights) < min_samples:
                continue
            mean_w = sum(weights) / len(weights)
            entry = likelihoods.get((cid, qid))
            stored = entry.likelihood if entry else 0.5
            rows.append(
                WeakMapping(
                    character_id=cid,
                    character_name=character_names.get(cid, str(cid)),
                    question_id=qid,
                    question_text=question_names.get(qid, str(qid)),
                    stored_likelihood=stored,
                    observed_mean_weight=mean_w,
                    abs_error=abs(stored - mean_w),
                    samples=len(weights),
                )
            )
        rows.sort(key=lambda r: r.abs_error, reverse=True)
        return rows[:limit]
