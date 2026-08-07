"""Core training simulator — virtual games over an in-memory KB copy."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from uuid import UUID, uuid4

from app.engine.confidence import evaluate_confidence, resolve_turn
from app.engine.constants import (
    DEFAULT_CONFIDENCE_HIGH,
    DEFAULT_CONFIDENCE_MARGIN,
    DEFAULT_CONFIDENCE_SEPARATION,
    DEFAULT_LEARNING_RATE,
    DEFAULT_MAX_QUESTIONS,
)
from app.engine.learning import (
    AnswerObservation,
    KnowledgeEntry,
    learn_from_completed_game,
    learn_from_wrong_guess,
)
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import create_initial_state, process_answer, select_next_question
from app.training.metrics import GameOutcome, TrainingMetrics
from app.training.oracle import oracle_answer


@dataclass
class TrainingSnapshot:
    """Immutable-ish knowledge snapshot used as the simulation substrate."""

    character_ids: list[UUID]
    character_names: dict[UUID, str]
    character_categories: dict[UUID, str]
    question_ids: list[UUID]
    question_refs: dict[UUID, QuestionRef]
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry]

    def copy_likelihoods(self) -> dict[tuple[UUID, UUID], LikelihoodEntry]:
        return {
            key: LikelihoodEntry(likelihood=entry.likelihood, sample_size=entry.sample_size)
            for key, entry in self.likelihoods.items()
        }


@dataclass
class TrainingResult:
    n_games: int
    metrics: TrainingMetrics
    final_likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry]
    initial_accuracy_probe: float
    window_size: int
    seed: int
    learned_updates: int = 0
    notes: list[str] = field(default_factory=list)


class TrainingSimulator:
    """
    Run virtual games against a deep-copied knowledge base.

    Learning updates stay in memory. Production / DB state is never written.
    Uses the same Bayesian engine, selector, and confidence rules as gameplay.
    """

    def __init__(
        self,
        snapshot: TrainingSnapshot,
        *,
        seed: int = 42,
        oracle_noise: float = 0.08,
        learning_rate: float = DEFAULT_LEARNING_RATE,
        apply_learning: bool = True,
        max_questions: int = DEFAULT_MAX_QUESTIONS,
        min_samples: int = 0,
        confidence_high: float = DEFAULT_CONFIDENCE_HIGH,
        confidence_separation: float = DEFAULT_CONFIDENCE_SEPARATION,
        confidence_margin: float = DEFAULT_CONFIDENCE_MARGIN,
    ):
        self.snapshot = snapshot
        self.seed = seed
        self.oracle_noise = oracle_noise
        self.learning_rate = learning_rate
        self.apply_learning = apply_learning
        self.max_questions = max_questions
        self.min_samples = min_samples
        self.confidence_high = confidence_high
        self.confidence_separation = confidence_separation
        self.confidence_margin = confidence_margin
        self.rng = random.Random(seed)

    def run(self, n_games: int = 10_000, *, window_size: int = 1_000) -> TrainingResult:
        if n_games <= 0:
            raise ValueError("n_games must be positive")
        if not self.snapshot.character_ids:
            raise ValueError("Training snapshot has no characters")
        if not self.snapshot.question_ids:
            raise ValueError("Training snapshot has no questions")

        likelihoods = self.snapshot.copy_likelihoods()
        metrics = TrainingMetrics()
        learned_updates = 0
        notes = [
            "Simulation used an in-memory knowledge copy only.",
            "Production database was not modified.",
        ]
        if not self.apply_learning:
            notes.append("Learning disabled — accuracy windows reflect static KB.")

        for _ in range(n_games):
            outcome = self._play_one(likelihoods)
            metrics.record(outcome, likelihoods)
            if self.apply_learning:
                learned_updates += self._apply_learning(outcome, likelihoods)

        windows = metrics.accuracy_windows(window_size)
        initial_probe = windows[0].accuracy if windows else 0.0

        return TrainingResult(
            n_games=n_games,
            metrics=metrics,
            final_likelihoods=likelihoods,
            initial_accuracy_probe=initial_probe,
            window_size=window_size,
            seed=self.seed,
            learned_updates=learned_updates,
            notes=notes,
        )

    def _confidence_kwargs(self) -> dict:
        return {
            "confidence_high": self.confidence_high,
            "confidence_separation": self.confidence_separation,
            "confidence_margin": self.confidence_margin,
            "max_questions": self.max_questions,
        }

    def _play_one(self, likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry]) -> GameOutcome:
        true_id = self.rng.choice(self.snapshot.character_ids)
        engine = create_initial_state(list(self.snapshot.character_ids), likelihoods)
        pending = select_next_question(
            engine,
            self.snapshot.question_ids,
            min_samples=self.min_samples,
            question_refs=self.snapshot.question_refs,
            character_categories=self.snapshot.character_categories,
            rng=self.rng,
        )
        if pending is None:
            return GameOutcome(
                correct=False,
                questions_asked=0,
                true_character_id=true_id,
                guessed_character_id=None,
                confidence=0.0,
                asked_question_ids=[],
                observations=[],
            )

        observations: list[tuple[UUID, str]] = []
        asked: list[UUID] = []
        awaiting_guess = False

        while pending is not None and not awaiting_guess:
            answer = oracle_answer(
                likelihoods,
                true_id,
                pending,
                self.rng,
                noise=self.oracle_noise,
            )
            observations.append((pending, answer))
            asked.append(pending)
            engine, _ = process_answer(engine, pending, answer)

            confidence = evaluate_confidence(engine, **self._confidence_kwargs())
            next_q: UUID | None = None
            if not confidence.should_guess:
                next_q = select_next_question(
                    engine,
                    self.snapshot.question_ids,
                    min_samples=self.min_samples,
                    question_refs=self.snapshot.question_refs,
                    character_categories=self.snapshot.character_categories,
                    rng=self.rng,
                )
                confidence = resolve_turn(
                    engine,
                    next_question_id=next_q,
                    **self._confidence_kwargs(),
                )

            awaiting_guess = confidence.should_guess
            pending = None if awaiting_guess else next_q

        if engine.probabilities:
            guessed_id = max(engine.probabilities, key=engine.probabilities.get)
            confidence_score = engine.probabilities[guessed_id]
        else:
            guessed_id = None
            confidence_score = 0.0

        return GameOutcome(
            correct=guessed_id == true_id,
            questions_asked=engine.questions_asked,
            true_character_id=true_id,
            guessed_character_id=guessed_id,
            confidence=confidence_score,
            asked_question_ids=asked,
            observations=observations,
        )

    def _apply_learning(
        self,
        outcome: GameOutcome,
        likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry],
    ) -> int:
        knowledge = {
            key: KnowledgeEntry(entry.likelihood, entry.sample_size)
            for key, entry in likelihoods.items()
        }
        obs = [
            AnswerObservation(question_id=qid, answer=answer)
            for qid, answer in outcome.observations
        ]
        if outcome.correct:
            updates = learn_from_completed_game(
                outcome.true_character_id, obs, knowledge, self.learning_rate
            )
        else:
            updates = learn_from_wrong_guess(
                outcome.true_character_id, obs, knowledge, learning_rate=self.learning_rate
            )

        for upd in updates:
            likelihoods[(upd.character_id, upd.question_id)] = LikelihoodEntry(
                likelihood=upd.likelihood,
                sample_size=upd.sample_size,
            )
        return len(updates)


def run_training_simulation(
    snapshot: TrainingSnapshot,
    *,
    n_games: int = 10_000,
    window_size: int = 1_000,
    seed: int = 42,
    apply_learning: bool = True,
    oracle_noise: float = 0.08,
) -> TrainingResult:
    return TrainingSimulator(
        snapshot,
        seed=seed,
        apply_learning=apply_learning,
        oracle_noise=oracle_noise,
    ).run(n_games, window_size=window_size)


def snapshot_from_seed_dict(data: dict, *, max_characters: int | None = None) -> TrainingSnapshot:
    """
    Build a TrainingSnapshot from a knowledge seed JSON structure
    (characters, questions, likelihood_rules, likelihood_overrides).
    """
    characters = list(data.get("characters") or [])
    if max_characters is not None:
        characters = characters[:max_characters]

    char_ids: list[UUID] = []
    names: dict[UUID, str] = {}
    categories: dict[UUID, str] = {}
    name_to_id: dict[str, UUID] = {}

    for item in characters:
        cid = uuid4()
        name = item["name"].strip()
        char_ids.append(cid)
        names[cid] = name
        categories[cid] = item["category"].strip()
        name_to_id[name.casefold()] = cid

    questions = list(data.get("questions") or [])
    q_ids: list[UUID] = []
    q_refs: dict[UUID, QuestionRef] = {}
    text_to_id: dict[str, UUID] = {}
    for item in questions:
        qid = uuid4()
        text = item["text"].strip()
        q_ids.append(qid)
        q_refs[qid] = QuestionRef(id=qid, text=text, category=item.get("category"))
        text_to_id[text.casefold()] = qid

    default_sample = int(data.get("default_sample_size", 10))
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry] = {}

    rules_by_cat: dict[str, dict[str, tuple[float, int]]] = {}
    for rule in data.get("likelihood_rules") or []:
        cat = rule["category"].strip().casefold()
        q = rule["question"].strip().casefold()
        sample = int(rule.get("sample_size", default_sample))
        rules_by_cat.setdefault(cat, {})[q] = (float(rule["likelihood"]), sample)

    for item in characters:
        cid = name_to_id[item["name"].strip().casefold()]
        cat = item["category"].strip().casefold()
        for q_key, (lik, sample) in rules_by_cat.get(cat, {}).items():
            qid = text_to_id.get(q_key)
            if qid is not None:
                likelihoods[(cid, qid)] = LikelihoodEntry(likelihood=lik, sample_size=sample)

    for ov in data.get("likelihood_overrides") or []:
        cid = name_to_id.get(ov["character"].strip().casefold())
        qid = text_to_id.get(ov["question"].strip().casefold())
        if cid is None or qid is None:
            continue
        sample = int(ov.get("sample_size", default_sample))
        likelihoods[(cid, qid)] = LikelihoodEntry(
            likelihood=float(ov["likelihood"]), sample_size=sample
        )

    default_lik = float(data.get("default_likelihood", 0.5))
    for cid in char_ids:
        for qid in q_ids:
            if (cid, qid) not in likelihoods:
                likelihoods[(cid, qid)] = LikelihoodEntry(
                    likelihood=default_lik, sample_size=default_sample
                )

    return TrainingSnapshot(
        character_ids=char_ids,
        character_names=names,
        character_categories=categories,
        question_ids=q_ids,
        question_refs=q_refs,
        likelihoods=likelihoods,
    )
