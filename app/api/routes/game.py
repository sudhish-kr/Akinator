"""Game REST API — thin routes over GameService / Session Manager."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_game_service, get_optional_user_id
from app.api.schemas.game import (
    AnswerRequest,
    AnswerResponse,
    GuessConfirmRequest,
    GuessConfirmResponse,
    GuessResponse,
    LearnRequest,
    LearnResponse,
    QuestionOut,
    RemainingCandidatesResponse,
    StartGameResponse,
    SuggestCharacterRequest,
    SuggestCharacterResponse,
)
from app.services.game_service import GameService, GameServiceError

router = APIRouter(prefix="/game", tags=["game"])


def _http_error(exc: GameServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


def _answer_response(result: dict) -> AnswerResponse:
    next_q = result.get("next_question")
    return AnswerResponse(
        status=result["status"],
        next_question=QuestionOut(**next_q) if next_q else None,
        questions_asked=result["questions_asked"],
        top_confidence=result["top_confidence"],
    )


@router.post("/start", response_model=StartGameResponse)
async def start_game(
    service: GameService = Depends(get_game_service),
    user_id: UUID | None = Depends(get_optional_user_id),
):
    try:
        return StartGameResponse(**(await service.start_game(user_id=user_id)))
    except GameServiceError as exc:
        raise _http_error(exc) from exc


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    body: AnswerRequest,
    service: GameService = Depends(get_game_service),
):
    try:
        result = await service.submit_answer(body.session_id, body.question_id, body.answer)
        return _answer_response(result)
    except GameServiceError as exc:
        raise _http_error(exc) from exc


@router.get("/state/{session_id}", response_model=AnswerResponse)
async def get_state(
    session_id: UUID,
    service: GameService = Depends(get_game_service),
):
    try:
        return _answer_response(await service.get_state(session_id))
    except GameServiceError as exc:
        raise _http_error(exc) from exc


@router.get("/guess/{session_id}", response_model=GuessResponse)
async def get_guess(
    session_id: UUID,
    service: GameService = Depends(get_game_service),
):
    try:
        return GuessResponse(**(await service.make_guess(session_id)))
    except GameServiceError as exc:
        raise _http_error(exc) from exc


@router.post("/learn", response_model=LearnResponse)
async def learn(
    body: LearnRequest,
    service: GameService = Depends(get_game_service),
):
    try:
        result = await service.learn(
            body.session_id,
            body.character_id,
            wrong_guess=body.wrong_guess,
            distinguishing_question_id=body.distinguishing_question_id,
            distinguishing_answer=body.distinguishing_answer,
        )
        return LearnResponse(**result)
    except GameServiceError as exc:
        raise _http_error(exc) from exc


# Additional session lifecycle routes (confirm / suggest) — thin service passthroughs
@router.post("/guess/confirm", response_model=GuessConfirmResponse)
async def confirm_guess(
    body: GuessConfirmRequest,
    service: GameService = Depends(get_game_service),
):
    try:
        result = await service.confirm_guess(
            body.session_id, body.correct, body.actual_character_id
        )
        next_q = result.get("next_question")
        return GuessConfirmResponse(
            status=result["status"],
            next_question=QuestionOut(**next_q) if next_q else None,
        )
    except GameServiceError as exc:
        raise _http_error(exc) from exc


@router.post("/suggest-character", response_model=SuggestCharacterResponse, status_code=201)
async def suggest_character(
    body: SuggestCharacterRequest,
    service: GameService = Depends(get_game_service),
):
    try:
        result = await service.suggest_character(body.session_id, body.name, body.category)
        return SuggestCharacterResponse(**result)
    except GameServiceError as exc:
        raise _http_error(exc) from exc


@router.get("/candidates/{session_id}", response_model=RemainingCandidatesResponse)
async def list_remaining_candidates(
    session_id: UUID,
    category: str | None = None,
    q: str | None = None,
    limit: int = Query(40, ge=1, le=100),
    service: GameService = Depends(get_game_service),
):
    try:
        return RemainingCandidatesResponse(
            **(
                await service.list_remaining_candidates(
                    session_id, category=category, q=q, limit=limit
                )
            )
        )
    except GameServiceError as exc:
        raise _http_error(exc) from exc
