from pydantic import BaseModel, Field


class CharacterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=100)
    image_url: str | None = None
    is_active: bool = True


class CharacterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    image_url: str | None = None
    is_active: bool | None = None


class QuestionCreate(BaseModel):
    text: str = Field(min_length=5, max_length=512)
    category: str | None = None
    is_active: bool = True


class QuestionUpdate(BaseModel):
    text: str | None = Field(default=None, min_length=5, max_length=512)
    category: str | None = None
    is_active: bool | None = None


class PaginatedMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int


class CharacterItem(BaseModel):
    id: str
    name: str
    category: str
    image_url: str | None = None
    is_active: bool
    times_guessed_correctly: int
    times_guessed_incorrectly: int


class CharacterListResponse(BaseModel):
    items: list[CharacterItem]
    meta: PaginatedMeta


class QuestionItem(BaseModel):
    id: str
    text: str
    category: str | None = None
    is_active: bool
    times_asked: int
    avg_information_gain: float | None = None


class QuestionListResponse(BaseModel):
    items: list[QuestionItem]
    meta: PaginatedMeta


class QuestionStatItem(BaseModel):
    id: str
    text: str
    times_asked: int


class CharacterAccuracyItem(BaseModel):
    id: str
    name: str
    times_guessed_correctly: int
    times_guessed_incorrectly: int
    accuracy: float


class CharacterGuessStatItem(BaseModel):
    id: str
    name: str
    times_guessed: int
    times_guessed_correctly: int
    times_guessed_incorrectly: int


class DailyActivityItem(BaseModel):
    date: str
    games: int


class StatisticsResponse(BaseModel):
    total_games_played: int
    guess_accuracy_rate: float
    learning_rate: float = 0.0
    average_questions_per_game: float = 0.0
    most_asked_questions: list[QuestionStatItem]
    most_guessed_characters: list[CharacterGuessStatItem] = []
    daily_activity: list[DailyActivityItem] = []
    lowest_accuracy_characters: list[CharacterAccuracyItem]


class KnowledgeCharacterExport(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=100)
    image_url: str | None = None
    is_active: bool = True


class KnowledgeQuestionExport(BaseModel):
    text: str = Field(min_length=5, max_length=512)
    category: str | None = None
    is_active: bool = True


class KnowledgeExportResponse(BaseModel):
    version: int = 1
    exported_at: str
    characters: list[KnowledgeCharacterExport]
    questions: list[KnowledgeQuestionExport]


class KnowledgeImportRequest(BaseModel):
    version: int = 1
    characters: list[KnowledgeCharacterExport] = Field(default_factory=list)
    questions: list[KnowledgeQuestionExport] = Field(default_factory=list)


class KnowledgeImportResponse(BaseModel):
    status: str = "imported"
    characters_imported: int
    questions_imported: int
