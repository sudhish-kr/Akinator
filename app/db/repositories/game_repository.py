from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Character,
    CharacterAnswer,
    GameAnswer,
    GameAnswerValue,
    GameSession,
    GameSessionStatus,
    Question,
)


class GameRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_characters(self) -> list[Character]:
        result = await self.db.execute(
            select(Character).where(Character.is_active.is_(True)).order_by(Character.name)
        )
        return list(result.scalars().all())

    async def get_active_questions(self) -> list[Question]:
        result = await self.db.execute(
            select(Question).where(Question.is_active.is_(True)).order_by(Question.text)
        )
        return list(result.scalars().all())

    async def list_characters(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Character], int]:
        query = select(Character)
        count_query = select(func.count()).select_from(Character)

        if category is not None:
            query = query.where(Character.category == category)
            count_query = count_query.where(Character.category == category)
        if is_active is not None:
            query = query.where(Character.is_active.is_(is_active))
            count_query = count_query.where(Character.is_active.is_(is_active))

        total = (await self.db.execute(count_query)).scalar_one()
        offset = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(Character.name).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def list_questions(
        self,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        is_active: bool | None = None,
    ) -> tuple[list[Question], int]:
        query = select(Question)
        count_query = select(func.count()).select_from(Question)

        if category is not None:
            query = query.where(Question.category == category)
            count_query = count_query.where(Question.category == category)
        if is_active is not None:
            query = query.where(Question.is_active.is_(is_active))
            count_query = count_query.where(Question.is_active.is_(is_active))

        total = (await self.db.execute(count_query)).scalar_one()
        offset = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(Question.text).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_likelihoods(
        self,
        character_ids: list[UUID],
        question_ids: list[UUID],
    ) -> list[CharacterAnswer]:
        if not character_ids or not question_ids:
            return []
        result = await self.db.execute(
            select(CharacterAnswer).where(
                CharacterAnswer.character_id.in_(character_ids),
                CharacterAnswer.question_id.in_(question_ids),
            )
        )
        return list(result.scalars().all())

    async def get_character_answer(
        self,
        character_id: UUID,
        question_id: UUID,
    ) -> CharacterAnswer | None:
        result = await self.db.execute(
            select(CharacterAnswer).where(
                CharacterAnswer.character_id == character_id,
                CharacterAnswer.question_id == question_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_character(self, character_id: UUID) -> Character | None:
        return await self.db.get(Character, character_id)

    async def get_question(self, question_id: UUID) -> Question | None:
        return await self.db.get(Question, question_id)

    async def create_session(self, user_id: UUID | None = None) -> GameSession:
        session = GameSession(user_id=user_id)
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session(self, session_id: UUID) -> GameSession | None:
        result = await self.db.execute(
            select(GameSession)
            .options(selectinload(GameSession.answers))
            .where(GameSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_session_answers(self, session_id: UUID) -> list[GameAnswer]:
        result = await self.db.execute(
            select(GameAnswer)
            .where(GameAnswer.session_id == session_id)
            .order_by(GameAnswer.order_index)
        )
        return list(result.scalars().all())

    async def save_answer(
        self,
        session_id: UUID,
        question_id: UUID,
        answer: str,
        order_index: int,
        entropy_before: float | None,
    ) -> GameAnswer:
        record = GameAnswer(
            session_id=session_id,
            question_id=question_id,
            answer=GameAnswerValue(answer),
            order_index=order_index,
            entropy_before=entropy_before,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def increment_question_times_asked(self, question_id: UUID) -> None:
        question = await self.db.get(Question, question_id)
        if question:
            question.times_asked += 1

    async def create_character(
        self,
        name: str,
        category: str,
        image_url: str | None = None,
        is_active: bool = True,
    ) -> Character:
        character = Character(
            name=name, category=category, image_url=image_url, is_active=is_active
        )
        self.db.add(character)
        await self.db.flush()
        return character

    async def create_question(
        self,
        text: str,
        category: str | None = None,
        is_active: bool = True,
    ) -> Question:
        question = Question(text=text, category=category, is_active=is_active)
        self.db.add(question)
        await self.db.flush()
        return question

    async def upsert_character_answer(
        self,
        character_id: UUID,
        question_id: UUID,
        likelihood: float,
        sample_size: int,
    ) -> CharacterAnswer:
        existing = await self.get_character_answer(character_id, question_id)
        if existing:
            existing.likelihood = likelihood
            existing.sample_size = sample_size
            return existing

        record = CharacterAnswer(
            character_id=character_id,
            question_id=question_id,
            likelihood=likelihood,
            sample_size=sample_size,
        )
        self.db.add(record)
        await self.db.flush()
        return record

    async def update_question_avg_ig(self, question_id: UUID, actual_gain: float) -> None:
        question = await self.db.get(Question, question_id)
        if not question:
            return
        if question.avg_information_gain is None:
            question.avg_information_gain = actual_gain
        else:
            # Rolling average weighted by times_asked
            n = max(question.times_asked, 1)
            question.avg_information_gain = (
                question.avg_information_gain * (n - 1) + actual_gain
            ) / n

    async def abandon_stale_sessions(self, minutes: int) -> int:
        from datetime import datetime, timedelta, timezone

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        result = await self.db.execute(
            select(GameSession).where(
                GameSession.status == GameSessionStatus.IN_PROGRESS,
                GameSession.started_at < cutoff,
            )
        )
        sessions = list(result.scalars().all())
        for session in sessions:
            session.status = GameSessionStatus.ABANDONED
            session.ended_at = datetime.now(timezone.utc)
        return len(sessions)

    async def get_statistics(self) -> dict:
        total_games = (
            await self.db.execute(
                select(func.count()).select_from(GameSession).where(
                    GameSession.status.in_([
                        GameSessionStatus.GUESSED_CORRECT,
                        GameSessionStatus.GUESSED_INCORRECT,
                    ])
                )
            )
        ).scalar_one()

        correct_games = (
            await self.db.execute(
                select(func.count())
                .select_from(GameSession)
                .where(GameSession.status == GameSessionStatus.GUESSED_CORRECT)
            )
        ).scalar_one()

        accuracy_rate = (correct_games / total_games) if total_games > 0 else 0.0

        top_questions = await self.db.execute(
            select(Question.id, Question.text, Question.times_asked)
            .where(Question.is_active.is_(True))
            .order_by(Question.times_asked.desc())
            .limit(10)
        )

        weak_rows = await self.db.execute(
            select(
                Character.id,
                Character.name,
                Character.times_guessed_correctly,
                Character.times_guessed_incorrectly,
            ).where(
                Character.is_active.is_(True),
                Character.times_guessed_correctly + Character.times_guessed_incorrectly > 0,
            )
        )
        weak_sorted = sorted(
            weak_rows.all(),
            key=lambda r: r.times_guessed_correctly
            / (r.times_guessed_correctly + r.times_guessed_incorrectly),
        )[:10]

        return {
            "total_games_played": total_games,
            "guess_accuracy_rate": round(accuracy_rate, 4),
            "most_asked_questions": [
                {"id": str(row.id), "text": row.text, "times_asked": row.times_asked}
                for row in top_questions
            ],
            "lowest_accuracy_characters": [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "times_guessed_correctly": row.times_guessed_correctly,
                    "times_guessed_incorrectly": row.times_guessed_incorrectly,
                    "accuracy": round(
                        row.times_guessed_correctly
                        / (row.times_guessed_correctly + row.times_guessed_incorrectly),
                        4,
                    ),
                }
                for row in weak_sorted
            ],
        }

    async def commit(self) -> None:
        await self.db.commit()

    async def rollback(self) -> None:
        await self.db.rollback()
