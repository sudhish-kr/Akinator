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

# --- Hierarchical question selection (Stage A → B → C) ---
DEFAULT_CANDIDATE_MASS_FOCUS = 0.92
DEFAULT_DIVERSITY_TOP_K = 4
DEFAULT_DIVERSITY_MARGIN = 0.04
DEFAULT_CATEGORY_IG_BONUS = 0.12
DEFAULT_BROAD_QUESTION_BONUS = 0.15
DEFAULT_CATEGORY_REMAIN_MASS = 1e-6

# Exit Stage A once a character category is clearly dominant.
DEFAULT_STAGE_A_EXIT_THRESHOLD = 0.35
DEFAULT_STAGE_A_EXIT_MARGIN = 0.10
# Enter Stage C (profession / franchise / niche) once domain dominance is stronger.
DEFAULT_STAGE_C_ENTER_THRESHOLD = 0.50

# Backward-compatible aliases used by older call sites / tests.
DEFAULT_CATEGORY_CONFIDENCE_GATE = DEFAULT_STAGE_A_EXIT_THRESHOLD
DEFAULT_CATEGORY_PREFERENCE_THRESHOLD = DEFAULT_STAGE_A_EXIT_THRESHOLD
DEFAULT_CATEGORY_UNLOCK_THRESHOLD = DEFAULT_STAGE_A_EXIT_THRESHOLD

# Stage A — broad identity only.
STAGE_A_QUESTION_CATEGORIES: frozenset[str] = frozenset(
    {
        "Personality",
        "Gender",
        "Age",
        "Fictional traits",
        "Physical appearance",
        "Nationality",
    }
)

# Stage B — domain detection (general domain questions).
STAGE_B_QUESTION_CATEGORIES: frozenset[str] = frozenset(
    {
        "Sports",
        "Movies",
        "TV",
        "Anime",
        "Cartoons",
        "Gaming",
        "Politics",
        "Science",
        "Music",
        "Literature",
        "History",
        "Mythology",
        "Technology",
    }
)

# Stage C — specific professions / awards / niche (category-tagged).
STAGE_C_QUESTION_CATEGORIES: frozenset[str] = frozenset(
    {
        "Profession",
        "Awards",
        "Relationships",
        "Time period",
    }
)

# Keywords that push an otherwise Stage-B domain question into Stage C.
STAGE_C_KEYWORDS: frozenset[str] = frozenset(
    {
        "chef",
        "architect",
        "lawyer",
        "doctor",
        "teacher",
        "pilot",
        "police",
        "cricket",
        "football",
        "soccer",
        "basketball",
        "tennis",
        "baseball",
        "hockey",
        "golf",
        "olympics",
        "marvel",
        "dc comic",
        "nobel",
        "singer",
        "rapper",
        "actor",
        "actress",
        "prime minister",
        "president",
        "ninja",
        "samurai",
        "jedi",
        "wizard",
        "superhero",
        "k-pop",
        "robot anime",
        "love story anime",
        "sports anime",
        "another-world",
    }
)

# Profession-like words that must never appear in Stage A / early Stage B picks.
PROFESSION_SPECIFIC_KEYWORDS: frozenset[str] = frozenset(
    {
        "chef",
        "architect",
        "lawyer",
        "doctor",
        "teacher",
        "pilot",
        "police",
        "reporter",
        "comedian",
        "fashion model",
        "artist",
        "actor",
        "actress",
        "singer",
        "rapper",
        "prime minister",
        "president",
    }
)

FICTIONAL_CHARACTER_CATEGORIES: frozenset[str] = frozenset(
    {
        "Movies",
        "TV Shows",
        "Anime",
        "Cartoons",
        "Gaming",
        "Mythology",
        "Literature",
    }
)

# Question.category → character categories that must remain / dominate for domain Qs.
DOMAIN_QUESTION_CATEGORY_REQUIREMENTS: dict[str, frozenset[str]] = {
    "Anime": frozenset({"Anime"}),
    "Sports": frozenset({"Sports"}),
    "Movies": frozenset({"Movies"}),
    "TV": frozenset({"TV Shows"}),
    "Cartoons": frozenset({"Cartoons"}),
    "Gaming": frozenset({"Gaming"}),
    "Science": frozenset({"Scientists"}),
    "History": frozenset({"Historical Figures"}),
    "Politics": frozenset({"Politicians"}),
    "Music": frozenset({"Musicians"}),
    "Literature": frozenset({"Literature"}),
    "Mythology": frozenset({"Mythology"}),
    "Technology": frozenset({"Business Leaders", "Scientists"}),
}

# Legacy name used by older helpers / tests.
BROAD_QUESTION_CATEGORIES: frozenset[str] = STAGE_A_QUESTION_CATEGORIES

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
