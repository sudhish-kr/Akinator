from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_game_service, get_optional_user_id
from app.api.schemas.game import (
    AnswerRequest,
    AnswerResponse,
    GuessConfirmRequest,
    GuessConfirmResponse,
    GuessRequest,
    GuessResponse,
    QuestionOut,
    StartGameResponse,
    SuggestCharacterRequest,
    SuggestCharacterResponse,
)
from app.services.game_service import GameService, GameServiceError

router = APIRouter(prefix="/game", tags=["game"])


def _handle_service_error(exc: GameServiceError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=str(exc))


@router.post("/start", response_model=StartGameResponse)
async def start_game(
    service: GameService = Depends(get_game_service),
    user_id: UUID | None = Depends(get_optional_user_id),
):
    try:
        result = await service.start_game(user_id=user_id)
        return StartGameResponse(**result)
    except GameServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.get("/{session_id}/state", response_model=AnswerResponse)
async def get_state(
    session_id: UUID,
    service: GameService = Depends(get_game_service),
):
    try:
        result = await service.get_state(session_id)
        next_q = result.get("next_question")
        return AnswerResponse(
            status=result["status"],
            next_question=QuestionOut(**next_q) if next_q else None,
            questions_asked=result["questions_asked"],
            top_confidence=result["top_confidence"],
        )
    except GameServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.post("/answer", response_model=AnswerResponse)
async def submit_answer(
    body: AnswerRequest,
    service: GameService = Depends(get_game_service),
):
    try:
        result = await service.submit_answer(body.session_id, body.question_id, body.answer)
        next_q = result.get("next_question")
        return AnswerResponse(
            status=result["status"],
            next_question=QuestionOut(**next_q) if next_q else None,
            questions_asked=result["questions_asked"],
            top_confidence=result["top_confidence"],
        )
    except GameServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.post("/guess", response_model=GuessResponse)
async def make_guess(
    body: GuessRequest,
    service: GameService = Depends(get_game_service),
):
    try:
        result = await service.make_guess(body.session_id)
        return GuessResponse(**result)
    except GameServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.post("/suggest-character", response_model=SuggestCharacterResponse, status_code=201)
async def suggest_character(
    body: SuggestCharacterRequest,
    service: GameService = Depends(get_game_service),
):
    try:
        result = await service.suggest_character(body.session_id, body.name, body.category)
        return SuggestCharacterResponse(**result)
    except GameServiceError as exc:
        raise _handle_service_error(exc) from exc


@router.post("/guess/confirm", response_model=GuessConfirmResponse)
async def confirm_guess(
    body: GuessConfirmRequest,
    service: GameService = Depends(get_game_service),
):
    try:
        result = await service.confirm_guess(
            body.session_id,
            body.correct,
            body.actual_character_id,
        )
        next_q = result.get("next_question")
        return GuessConfirmResponse(
            status=result["status"],
            next_question=QuestionOut(**next_q) if next_q else None,
        )
    except GameServiceError as exc:
        raise _handle_service_error(exc) from exc
