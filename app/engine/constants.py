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
# Hard constraints from reliable L(C,Q): clear contradiction → drop (YES/NO).
DEFAULT_CONSTRAINT_AFFIRM_MAX = 0.20  # L <= this contradicts YES
DEFAULT_CONSTRAINT_NEGATE_MIN = 0.80  # L >= this contradicts NO
DEFAULT_CONSTRAINT_MIN_SAMPLES = 10
DEFAULT_CONSTRAINT_SOFT_FACTOR = 0.05  # PROBABLY* soft contradiction multiplier
DEFAULT_CONFIDENCE_HIGH = 0.85
DEFAULT_CONFIDENCE_SEPARATION = 0.6
DEFAULT_CONFIDENCE_MARGIN = 0.4
# Never force a "best available" guess below this unless the question budget is spent.
DEFAULT_MIN_GUESS_CONFIDENCE = 0.35
DEFAULT_MAX_QUESTIONS = 20
DEFAULT_IG_TIE_THRESHOLD = 0.001
DEFAULT_CONSECUTIVE_DONT_KNOW_CAP = 5
DEFAULT_NEW_QUESTION_MIN_SAMPLES = 5
DEFAULT_LEARNING_RATE = 0.07

# --- Natural gameplay question selection (Stage 1 → 2 → 3 → 4) ---
DEFAULT_CANDIDATE_MASS_FOCUS = 0.85
DEFAULT_DIVERSITY_TOP_K = 4
DEFAULT_DIVERSITY_MARGIN = 0.04
DEFAULT_CATEGORY_IG_BONUS = 0.12
DEFAULT_BROAD_QUESTION_BONUS = 0.15
DEFAULT_CATEGORY_REMAIN_MASS = 1e-6

# Early-game ranking: prefer natural identity / origin / domain questions.
# Low-value age questions stay locked for the first N turns (about 6–8).
DEFAULT_EARLY_PRIORITY_LOCK_QUESTIONS = 7
# After category detection, low-age questions need meaningful IG to surface.
DEFAULT_LOW_PRIORITY_AGE_MIN_IG = 0.12
# Low-age IG must be within this margin of the best non-low alternative.
DEFAULT_LOW_PRIORITY_AGE_IG_MARGIN = 0.08

# Ordered early priorities (highest first). First matching group wins.
# Akinator-like opening: alive/dead → India/country → athlete/domain.
EARLY_PRIORITY_KEYWORD_GROUPS: tuple[tuple[tuple[str, ...], float], ...] = (
    (("still alive", "alive today", "are they alive", "character still alive"), 0.48),
    (("real person", "made-up character", "made-up?", "fictional character"), 0.40),
    (("from india",), 0.38),
    (
        (
            "another country",
            "from your country",
            "from asia",
            "from europe",
            "from the americas",
            "from america",
            "from africa",
            "from australia",
            "from japan",
            "from the united states",
            "from the usa",
            "from the united kingdom",
            "from the uk",
        ),
        0.34,
    ),
    (("are they male", "girl or woman", "a man", "a woman", "character a man", "character a woman"), 0.28),
    (("are they human", "character human", "an animal"), 0.24),
    (("famous worldwide", "people still talk", "are they famous", "character famous"), 0.20),
    (
        (
            "sports player",
            "sportsperson",
            "an athlete",
            "from a movie",
            "from a tv show",
            "from tv",
            "a musician",
            "political leader",
            "a politician",
            "a scientist",
            "business leader",
            "business person",
            "from anime",
            "from a video game",
            "from a game",
            "from sports",
            "a superhero",
        ),
        0.14,
    ),
)

# Alive / dead status — must lead the opening when still unused.
ALIVE_STATUS_KEYWORDS: frozenset[str] = frozenset(
    {
        "still alive",
        "alive today",
        "are they alive",
        "character still alive",
        "is your character still alive?",
        "alive?",
    }
)

# Fine-grained age identity — unnatural early; keep in DB but demote hard.
LOW_PRIORITY_AGE_KEYWORDS: frozenset[str] = frozenset(
    {
        "baby",
        "toddler",
        "teenager",
        "elderly",
        "kid or teen",
        "a child",
        "are they a child",
        "are they children",
        "grown-up",
        "look old",
        "look young",
    }
)

