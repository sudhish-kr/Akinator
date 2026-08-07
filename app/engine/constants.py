from enum import Enum

# Answer weights per TDD v1.1 Section 2.1
ANSWER_WEIGHTS: dict[str, float] = {
    "yes": 1.0,
    "probably_yes": 0.75,
    "dont_know": 0.5,
    "probably_no": 0.25,
    "no": 0.0,
}


class Answer(str, Enum):
    YES = "yes"
    PROBABLY_YES = "probably_yes"
    DONT_KNOW = "dont_know"
    PROBABLY_NO = "probably_no"
    NO = "no"

    @property
    def weight(self) -> float:
        return ANSWER_WEIGHTS[self.value]


ALL_ANSWERS: tuple[Answer, ...] = tuple(Answer)

# Default engine thresholds (overridable via Settings in services layer)
DEFAULT_ELIMINATION_FLOOR = 0.0005
DEFAULT_ELIMINATION_MAGNITUDE = 1000.0
DEFAULT_CONFIDENCE_HIGH = 0.85
DEFAULT_CONFIDENCE_SEPARATION = 0.6
DEFAULT_CONFIDENCE_MARGIN = 0.4
DEFAULT_MAX_QUESTIONS = 25
DEFAULT_IG_TIE_THRESHOLD = 0.001
DEFAULT_CONSECUTIVE_DONT_KNOW_CAP = 5
DEFAULT_NEW_QUESTION_MIN_SAMPLES = 5
DEFAULT_LEARNING_RATE = 0.07

# Dynamic question selection (candidate-focused, category-aware, diverse)
DEFAULT_CATEGORY_CONFIDENCE_GATE = 0.20
DEFAULT_CATEGORY_IG_BONUS = 0.12
DEFAULT_CANDIDATE_MASS_FOCUS = 0.92
DEFAULT_DIVERSITY_TOP_K = 4
DEFAULT_DIVERSITY_MARGIN = 0.04

# Character KB category → preferred question.category tags (from knowledge seed).
CHARACTER_CATEGORY_QUESTION_PREFERENCES: dict[str, frozenset[str]] = {
    "Movies": frozenset({"Movies", "Fictional traits", "Personality", "Awards"}),
    "TV Shows": frozenset({"TV", "Fictional traits", "Personality", "Time period"}),
    "Anime": frozenset({"Anime", "Fictional traits", "Nationality", "Personality"}),
    "Cartoons": frozenset({"Cartoons", "Fictional traits", "Personality", "Age"}),
    "Sports": frozenset({"Sports", "Physical appearance", "Awards", "Nationality"}),
    "Scientists": frozenset({"Science", "Profession", "Technology", "Nationality"}),
    "Historical Figures": frozenset({"History", "Time period", "Politics", "Profession"}),
    "Politicians": frozenset({"Politics", "History", "Nationality", "Time period"}),
    "Musicians": frozenset({"Music", "Awards", "Time period", "Nationality"}),
    "Business Leaders": frozenset({"Technology", "Profession", "Awards", "Nationality"}),
    "Gaming": frozenset({"Gaming", "Fictional traits", "Personality", "Physical appearance"}),
    "Mythology": frozenset({"Mythology", "Fictional traits", "Relationships", "History"}),
    "Literature": frozenset({"Literature", "Fictional traits", "Personality", "Time period"}),
}
