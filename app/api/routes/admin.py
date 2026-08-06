import math
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.api.deps import get_game_repository, require_admin
from app.api.schemas.admin import (
    CharacterCreate,
    CharacterItem,
    CharacterListResponse,
    CharacterUpdate,
    KnowledgeExportResponse,
    KnowledgeImportRequest,
    KnowledgeImportResponse,
    PaginatedMeta,
    QuestionCreate,
    QuestionItem,
    QuestionListResponse,
    QuestionUpdate,
    StatisticsResponse,
)
from app.db.repositories.game_repository import GameRepository
from app.services.knowledge_io import KnowledgeIOError, KnowledgeIOService
from app.services.media_service import MediaError, save_character_image

router = APIRouter(tags=["catalog"])


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


# ---- Admin-only APIs (RBAC: admin role required) ----

admin_router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)],
)


@admin_router.post("/characters", response_model=CharacterItem, status_code=201)
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


@admin_router.patch("/characters/{character_id}", response_model=CharacterItem)
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


@admin_router.post("/characters/{character_id}/image", response_model=CharacterItem)
async def upload_character_image(
    character_id: UUID,
    file: UploadFile = File(...),
    repo: GameRepository = Depends(get_game_repository),
):
    character = await repo.get_character(character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    try:
        path = await save_character_image(file, character_id)
    except MediaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    character.image_url = path
    await repo.commit()
    return _character_item(character)


@admin_router.post("/questions", response_model=QuestionItem, status_code=201)
async def create_question(
    body: QuestionCreate,
    repo: GameRepository = Depends(get_game_repository),
):
    question = await repo.create_question(
        text=body.text, category=body.category, is_active=body.is_active
    )
    await repo.commit()
    return _question_item(question)


@admin_router.patch("/questions/{question_id}", response_model=QuestionItem)
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


@admin_router.get("/knowledge/export", response_model=KnowledgeExportResponse)
async def export_knowledge(repo: GameRepository = Depends(get_game_repository)):
    return KnowledgeExportResponse(**(await KnowledgeIOService(repo).export_knowledge()))


@admin_router.post("/knowledge/import", response_model=KnowledgeImportResponse)
async def import_knowledge(
    body: KnowledgeImportRequest,
    repo: GameRepository = Depends(get_game_repository),
):
    if not body.characters and not body.questions:
        raise HTTPException(status_code=400, detail="Import must include characters or questions")
    try:
        result = await KnowledgeIOService(repo).import_knowledge(
            characters=[c.model_dump() for c in body.characters],
            questions=[q.model_dump() for q in body.questions],
        )
    except KnowledgeIOError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
    return KnowledgeImportResponse(**result)


router.include_router(admin_router)