# Exit Stage 1 (Identity) once a character category is clearly dominant.
DEFAULT_STAGE_A_EXIT_THRESHOLD = 0.35
DEFAULT_STAGE_A_EXIT_MARGIN = 0.10
# Enter Stage 2 (Origin) after identity; Stage 3 (Category) after origin mass.
DEFAULT_STAGE_ORIGIN_EXIT_THRESHOLD = 0.42
DEFAULT_STAGE_ORIGIN_EXIT_MARGIN = 0.08
# Enter Stage 4 (Subcategory) only with strong domain dominance.
DEFAULT_STAGE_C_ENTER_THRESHOLD = 0.62

# Backward-compatible aliases used by older call sites / tests.
DEFAULT_CATEGORY_CONFIDENCE_GATE = DEFAULT_STAGE_A_EXIT_THRESHOLD
DEFAULT_CATEGORY_PREFERENCE_THRESHOLD = DEFAULT_STAGE_A_EXIT_THRESHOLD
DEFAULT_CATEGORY_UNLOCK_THRESHOLD = DEFAULT_STAGE_A_EXIT_THRESHOLD

# Stage 1 — Identity only (real/fictional, gender, alive, human, famous).
# Keep phrases specific: bare "made-up" must NOT match "made-up guild".
STAGE_1_IDENTITY_KEYWORDS: frozenset[str] = frozenset(
    {
        "real person",
        "made-up character",
        "made-up?",
        "character made-up",
        "fictional character",
        "still alive",
        "alive today",
        "are they alive",
        "are they male",
        "girl or woman",
        "a man",
        "a woman",
        "are they human",
        "character human",
        "an animal",
        "famous worldwide",
        "people still talk",
        "are they famous",
        "character famous",
        "still famous",
        # Short probes used in tests / curated decks
        "alive?",
        "male?",
        "female?",
        "human?",
        "famous?",
        "real?",
        "is your character a man?",
        "is your character a woman?",
        "is your character human?",
        "is your character famous?",
        "is your character still alive?",
        "is your character a real person?",
        "is your character made-up?",
    }
)

# Major category questions (Level 2) — broad domain only, not subtypes.
MAJOR_CATEGORY_KEYWORDS: frozenset[str] = frozenset(
    {
        "sports player",
        "sportsperson",
        "an athlete",
        "your character an athlete",
        "from sports",
        "from a movie",
        "from a tv show",
        "from tv",
        "from anime",
        "from a cartoon",
        "from a video game",
        "from a game",
        "a musician",
        "political leader",
        "a politician",
        "a scientist",
        "business leader",
        "business person",
        "from mythology",
        "from a myth",
        "from a book",
        "a superhero",
    }
)

# Sport subtypes (Level 3) — never treat these as the major Sports category.
SPORT_SUBTYPE_KEYWORDS: frozenset[str] = frozenset(
    {
        "cricket",
        "football",
        "soccer",
        "basketball",
        "tennis",
        "baseball",
        "hockey",
        "golf",
        "boxing",
        "skating",
        "fencing",
        "martial arts",
        "swimming",
        "running",
        "gymnastics",
        "racing",
        "skiing",
        "rugby",
        "volleyball",
        "wrestling",
        "archery",
        "surfing",
        "cycling",
        "olympics",
        "olympic",
    }
)

# Ultra-specific sports details (Level 4) — after a subtype is established.
SPORT_SPECIFIC_KEYWORDS: frozenset[str] = frozenset(
    {
        "batsman",
        "batting",
        "bowler",
        "goalkeeper",
        "forward",
        "striker",
        "midfielder",
        "play for india",
        "play for argentina",
        "for india",
        "for argentina",
    }
)

# Stage 2 — Origin (place / era), before domain category.
# Place / nationality questions are mutually exclusive: ask at most one per game.
NATIONALITY_PLACE_KEYWORDS: frozenset[str] = frozenset(
    {
        "from india",
        "from japan",
        "from asia",
        "from europe",
        "from the americas",
        "from america",
        "from africa",
        "from australia",
        "from the united states",
        "from the usa",
        "from the united kingdom",
        "from the uk",
        "another country",
        "from your country",
    }
)

STAGE_2_ORIGIN_KEYWORDS: frozenset[str] = frozenset(
    set(NATIONALITY_PLACE_KEYWORDS)
    | {
        "known today",
        "modern times",
        "from long ago",
        "from history",
        "famous in the 1900s",
        "were they famous long ago",
        "from ancient times",
        "before cars",
    }
)

