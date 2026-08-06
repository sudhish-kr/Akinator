"""Post-game self-learning — TDD v1.1 Section 4."""

from uuid import UUID

from app.config import settings
from app.db.repositories.game_repository import GameRepository
from app.engine.learning import (
    AnswerObservation,
    KnowledgeEntry,
    learn_from_completed_game,
    learn_from_wrong_guess,
)


class LearningService:
    def __init__(self, repo: GameRepository):
        self.repo = repo

    async def _load_knowledge(
        self,
        character_id: UUID,
        question_ids: list[UUID],
    ) -> dict[tuple[UUID, UUID], KnowledgeEntry]:
        knowledge: dict[tuple[UUID, UUID], KnowledgeEntry] = {}
        for qid in question_ids:
            existing = await self.repo.get_character_answer(character_id, qid)
            if existing:
                knowledge[(character_id, qid)] = KnowledgeEntry(
                    likelihood=existing.likelihood,
                    sample_size=existing.sample_size,
                )
        return knowledge

    async def _apply_updates(self, updates) -> int:
        for update in updates:
            await self.repo.upsert_character_answer(
                character_id=update.character_id,
                question_id=update.question_id,
                likelihood=update.likelihood,
                sample_size=update.sample_size,
            )
        return len(updates)

    async def learn_from_session(self, session_id: UUID, character_id: UUID) -> int:
        """
        Replay GameAnswers and nudge L(C, Q) toward user answers (Section 4.1).
        Returns number of likelihood pairs updated.
        """
        answers = await self.repo.get_session_answers(session_id)
        if not answers:
            return 0

        observations = [
            AnswerObservation(question_id=a.question_id, answer=a.answer.value)
            for a in answers
        ]
        question_ids = [o.question_id for o in observations]
        knowledge = await self._load_knowledge(character_id, question_ids)

        updates = learn_from_completed_game(
            character_id,
            observations,
            knowledge,
            learning_rate=settings.learning_rate,
        )
        count = await self._apply_updates(updates)

        # Track actual information gain (Section 4.3)
        for i, game_answer in enumerate(answers):
            if game_answer.entropy_before is not None and i + 1 < len(answers):
                next_entropy = answers[i + 1].entropy_before
                if next_entropy is not None:
                    actual_gain = game_answer.entropy_before - next_entropy
                    await self.repo.update_question_avg_ig(game_answer.question_id, actual_gain)

        return count

    async def learn_from_wrong_guess(
        self,
        session_id: UUID,
        correct_character_id: UUID,
        distinguishing_question_id: UUID | None = None,
        distinguishing_answer: str | None = None,
    ) -> int:
        """
        AI guessed wrong: store the correct character and distinguishing Q/A,
        and learn from the session answers (no duplicate knowledge rows).
        """
        answers = await self.repo.get_session_answers(session_id)
        observations = [
            AnswerObservation(question_id=a.question_id, answer=a.answer.value)
            for a in answers
        ]

        question_ids = list({o.question_id for o in observations})
        if distinguishing_question_id is not None:
            question_ids.append(distinguishing_question_id)

        knowledge = await self._load_knowledge(correct_character_id, question_ids)
        updates = learn_from_wrong_guess(
            correct_character_id,
            observations,
            knowledge,
            distinguishing_question_id=distinguishing_question_id,
            distinguishing_answer=distinguishing_answer,
            learning_rate=settings.learning_rate,
        )
        return await self._apply_updates(updates)
