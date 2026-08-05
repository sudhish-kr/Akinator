from uuid import UUID

from pydantic import BaseModel, Field


class QuestionOut(BaseModel):
    id: str
    text: str


class StartGameResponse(BaseModel):
    session_id: str
    question: QuestionOut
    questions_asked: int = 0


class AnswerRequest(BaseModel):
    session_id: UUID
    question_id: UUID
    answer: str = Field(
        description="One of: yes, probably_yes, dont_know, probably_no, no"
    )


class AnswerResponse(BaseModel):
    status: str
    next_question: QuestionOut | None = None
    questions_asked: int
    top_confidence: float


class GuessRequest(BaseModel):
    session_id: UUID


class CharacterOut(BaseModel):
    id: str
    name: str
    image_url: str | None = None


class GuessResponse(BaseModel):
    character: CharacterOut
    confidence: float


class GuessConfirmRequest(BaseModel):
    session_id: UUID
    correct: bool
    actual_character_id: UUID | None = None


class GuessConfirmResponse(BaseModel):
    status: str
    next_question: QuestionOut | None = None


class SuggestCharacterRequest(BaseModel):
    session_id: UUID
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(default="unknown", max_length=100)


class SuggestCharacterResponse(BaseModel):
    status: str
    character_id: str