STAGE_2_ORIGIN_CATEGORIES: frozenset[str] = frozenset(
    {
        "Nationality",
        "Time period",
    }
)

# Stage A / 1 categories (metadata bucket; Stage 1 still keyword-gated).
# Nationality is Stage 2 (origin), not identity.
STAGE_A_QUESTION_CATEGORIES: frozenset[str] = frozenset(
    {
        "Personality",
        "Gender",
        "Age",
        "Fictional traits",
        "Physical appearance",
    }
)

# Stage 3 — Category / domain detection.
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

# Stage 4 — Subcategory / specific (and Stage-C tagged categories).
STAGE_C_QUESTION_CATEGORIES: frozenset[str] = frozenset(
    {
        "Profession",
        "Awards",
        "Relationships",
        "Time period",
    }
)

# Keywords that push an otherwise domain question into Stage 4 (subcategory).
STAGE_C_KEYWORDS: frozenset[str] = frozenset(
    set(SPORT_SUBTYPE_KEYWORDS)
    | set(SPORT_SPECIFIC_KEYWORDS)
    | {
        "chef",
        "architect",
        "lawyer",
        "doctor",
        "teacher",
        "pilot",
        "police",
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
        "pirate",
        "magic",
        "k-pop",
        "robot anime",
        "love story anime",
        "sports anime",
        "another-world",
        "queen",
        "princess",
        "vampire",
        "ice powers",
        "fire powers",
        "lightning powers",
        "super speed",
        "filler",
        "love triangle",
        "dj",
        "guild",
        "catchphrase",
        "franchise",
        "sword",
        "fight crime",
        "famous for",
    }
)

# Hard niche / franchise / occupation — never ask early (Stage 1–3).
FORBIDDEN_EARLY_KEYWORDS: frozenset[str] = frozenset(
    set(SPORT_SUBTYPE_KEYWORDS)
    | set(SPORT_SPECIFIC_KEYWORDS)
    | {
        "chef",
        "architect",
        "dj",
        "queen",
        "princess",
        "baby",
        "toddler",
        "teenager",
        "elderly",
        "vampire",
        "ice powers",
        "fire powers",
        "lightning powers",
        "filler",
        "love triangle",
        "made-up guild",
        "guild",
        "catchphrase",
        "marvel",
        "dc comic",
        "jedi",
        "k-pop",
        "franchise",
        "ninja",
        "samurai",
        "wizard",
        "pirate",
        "knight",
        "cyborg",
        "detective",
        "olympic",
        "sword",
        "famous for",
    }
)

# Profession-like words that must never appear before category detection.
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
        "dj",
        "queen",
        "princess",
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

# Niche Stage-4 topics that require a matching dominant fictional/domain category.
NICHE_TOPIC_REQUIRED_CATEGORIES: dict[str, frozenset[str]] = {
    "guild": frozenset({"Anime", "Gaming"}),
    "ninja": frozenset({"Anime"}),
    "samurai": frozenset({"Anime"}),
    "ice powers": frozenset({"Anime", "Movies", "Cartoons", "Gaming", "Mythology"}),
    "fire powers": frozenset({"Anime", "Movies", "Cartoons", "Gaming", "Mythology"}),
    "lightning powers": frozenset({"Anime", "Movies", "Cartoons", "Gaming", "Mythology"}),
    "vampire": frozenset({"Movies", "TV Shows", "Literature", "Mythology"}),
    "jedi": frozenset({"Movies", "Gaming"}),
    "marvel": frozenset({"Movies", "TV Shows", "Gaming"}),
    "dc comic": frozenset({"Movies", "TV Shows", "Gaming"}),
    "filler": frozenset({"Anime"}),
    "love triangle": frozenset({"Anime", "Movies", "TV Shows", "Literature"}),
    "catchphrase": frozenset({"Anime", "Movies", "TV Shows", "Cartoons", "Gaming"}),
    **{sport: frozenset({"Sports"}) for sport in SPORT_SUBTYPE_KEYWORDS},
    **{detail: frozenset({"Sports"}) for detail in SPORT_SPECIFIC_KEYWORDS},
    "sword": frozenset({"Anime", "Movies", "Gaming", "Mythology", "Literature"}),
}

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

# Penalty applied when a Stage-4 / niche question is scored (keeps flow natural).
DEFAULT_SPECIFICITY_PENALTY = 0.18
DEFAULT_NEAR_DUPLICATE_PENALTY = 0.25
