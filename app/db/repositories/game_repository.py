import asyncio
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    Character,
    CharacterAlias,
    CharacterAnswer,
    GameAnswer,
    GameAnswerValue,
    GameSession,
    GameSessionStatus,
    Question,
    RejectedGuess,
)
from app.engine.learn_categories import matching_character_categories


class GameRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_characters(self) -> list[Character]:
        result = await self.db.execute(
            select(Character)
            .where(Character.is_active.is_(True))
            .order_by(Character.popularity_score.desc(), Character.name)
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
        q: str | None = None,
        *,
        sort: str = "popularity",
    ) -> tuple[list[Character], int]:
        query = select(Character)
        count_query = select(func.count()).select_from(Character)

        if category is not None:
            allowed = matching_character_categories(category)
            if allowed and len(allowed) == 1:
                stored = next(iter(allowed))
                query = query.where(Character.category == stored)
                count_query = count_query.where(Character.category == stored)
            elif allowed:
                query = query.where(Character.category.in_(allowed))
                count_query = count_query.where(Character.category.in_(allowed))
        if is_active is not None:
            query = query.where(Character.is_active.is_(is_active))
            count_query = count_query.where(Character.is_active.is_(is_active))
        if q is not None and q.strip():
            like = f"%{q.strip()}%"
            query = query.where(Character.name.ilike(like))
            count_query = count_query.where(Character.name.ilike(like))

        total = (await self.db.execute(count_query)).scalar_one()
        offset = (page - 1) * page_size
        if sort == "name":
            ordered = query.order_by(Character.name)
        else:
            ordered = query.order_by(Character.popularity_score.desc(), Character.name)
        result = await self.db.execute(ordered.offset(offset).limit(page_size))
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

    async def list_all_characters(self) -> list[Character]:
        result = await self.db.execute(select(Character).order_by(Character.name))
        return list(result.scalars().all())

    async def list_all_questions(self) -> list[Question]:
        result = await self.db.execute(select(Question).order_by(Question.text))
        return list(result.scalars().all())

    async def find_characters_by_names(self, names: list[str]) -> list[Character]:
        if not names:
            return []
        lowered = {n.casefold() for n in names}
        result = await self.db.execute(select(Character))
        return [c for c in result.scalars().all() if c.name.casefold() in lowered]

    async def find_questions_by_texts(self, texts: list[str]) -> list[Question]:
        if not texts:
            return []
        lowered = {t.casefold() for t in texts}
        result = await self.db.execute(select(Question))
        return [q for q in result.scalars().all() if q.text.casefold() in lowered]

    async def find_aliases_by_values(self, aliases: list[str]) -> list[CharacterAlias]:
        if not aliases:
            return []
        lowered = {a.casefold() for a in aliases}
        result = await self.db.execute(select(CharacterAlias))
        return [row for row in result.scalars().all() if row.alias.casefold() in lowered]

    async def create_alias(self, character_id: UUID, alias: str) -> CharacterAlias:
        row = CharacterAlias(character_id=character_id, alias=alias)
        self.db.add(row)
        await self.db.flush()
        return row

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

    def _active_likelihood_stmt(self):
        return (
            select(
                CharacterAnswer.character_id,
                CharacterAnswer.question_id,
                CharacterAnswer.likelihood,
                CharacterAnswer.sample_size,
            )
            .join(Character, Character.id == CharacterAnswer.character_id)
            .join(Question, Question.id == CharacterAnswer.question_id)
            .where(Character.is_active.is_(True), Question.is_active.is_(True))
        )

    async def iter_active_likelihood_rows(self, *, batch_size: int = 5000):
        """Yield active L(C, Q) rows without a second full-table Python list.

        Uses batched ``execute()`` (client-side fetch), not ``stream()``.
        SQLAlchemy ``AsyncSession.stream()`` opens an asyncpg **server-side
        cursor**, which Neon/PgBouncer pooled connections reject.

        One giant SELECT also blocked the uvicorn event loop while Neon
        returned the full mapping, so Render's 5s health check timed out
        and recycled the instance during POST /game/start. Keyset pages
        plus ``asyncio.sleep(0)`` let GET /health/live run between batches.
        """
        size = max(1, int(batch_size))
        last_cid = None
        last_qid = None
        while True:
            stmt = (
                self._active_likelihood_stmt()
                .order_by(CharacterAnswer.character_id, CharacterAnswer.question_id)
                .limit(size)
            )
            if last_cid is not None:
                stmt = stmt.where(
                    or_(
                        CharacterAnswer.character_id > last_cid,
                        and_(
                            CharacterAnswer.character_id == last_cid,
                            CharacterAnswer.question_id > last_qid,
                        ),
                    )
                )
            result = await self.db.execute(stmt)
            rows = result.all()
            if not rows:
                return
            for character_id, question_id, likelihood, sample_size in rows:
                yield character_id, question_id, float(likelihood), int(sample_size)
            if len(rows) < size:
                return
            last_cid, last_qid = rows[-1][0], rows[-1][1]
            await asyncio.sleep(0)

    async def get_active_likelihood_rows(
        self,
    ) -> list[tuple[UUID, UUID, float, int]]:
        """All L(C,Q) for active characters × active questions (no huge IN lists)."""
        return [row async for row in self.iter_active_likelihood_rows()]

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
        # Assign id in Python so start_game can use it without a Neon flush RTT.
        session = GameSession(id=uuid4(), user_id=user_id)
        self.db.add(session)
        return session

    async def get_session_row(self, session_id: UUID) -> GameSession | None:
        """Session row only — skip selectinload(answers) for progress updates."""
        return await self.db.get(GameSession, session_id)

    async def update_session_progress(self, session_id: UUID, *, questions_asked: int) -> None:
        await self.db.execute(
            update(GameSession)
            .where(GameSession.id == session_id)
            .values(
                questions_asked_count=questions_asked,
                last_activity_at=datetime.now(timezone.utc),
            )
        )

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

    async def record_rejected_guess(self, session_id: UUID, character_id: UUID) -> None:
        existing = await self.db.execute(
            select(RejectedGuess).where(
                RejectedGuess.session_id == session_id,
                RejectedGuess.character_id == character_id,
            )
        )
        if existing.scalar_one_or_none():
            return
        self.db.add(RejectedGuess(session_id=session_id, character_id=character_id))
        await self.db.flush()

    async def get_rejected_character_ids(self, session_id: UUID) -> set[UUID]:
        result = await self.db.execute(
            select(RejectedGuess.character_id).where(RejectedGuess.session_id == session_id)
        )
        return set(result.scalars().all())

    async def increment_question_times_asked(self, question_id: UUID) -> None:
        await self.db.execute(
            update(Question)
            .where(Question.id == question_id)
            .values(times_asked=Question.times_asked + 1)
        )

    async def create_character(
        self,
        name: str,
        category: str,
        image_url: str | None = None,
        is_active: bool = True,
        popularity_score: int = 0,
    ) -> Character:
        character = Character(
            name=name,
            category=category,
            image_url=image_url,
            is_active=is_active,
            popularity_score=popularity_score,
        )
        self.db.add(character)
        await self.db.flush()
        return character

    async def create_question(
        self,
        text: str,
        category: str | None = None,
        is_active: bool = True,
        *,
        times_asked: int = 0,
        avg_information_gain: float | None = None,
    ) -> Question:
        question = Question(
            text=text,
            category=category,
            is_active=is_active,
            times_asked=times_asked,
            avg_information_gain=avg_information_gain,
        )
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

    async def bulk_upsert_character_answers(
        self,
        rows: list[tuple[UUID, UUID, float, int]],
        *,
        chunk_size: int = 2000,
    ) -> dict[str, int]:
        """Upsert many (character_id, question_id, likelihood, sample_size) rows.

        Uses SQLite ON CONFLICT for speed when syncing seed likelihoods into an
        existing database. Returns created/updated/written counts.
        """
        if not rows:
            return {"created": 0, "updated": 0, "written": 0}

        existing_result = await self.db.execute(
            select(CharacterAnswer.character_id, CharacterAnswer.question_id)
        )
        existing = {(cid, qid) for cid, qid in existing_result.all()}

        created = 0
        updated = 0
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        for start in range(0, len(rows), chunk_size):
            chunk = rows[start : start + chunk_size]
            values = []
            for character_id, question_id, likelihood, sample_size in chunk:
                if (character_id, question_id) in existing:
                    updated += 1
                else:
                    created += 1
                    existing.add((character_id, question_id))
                values.append(
                    {
                        "id": uuid4(),
                        "character_id": character_id,
                        "question_id": question_id,
                        "likelihood": likelihood,
                        "sample_size": sample_size,
                    }
                )
            stmt = sqlite_insert(CharacterAnswer).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["character_id", "question_id"],
                set_={
                    "likelihood": stmt.excluded.likelihood,
                    "sample_size": stmt.excluded.sample_size,
                },
            )
            await self.db.execute(stmt)
        await self.db.flush()
        return {"created": created, "updated": updated, "written": created + updated}

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
        # Use last activity, not start time — a long active game is not stale
        result = await self.db.execute(
            select(GameSession).where(
                GameSession.status == GameSessionStatus.IN_PROGRESS,
                func.coalesce(GameSession.last_activity_at, GameSession.started_at) < cutoff,
            )
        )
        sessions = list(result.scalars().all())
        for session in sessions:
            session.status = GameSessionStatus.ABANDONED
            session.ended_at = datetime.now(timezone.utc)
        return len(sessions)

    async def get_statistics(self) -> dict:
        finished_statuses = [
            GameSessionStatus.GUESSED_CORRECT,
            GameSessionStatus.GUESSED_INCORRECT,
        ]

        total_games = (
            await self.db.execute(
                select(func.count())
                .select_from(GameSession)
                .where(GameSession.status.in_(finished_statuses))
            )
        ).scalar_one()

        correct_games = (
            await self.db.execute(
                select(func.count())
                .select_from(GameSession)
                .where(GameSession.status == GameSessionStatus.GUESSED_CORRECT)
            )
        ).scalar_one()

        abandoned_games = (
            await self.db.execute(
                select(func.count())
                .select_from(GameSession)
                .where(GameSession.status == GameSessionStatus.ABANDONED)
            )
        ).scalar_one()

        accuracy_rate = (correct_games / total_games) if total_games > 0 else 0.0
        # Share of terminal sessions that completed into a learnable outcome
        terminal = total_games + abandoned_games
        learning_rate = (total_games / terminal) if terminal > 0 else 0.0

        avg_questions = (
            await self.db.execute(
                select(func.avg(GameSession.questions_asked_count)).where(
                    GameSession.status.in_(finished_statuses)
                )
            )
        ).scalar_one()
        average_questions_per_game = round(float(avg_questions or 0.0), 2)

        top_questions = await self.db.execute(
            select(Question.id, Question.text, Question.times_asked)
            .where(Question.is_active.is_(True))
            .order_by(Question.times_asked.desc())
            .limit(10)
        )

        guessed_total = Character.times_guessed_correctly + Character.times_guessed_incorrectly
        top_characters = await self.db.execute(
            select(
                Character.id,
                Character.name,
                Character.times_guessed_correctly,
                Character.times_guessed_incorrectly,
            )
            .where(Character.is_active.is_(True), guessed_total > 0)
            .order_by(guessed_total.desc())
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
                guessed_total > 0,
            )
        )
        weak_sorted = sorted(
            weak_rows.all(),
            key=lambda r: r.times_guessed_correctly
            / (r.times_guessed_correctly + r.times_guessed_incorrectly),
        )[:10]

        # Daily activity for the last 14 calendar days (inclusive)
        now = datetime.now(timezone.utc)
        start_day = (now - timedelta(days=13)).replace(hour=0, minute=0, second=0, microsecond=0)
        day_expr = func.date(GameSession.started_at)
        daily_rows = await self.db.execute(
            select(day_expr.label("day"), func.count().label("games"))
            .where(GameSession.started_at >= start_day)
            .group_by(day_expr)
            .order_by(day_expr)
        )
        by_day = {str(row.day): int(row.games) for row in daily_rows.all()}
        daily_activity = []
        for offset in range(14):
            day = (start_day + timedelta(days=offset)).date().isoformat()
            daily_activity.append({"date": day, "games": by_day.get(day, 0)})

        return {
            "total_games_played": total_games,
            "guess_accuracy_rate": round(accuracy_rate, 4),
            "learning_rate": round(learning_rate, 4),
            "average_questions_per_game": average_questions_per_game,
            "most_asked_questions": [
                {"id": str(row.id), "text": row.text, "times_asked": row.times_asked}
                for row in top_questions
            ],
            "most_guessed_characters": [
                {
                    "id": str(row.id),
                    "name": row.name,
                    "times_guessed": row.times_guessed_correctly + row.times_guessed_incorrectly,
                    "times_guessed_correctly": row.times_guessed_correctly,
                    "times_guessed_incorrectly": row.times_guessed_incorrectly,
                }
                for row in top_characters
            ],
            "daily_activity": daily_activity,
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
