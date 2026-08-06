from datetime import datetime, timezone
from uuid import UUID

from app.config import settings
from app.db.models import GameSessionStatus
from app.db.repositories.game_repository import GameRepository
from app.engine.constants import Answer
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    decide_after_answer,
    process_answer,
    select_next_question,
)
from app.services.learning_service import LearningService
from app.services.session_store import LiveSession, SessionStore, session_store


class GameServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class GameService:
    def __init__(self, repo: GameRepository, store: SessionStore | None = None):
        self.repo = repo
        self.store = store or session_store
        self.learning = LearningService(repo)

    async def _load_playable_data(self) -> tuple[list, list, dict, list[UUID]]:
        characters = await self.repo.get_active_characters()
        questions = await self.repo.get_active_questions()

        if not characters:
            raise GameServiceError("No active characters available", 503)
        if not questions:
            raise GameServiceError("No active questions available", 503)

        character_ids = [c.id for c in characters]
        question_ids = [q.id for q in questions]

        rows = await self.repo.get_likelihoods(character_ids, question_ids)
        likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry] = {}
        for row in rows:
            likelihoods[(row.character_id, row.question_id)] = LikelihoodEntry(
                likelihood=row.likelihood,
                sample_size=row.sample_size,
            )

        return characters, questions, likelihoods, question_ids

    async def start_game(self, user_id: UUID | None = None) -> dict:
        characters, questions, likelihoods, question_ids = await self._load_playable_data()

        db_session = await self.repo.create_session(user_id=user_id)
        character_ids = [c.id for c in characters]

        engine = create_initial_state(character_ids, likelihoods)
        first_q_id = select_next_question(
            engine,
            question_ids,
            min_samples=settings.new_question_min_samples,
        )
        if first_q_id is None:
            raise GameServiceError("No eligible questions to start game", 503)

        question_refs = {
            q.id: QuestionRef(id=q.id, text=q.text, category=q.category) for q in questions
        }
        character_names = {c.id: c.name for c in characters}

        live = LiveSession(
            session_id=db_session.id,
            engine=engine,
            question_refs=question_refs,
            character_names=character_names,
            all_question_ids=question_ids,
            pending_question_id=first_q_id,
        )
        self.store.save(live)
        await self.repo.commit()

        first_q = question_refs[first_q_id]
        return {
            "session_id": str(db_session.id),
            "question": {"id": str(first_q.id), "text": first_q.text},
            "questions_asked": 0,
        }

    def _state_payload(self, live: LiveSession) -> dict:
        """Current session state in the same shape as an answer response."""
        top_confidence = max(live.engine.probabilities.values(), default=0.0)
        # A session with no pending question has nothing left to ask -> guess
        ready = live.awaiting_guess or live.pending_question_id is None
        if ready and not live.awaiting_guess:
            live.awaiting_guess = True
            self.store.save(live)
        payload = {
            "status": "ready_to_guess" if ready else "asking",
            "next_question": None,
            "questions_asked": live.engine.questions_asked,
            "top_confidence": round(top_confidence, 4),
        }
        if not ready:
            q = live.question_refs[live.pending_question_id]
            payload["next_question"] = {"id": str(q.id), "text": q.text}
        return payload

    async def get_state(self, session_id: UUID) -> dict:
        return self._state_payload(await self._get_live_session(session_id))

    async def submit_answer(
        self,
        session_id: UUID,
        question_id: UUID,
        answer: str,
    ) -> dict:
        live = await self._get_live_session(session_id)

        if question_id == live.last_answered_question_id:
            # Duplicate/retried request for a question already processed —
            # replay the current state instead of erroring (idempotency).
            return self._state_payload(live)

        if live.awaiting_guess:
            raise GameServiceError("Session is ready to guess; call /game/guess", 409)

        if live.pending_question_id != question_id:
            raise GameServiceError("Question does not match the current pending question", 409)

        try:
            answer_enum = Answer(answer)
        except ValueError as exc:
            raise GameServiceError(
                f"Invalid answer. Must be one of: {', '.join(a.value for a in Answer)}"
            ) from exc

        engine, entropy_before = process_answer(live.engine, question_id, answer_enum)

        await self.repo.save_answer(
            session_id=session_id,
            question_id=question_id,
            answer=answer,
            order_index=engine.questions_asked,
            entropy_before=entropy_before,
        )
        await self.repo.increment_question_times_asked(question_id)

        db_session = await self.repo.get_session(session_id)
        if db_session:
            db_session.questions_asked_count = engine.questions_asked

        confidence, next_q_id = decide_after_answer(
            engine,
            live.all_question_ids,
            confidence_high=settings.confidence_high,
            confidence_separation=settings.confidence_separation,
            confidence_margin=settings.confidence_margin,
            max_questions=settings.max_questions,
        )

        # No unused questions left -> guess best-so-far (TDD Section 2.5,
        # same spirit as the question-budget rule)
        must_guess = confidence.should_guess or next_q_id is None

        live.engine = engine
        live.pending_question_id = None if must_guess else next_q_id
        live.last_answered_question_id = question_id
        live.awaiting_guess = must_guess
        self.store.save(live)
        await self.repo.commit()

        if must_guess:
            return {
                "status": "ready_to_guess",
                "next_question": None,
                "questions_asked": engine.questions_asked,
                "top_confidence": round(confidence.confidence, 4),
            }

        next_q = live.question_refs[next_q_id]
        return {
            "status": "asking",
            "next_question": {"id": str(next_q.id), "text": next_q.text},
            "questions_asked": engine.questions_asked,
            "top_confidence": round(confidence.confidence, 4),
        }

    async def make_guess(self, session_id: UUID) -> dict:
        live = await self._get_live_session(session_id)
        if not live.awaiting_guess:
            raise GameServiceError("Engine is not ready to guess yet", 409)

        top_id = max(live.engine.probabilities, key=live.engine.probabilities.get)
        confidence = live.engine.probabilities[top_id]
        character = await self.repo.get_character(top_id)
        if not character:
            raise GameServiceError("Top candidate character not found", 500)

        db_session = await self.repo.get_session(session_id)
        if db_session:
            db_session.guessed_character_id = top_id

        await self.repo.commit()

        return {
            "character": {
                "id": str(character.id),
                "name": character.name,
                "image_url": character.image_url,
            },
            "confidence": round(confidence, 4),
        }

    async def confirm_guess(
        self,
        session_id: UUID,
        correct: bool,
        actual_character_id: UUID | None = None,
    ) -> dict:
        live = await self._get_live_session(session_id)
        db_session = await self.repo.get_session(session_id)
        if not db_session:
            raise GameServiceError("Session not found", 404)

        if correct:
            db_session.status = GameSessionStatus.GUESSED_CORRECT
            db_session.actual_character_id = db_session.guessed_character_id
            db_session.ended_at = datetime.now(timezone.utc)
            if db_session.guessed_character_id:
                char = await self.repo.get_character(db_session.guessed_character_id)
                if char:
                    char.times_guessed_correctly += 1
                await self.learning.learn_from_session(session_id, db_session.guessed_character_id)
            await self.repo.commit()
            self.store.delete(session_id)
            return {"status": "guessed_correct"}

        # Incorrect guess — remove guessed character and resume (TDD Section 2.5)
        if actual_character_id is None:
            raise GameServiceError(
                "actual_character_id required when correct=false for existing characters",
                400,
            )

        guessed_id = db_session.guessed_character_id
        if guessed_id:
            char = await self.repo.get_character(guessed_id)
            if char:
                char.times_guessed_incorrectly += 1

        # Learn from the actual character the user was thinking of (TDD Section 4.2)
        await self.learning.learn_from_wrong_guess(session_id, actual_character_id)

        if guessed_id and guessed_id in live.engine.probabilities:
            del live.engine.probabilities[guessed_id]
            live.engine.character_ids = [
                cid for cid in live.engine.character_ids if cid != guessed_id
            ]

        total = sum(live.engine.probabilities.values())
        if total > 0:
            live.engine.probabilities = {
                cid: p / total for cid, p in live.engine.probabilities.items()
            }

        live.awaiting_guess = False
        db_session.actual_character_id = actual_character_id
        db_session.status = GameSessionStatus.IN_PROGRESS
        db_session.guessed_character_id = None

        next_q_id = select_next_question(
            live.engine,
            live.all_question_ids,
            min_samples=settings.new_question_min_samples,
        )
        live.pending_question_id = next_q_id
        self.store.save(live)
        await self.repo.commit()

        if next_q_id is None:
            live.awaiting_guess = True
            self.store.save(live)
            return {"status": "ready_to_guess", "next_question": None}

        next_q = live.question_refs[next_q_id]
        return {
            "status": "resumed",
            "next_question": {"id": str(next_q.id), "text": next_q.text},
        }

    async def suggest_character(
        self,
        session_id: UUID,
        name: str,
        category: str,
    ) -> dict:
        """Wrong guess + character not in DB: queue for moderation (TDD 4.2).
        Created inactive so spam cannot pollute the model until an admin approves."""
        db_session = await self.repo.get_session(session_id)
        if not db_session:
            raise GameServiceError("Session not found", 404)

        character = await self.repo.create_character(
            name=name, category=category, is_active=False
        )
        if db_session.status == GameSessionStatus.IN_PROGRESS:
            db_session.status = GameSessionStatus.GUESSED_INCORRECT
            db_session.ended_at = datetime.now(timezone.utc)
        await self.repo.commit()
        self.store.delete(session_id)
        return {"status": "submitted_for_review", "character_id": str(character.id)}

    async def _get_live_session(self, session_id: UUID) -> LiveSession:
        live = self.store.get(session_id)
        if live:
            return live
        live = await self._rehydrate(session_id)
        if not live:
            raise GameServiceError("Session not found or expired", 404)
        return live

    async def _rehydrate(self, session_id: UUID) -> LiveSession | None:
        """Rebuild live state by replaying the game_answers log through the
        engine. Makes the API stateless: any worker/restart can resume any
        in-progress session (docs/ARCHITECTURE.md Section 3.1)."""
        db_session = await self.repo.get_session(session_id)
        if not db_session or db_session.status != GameSessionStatus.IN_PROGRESS:
            return None

        characters, questions, likelihoods, question_ids = await self._load_playable_data()
        engine = create_initial_state([c.id for c in characters], likelihoods)

        answers = await self.repo.get_session_answers(session_id)
        last_qid: UUID | None = None
        for game_answer in answers:
            engine, _ = process_answer(engine, game_answer.question_id, game_answer.answer.value)
            last_qid = game_answer.question_id

        confidence, next_q_id = decide_after_answer(
            engine,
            question_ids,
            confidence_high=settings.confidence_high,
            confidence_separation=settings.confidence_separation,
            confidence_margin=settings.confidence_margin,
            max_questions=settings.max_questions,
        )
        must_guess = confidence.should_guess or next_q_id is None

        live = LiveSession(
            session_id=session_id,
            engine=engine,
            question_refs={
                q.id: QuestionRef(id=q.id, text=q.text, category=q.category) for q in questions
            },
            character_names={c.id: c.name for c in characters},
            all_question_ids=question_ids,
            pending_question_id=None if must_guess else next_q_id,
            last_answered_question_id=last_qid,
            awaiting_guess=must_guess,
        )
        self.store.save(live)
        return live
