"""Post-game self-learning — TDD v1.1 Section 4."""

from uuid import UUID

from app.config import settings
from app.db.repositories.game_repository import GameRepository
from app.engine.bayesian import apply_learning_update
from app.engine.constants import ANSWER_WEIGHTS


class LearningService:
    def __init__(self, repo: GameRepository):
        self.repo = repo

    async def learn_from_session(self, session_id: UUID, character_id: UUID) -> int:
        """
        Replay GameAnswers and nudge L(C, Q) toward user answers (Section 4.1).
        Returns number of likelihood pairs updated.
        """
        answers = await self.repo.get_session_answers(session_id)
        if not answers:
            return 0

        learning_rate = settings.learning_rate
        updated = 0

        for i, game_answer in enumerate(answers):
            answer_weight = ANSWER_WEIGHTS[game_answer.answer.value]
            existing = await self.repo.get_character_answer(
                character_id, game_answer.question_id
            )

            old_likelihood = existing.likelihood if existing else 0.5
            old_sample = existing.sample_size if existing else 0

            new_likelihood = apply_learning_update(old_likelihood, answer_weight, learning_rate)
            await self.repo.upsert_character_answer(
                character_id=character_id,
                question_id=game_answer.question_id,
                likelihood=new_likelihood,
                sample_size=old_sample + 1,
            )
            updated += 1

            # Track actual information gain (Section 4.3)
            if game_answer.entropy_before is not None and i + 1 < len(answers):
                next_entropy = answers[i + 1].entropy_before
                if next_entropy is not None:
                    actual_gain = game_answer.entropy_before - next_entropy
                    await self.repo.update_question_avg_ig(game_answer.question_id, actual_gain)

        return updated
