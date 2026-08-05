import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_game_repository, require_admin
from app.api.schemas.admin import (
    CharacterCreate,
    CharacterItem,
    CharacterListResponse,
    CharacterUpdate,
    PaginatedMeta,
    QuestionCreate,
    QuestionItem,
    QuestionListResponse,
    QuestionUpdate,
    StatisticsResponse,
)
from app.db.repositories.game_repository import GameRepository

router = APIRouter(tags=["admin"])


def _character_item(c) -> CharacterItem:
    return CharacterItem(
        id=str(c.id),
        name=c.name,
        category=c.category,
        image_url=c.image_url,
        is_active=c.is_active,
        times_guessed_correctly=c.times_guessed_correctly,
        times_guessed_incorrectly=c.times_guessed_incorrectly,
    )


def _question_item(q) -> QuestionItem:
    return QuestionItem(
        id=str(q.id),
        text=q.text,
        category=q.category,
        is_active=q.is_active,
        times_asked=q.times_asked,
        avg_information_gain=q.avg_information_gain,
    )


def _paginated_meta(page: int, page_size: int, total: int) -> PaginatedMeta:
    return PaginatedMeta(
        page=page,
        page_size=page_size,
        total=total,
        total_pages=max(1, math.ceil(total / page_size)),
    )


@router.get("/characters", response_model=CharacterListResponse)
async def list_characters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    is_active: bool | None = None,
    repo: GameRepository = Depends(get_game_repository),
):
    items, total = await repo.list_characters(page, page_size, category, is_active)
    return CharacterListResponse(
        items=[
            CharacterItem(
                id=str(c.id),
                name=c.name,
                category=c.category,
                image_url=c.image_url,
                is_active=c.is_active,
                times_guessed_correctly=c.times_guessed_correctly,
                times_guessed_incorrectly=c.times_guessed_incorrectly,
            )
            for c in items
        ],
        meta=_paginated_meta(page, page_size, total),
    )


@router.get("/questions", response_model=QuestionListResponse)
async def list_questions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: str | None = None,
    is_active: bool | None = None,
    repo: GameRepository = Depends(get_game_repository),
):
    items, total = await repo.list_questions(page, page_size, category, is_active)
    return QuestionListResponse(
        items=[
            QuestionItem(
                id=str(q.id),
                text=q.text,
                category=q.category,
                is_active=q.is_active,
                times_asked=q.times_asked,
                avg_information_gain=q.avg_information_gain,
            )
            for q in items
        ],
        meta=_paginated_meta(page, page_size, total),
    )


@router.get("/statistics", response_model=StatisticsResponse)
async def get_statistics(repo: GameRepository = Depends(get_game_repository)):
    data = await repo.get_statistics()
    return StatisticsResponse(**data)


# ---- Admin-only mutations (RBAC via require_admin) ----


@router.post(
    "/admin/characters",
    response_model=CharacterItem,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create_character(
    body: CharacterCreate,
    repo: GameRepository = Depends(get_game_repository),
):
    character = await repo.create_character(
        name=body.name,
        category=body.category,
        image_url=body.image_url,
        is_active=body.is_active,
    )
    await repo.commit()
    return _character_item(character)


@router.patch(
    "/admin/characters/{character_id}",
    response_model=CharacterItem,
    dependencies=[Depends(require_admin)],
)
async def update_character(
    character_id: UUID,
    body: CharacterUpdate,
    repo: GameRepository = Depends(get_game_repository),
):
    character = await repo.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(character, field, value)
    await repo.commit()
    return _character_item(character)


@router.post(
    "/admin/questions",
    response_model=QuestionItem,
    status_code=201,
    dependencies=[Depends(require_admin)],
)
async def create_question(
    body: QuestionCreate,
    repo: GameRepository = Depends(get_game_repository),
):
    question = await repo.create_question(
        text=body.text, category=body.category, is_active=body.is_active
    )
    await repo.commit()
    return _question_item(question)


@router.patch(
    "/admin/questions/{question_id}",
    response_model=QuestionItem,
    dependencies=[Depends(require_admin)],
)
async def update_question(
    question_id: UUID,
    body: QuestionUpdate,
    repo: GameRepository = Depends(get_game_repository),
):
    question = await repo.get_question(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    updates = body.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(question, field, value)
    await repo.commit()
    return _question_item(question)
