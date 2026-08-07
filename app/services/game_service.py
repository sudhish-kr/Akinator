from datetime import datetime, timezone
from uuid import UUID

from app.config import settings
from app.db.models import GameSessionStatus
from app.db.repositories.game_repository import GameRepository
from app.engine.explain import AnswerObservation, build_guess_explanation
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    decide_after_answer,
    process_answer,
    select_next_question,
)
from app.services.session_manager import ConfidenceThresholds, GameSessionManager
from app.services.session_store import LiveSession, SessionStore, StoredAnswer, session_store
from app.monitoring.instrumentation import track_ai_inference


class GameServiceError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code


class GameService:
    def __init__(self, repo: GameRepository, store: SessionStore | None = None):
        self.repo = repo
        self.store = store or session_store
        self.sessions = GameSessionManager(
            thresholds=ConfidenceThresholds(
                high=settings.confidence_high,
                separation=settings.confidence_separation,
                margin=settings.confidence_margin,
                max_questions=settings.max_questions,
            ),
            min_samples=settings.new_question_min_samples,
        )

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

        question_refs = {
            q.id: QuestionRef(id=q.id, text=q.text, category=q.category) for q in questions
        }
        character_names = {c.id: c.name for c in characters}

        try:
            with track_ai_inference("start_game"):
                live = self.sessions.start(
                    session_id=db_session.id,
                    character_ids=[c.id for c in characters],
                    likelihoods=likelihoods,
                    question_ids=question_ids,
                    question_refs=question_refs,
                    character_names=character_names,
                )
        except ValueError as exc:
            raise GameServiceError(str(exc), 503) from exc

        self.store.save(live)
        await self.repo.commit()

        first_q = question_refs[live.pending_question_id]
        return {
            "session_id": str(db_session.id),
            "question": {"id": str(first_q.id), "text": first_q.text},
            "questions_asked": 0,
        }

    def _state_payload(self, live: LiveSession) -> dict:
        top_confidence = max(live.engine.probabilities.values(), default=0.0)
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
            return self._state_payload(live)

        try:
            with track_ai_inference("submit_answer"):
                turn = self.sessions.submit_answer(live, question_id, answer)
        except ValueError as exc:
            msg = str(exc)
            code = 409 if "ready to guess" in msg or "does not match" in msg else 400
            raise GameServiceError(msg, code) from exc

        await self.repo.save_answer(
            session_id=session_id,
            question_id=question_id,
            answer=answer,
            order_index=turn.questions_asked,
            entropy_before=turn.entropy_before,
        )
        await self.repo.increment_question_times_asked(question_id)

        db_session = await self.repo.get_session(session_id)
        if db_session:
            db_session.questions_asked_count = turn.questions_asked
            db_session.last_activity_at = datetime.now(timezone.utc)

        self.store.save(live)
        await self.repo.commit()

        if turn.status == "ready_to_guess":
            return {
                "status": "ready_to_guess",
                "next_question": None,
                "questions_asked": turn.questions_asked,
                "top_confidence": round(turn.top_confidence, 4),
            }

        next_q = live.question_refs[turn.next_question_id]
        return {
            "status": "asking",
            "next_question": {"id": str(next_q.id), "text": next_q.text},
            "questions_asked": turn.questions_asked,
            "top_confidence": round(turn.top_confidence, 4),
        }

    async def make_guess(self, session_id: UUID) -> dict:
        live = await self._get_live_session(session_id)
        if not live.awaiting_guess:
            raise GameServiceError("Engine is not ready to guess yet", 409)

        with track_ai_inference("make_guess"):
            guess = self.sessions.best_guess(live)
            if guess is None:
                raise GameServiceError("No candidates available to guess", 500)
            top_id, confidence = guess

            character = await self.repo.get_character(top_id)
            if not character:
                raise GameServiceError("Top candidate character not found", 500)

            db_session = await self.repo.get_session(session_id)
            if db_session:
                db_session.guessed_character_id = top_id
                db_session.last_activity_at = datetime.now(timezone.utc)

            await self.repo.commit()

            explanation = build_guess_explanation(
                guessed_id=top_id,
                guessed_name=character.name,
                confidence=confidence,
                probabilities=live.engine.probabilities,
                character_ids=list(live.engine.character_ids),
                character_names=live.character_names,
                likelihoods=live.engine.likelihoods,
                answers=[
                    AnswerObservation(question_id=a.question_id, answer=a.answer)
                    for a in live.answers
                ],
                question_refs=live.question_refs,
            )

        return {
            "character": {
                "id": str(character.id),
                "name": character.name,
                "image_url": character.image_url,
            },
            "confidence": round(confidence, 4),
            **explanation,
        }

    async def learn(
        self,
        session_id: UUID,
        character_id: UUID,
        *,
        wrong_guess: bool = False,
        distinguishing_question_id: UUID | None = None,
        distinguishing_answer: str | None = None,
    ) -> dict:
        """Close the session quickly; learning + analytics run in Celery workers."""
        from app.workers.queue import enqueue_post_game

        db_session = await self.repo.get_session(session_id)
        if not db_session:
            raise GameServiceError("Session not found", 404)
        if db_session.status != GameSessionStatus.IN_PROGRESS:
            raise GameServiceError("Session is already closed", 409)

        now = datetime.now(timezone.utc)
        guessed_id = db_session.guessed_character_id

        if wrong_guess:
            db_session.status = GameSessionStatus.GUESSED_INCORRECT
            db_session.actual_character_id = character_id
        else:
            db_session.status = GameSessionStatus.GUESSED_CORRECT
            db_session.actual_character_id = character_id
            if not db_session.guessed_character_id:
                db_session.guessed_character_id = character_id

        db_session.ended_at = now
        db_session.last_activity_at = now
        await self.repo.commit()
        self.store.delete(session_id)

        jobs = enqueue_post_game(
            session_id,
            character_id,
            wrong_guess=wrong_guess,
            guessed_character_id=guessed_id,
            distinguishing_question_id=distinguishing_question_id,
            distinguishing_answer=distinguishing_answer,
        )
        # updates stays 0 in the HTTP response — workers apply KB changes async
        return {"status": "learned", "updates": 0, **jobs}

    async def confirm_guess(
        self,
        session_id: UUID,
        correct: bool,
        actual_character_id: UUID | None = None,
    ) -> dict:
        from app.workers.queue import enqueue_post_game

        live = await self._get_live_session(session_id)
        db_session = await self.repo.get_session(session_id)
        if not db_session:
            raise GameServiceError("Session not found", 404)

        if correct:
            db_session.status = GameSessionStatus.GUESSED_CORRECT
            db_session.actual_character_id = db_session.guessed_character_id
            db_session.ended_at = datetime.now(timezone.utc)
            await self.repo.commit()
            self.store.delete(session_id)
            if db_session.guessed_character_id:
                enqueue_post_game(
                    session_id,
                    db_session.guessed_character_id,
                    wrong_guess=False,
                    guessed_character_id=db_session.guessed_character_id,
                )
            return {"status": "guessed_correct"}

        if actual_character_id is None:
            raise GameServiceError(
                "actual_character_id required when correct=false for existing characters",
                400,
            )

        guessed_id = db_session.guessed_character_id
        if guessed_id:
            # Persist the rejection so rehydration can re-exclude this
            # character after a cache loss (docs/ARCHITECTURE.md gap fix)
            await self.repo.record_rejected_guess(session_id, guessed_id)

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
        db_session.last_activity_at = datetime.now(timezone.utc)

        next_q_id = select_next_question(
            live.engine,
            live.all_question_ids,
            min_samples=settings.new_question_min_samples,
        )
        live.pending_question_id = next_q_id
        self.store.save(live)
        await self.repo.commit()

        enqueue_post_game(
            session_id,
            actual_character_id,
            wrong_guess=True,
            guessed_character_id=guessed_id,
        )

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
        db_session = await self.repo.get_session(session_id)
        if not db_session or db_session.status != GameSessionStatus.IN_PROGRESS:
            return None

        characters, questions, likelihoods, question_ids = await self._load_playable_data()
        engine = create_initial_state([c.id for c in characters], likelihoods)

        # Re-exclude characters the user already rejected in this session
        rejected = await self.repo.get_rejected_character_ids(session_id)
        if rejected:
            engine.probabilities = {
                cid: p for cid, p in engine.probabilities.items() if cid not in rejected
            }
            engine.character_ids = [cid for cid in engine.character_ids if cid not in rejected]
            total = sum(engine.probabilities.values())
            if total > 0:
                engine.probabilities = {
                    cid: p / total for cid, p in engine.probabilities.items()
                }

        answers = await self.repo.get_session_answers(session_id)
        stored: list[StoredAnswer] = []
        last_qid: UUID | None = None
        for game_answer in answers:
            engine, _ = process_answer(engine, game_answer.question_id, game_answer.answer.value)
            stored.append(
                StoredAnswer(question_id=game_answer.question_id, answer=game_answer.answer.value)
            )
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
            answers=stored,
        )
        self.store.save(live)
        return live
