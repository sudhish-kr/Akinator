"""Curated production Question Database v2 (~250 Akinator-style questions).

Hierarchy levels:
  1 Identity · 2 Category · 3 Subcategory · 4 Specific · 5 Rare

Phrasing follows Akinator-style UX: "Is your character…?" / "Does your character…?"
Does not touch the Bayesian engine or learning code.
"""

from __future__ import annotations

from typing import Any

from akinator_style_rewrites import to_akinator_style

DATASET_ID = "v2"
QUESTION_PHASE = 2
TARGET_COUNT = 250
MIN_COUNT = 220
MAX_COUNT = 300
MAX_WORDS = 10

# Level → engine question.category buckets (matches Stage A/B/C in constants).
LEVEL_NAMES = {
    1: "Identity",
    2: "Category",
    3: "Subcategory",
    4: "Specific",
    5: "Rare",
}

# Classic questions get a slight IG boost after rewrite.
_CLASSIC_BOOST = {
    "Is your character a real person?",
    "Is your character made-up?",
    "Is your character still alive?",
    "Is your character a man?",
    "Is your character a woman?",
    "Is your character human?",
    "Is your character famous?",
    "Is your character an athlete?",
    "Is your character from a movie?",
    "Is your character from anime?",
    "Is your character from a cartoon?",
    "Is your character from a game?",
    "Is your character from TV?",
    "Is your character a superhero?",
    "Is your character a scientist?",
    "Is your character a musician?",
    "Is your character a politician?",
    "Does your character play cricket?",
    "Does your character play football?",
    "Is your character a ninja?",
}

# Source rows still use pre-rewrite text for stable editing; build() rewrites.
# (text, category, hierarchy_level, initial_ig)
_QUESTIONS: list[tuple[str, str, int, float]] = [
    # --- Level 1 · Identity ---
    ("Is this a real person?", "Personality", 1, 0.55),
    ("Is this a made-up character?", "Fictional traits", 1, 0.55),
    ("Is this person still alive?", "Age", 1, 0.48),
    ("Are they male?", "Gender", 1, 0.42),
    ("Are they a girl or woman?", "Gender", 1, 0.42),
    ("Are they a kid or teen?", "Age", 1, 0.42),
    ("Are they a grown-up?", "Age", 1, 0.40),
    ("Are they human?", "Personality", 1, 0.45),
    ("Are they an animal?", "Personality", 1, 0.40),
    ("Do they wear a costume?", "Physical appearance", 4, 0.38),
    ("Do they wear a mask?", "Physical appearance", 4, 0.36),
    ("Do they have long hair?", "Physical appearance", 5, 0.28),
    ("Do they have short hair?", "Physical appearance", 5, 0.28),
    ("Do they have dark hair?", "Physical appearance", 5, 0.28),
    ("Do they have light hair?", "Physical appearance", 5, 0.28),
    ("Do they wear glasses?", "Physical appearance", 5, 0.30),
    ("Are they tall?", "Physical appearance", 5, 0.26),
    ("Are they known by one name?", "Personality", 5, 0.30),
    ("Are they famous worldwide?", "Personality", 1, 0.42),
    # Origin (engine Stage 2) — after alive/dead, before athlete/domain.
    ("Are they from India?", "Nationality", 2, 0.42),
    ("Are they from Japan?", "Nationality", 2, 0.32),
    ("Are they from the United States?", "Nationality", 2, 0.34),
    ("Are they from the United Kingdom?", "Nationality", 2, 0.32),
    ("Are they from Asia?", "Nationality", 2, 0.38),
    ("Are they from Europe?", "Nationality", 2, 0.38),
    ("Are they from the Americas?", "Nationality", 2, 0.38),
    ("Are they from Africa?", "Nationality", 2, 0.32),
    ("Are they from Australia?", "Nationality", 2, 0.28),
    ("Are they kind and helpful?", "Personality", 5, 0.28),
    ("Are they mostly serious?", "Personality", 5, 0.26),
    ("Are they mostly funny?", "Personality", 5, 0.28),
    ("Are they brave?", "Personality", 5, 0.30),
    ("Are they very smart?", "Personality", 4, 0.32),
    ("Are they strong?", "Physical appearance", 5, 0.28),
    ("Do they have a special outfit?", "Physical appearance", 4, 0.34),
    ("Do they look young?", "Age", 5, 0.30),
    ("Do they look old?", "Age", 5, 0.28),
    ("Are they a hero?", "Fictional traits", 2, 0.40),
    ("Are they a villain?", "Fictional traits", 2, 0.38),
    ("Is this about magic?", "Fictional traits", 2, 0.40),
    ("Is this sci-fi?", "Fictional traits", 2, 0.38),
    ("Can they talk like a person?", "Personality", 5, 0.30),
    ("Do they live in a city?", "Personality", 5, 0.24),
    ("Do they live in nature?", "Personality", 5, 0.24),
    ("Are they part of a big story?", "Personality", 5, 0.26),
    ("Do people still talk about them?", "Personality", 1, 0.34),
    ("Were they famous long ago?", "Age", 2, 0.34),
    ("Do they have a best friend?", "Personality", 5, 0.26),
    ("Do people dress like them?", "Physical appearance", 5, 0.24),
    ("Do they smile a lot?", "Personality", 5, 0.24),
    # --- Origin (engine Stage 2; kept before domain categories) ---
    ("Are they from another country?", "Nationality", 2, 0.40),
    ("Are they from modern times?", "Time period", 2, 0.40),
    ("Are they from history?", "History", 2, 0.42),
    # --- Level 2 · Category (domain) ---
    ("Is this a sports player?", "Sports", 2, 0.58),
    ("Is this from a movie?", "Movies", 2, 0.58),
    ("Is this from a TV show?", "TV", 2, 0.54),
    ("Is this from anime?", "Anime", 2, 0.56),
    ("Is this from a cartoon?", "Cartoons", 2, 0.56),
    ("Is this from a video game?", "Gaming", 2, 0.55),
    ("Is this a scientist?", "Science", 2, 0.55),
    ("Is this a musician?", "Music", 2, 0.56),
    ("Is this a writer?", "Literature", 2, 0.52),
    ("Is this a political leader?", "Politics", 2, 0.55),
    ("Is this a business leader?", "Technology", 2, 0.50),
    ("Is this from an old legend?", "Mythology", 2, 0.57),
    ("Is this from long-ago history?", "History", 2, 0.50),
    ("Do they play team sports?", "Sports", 2, 0.42),
    ("Do they play alone sports?", "Sports", 2, 0.36),
    ("Are they in action movies?", "Movies", 2, 0.40),
    ("Are they in funny movies?", "Movies", 2, 0.38),
    ("Are they in kids movies?", "Movies", 2, 0.36),
    ("Are they on a kids TV show?", "TV", 2, 0.38),
    ("Are they on a funny TV show?", "TV", 2, 0.36),
    ("Are they on a serious TV show?", "TV", 2, 0.34),
    ("Are they from kids anime?", "Anime", 2, 0.36),
    ("Are they from action anime?", "Anime", 2, 0.38),
    ("Are they from a funny cartoon?", "Cartoons", 2, 0.36),
    ("Are they from a school cartoon?", "Cartoons", 2, 0.32),
    ("Are they from an adventure game?", "Gaming", 2, 0.36),
    ("Are they from a fighting game?", "Gaming", 2, 0.34),
    ("Do they study nature?", "Science", 2, 0.34),
    ("Do they study stars?", "Science", 2, 0.34),
    ("Do they study numbers?", "Science", 2, 0.32),
    ("Do they sing songs?", "Music", 2, 0.42),
    ("Do they play an instrument?", "Music", 2, 0.40),
    ("Do they write books?", "Literature", 2, 0.40),
    ("Do they write poems?", "Literature", 2, 0.30),
    ("Do they lead a country?", "Politics", 2, 0.42),
    ("Do they run a big company?", "Technology", 2, 0.40),
    ("Are they from Greek myths?", "Mythology", 2, 0.34),
    ("Are they from Norse myths?", "Mythology", 2, 0.30),
    ("Are they from Egyptian myths?", "Mythology", 2, 0.28),
    ("Did they live before cars?", "History", 2, 0.34),
    ("Did they live with kings?", "History", 2, 0.32),
    ("Are they from space stories?", "Movies", 2, 0.34),
    ("Are they from animal stories?", "Cartoons", 2, 0.34),
    ("Are they from robot stories?", "Gaming", 2, 0.30),
    ("Is this about sports games?", "Sports", 2, 0.36),
    ("Is this about school life?", "Anime", 2, 0.32),
    ("Is this about music shows?", "Music", 2, 0.30),
    ("Is this about science work?", "Science", 2, 0.34),
    ("Is this about old wars?", "History", 2, 0.34),
    ("Is this about kings and queens?", "History", 2, 0.32),
    ("Is this about computers?", "Technology", 2, 0.34),
    ("Is this about phones or apps?", "Technology", 2, 0.30),
    ("Is this a superhero?", "Movies", 2, 0.45),
    ("Is this about space?", "Science", 2, 0.40),
    ("Are they linked to war?", "History", 2, 0.40),
    ("Is this from long ago?", "History", 2, 0.48),
    ("Are they known today?", "Time period", 3, 0.40),
    ("Were they famous in the 1900s?", "Time period", 3, 0.38),
    ("Have they won big awards?", "Awards", 4, 0.42),
    # --- Level 3 · Subcategory ---
    ("Do they play with a ball?", "Sports", 3, 0.36),
    ("Do they race or run fast?", "Sports", 3, 0.32),
    ("Do they swim in contests?", "Sports", 3, 0.28),
    ("Do they play on ice?", "Sports", 3, 0.26),
    ("Do they fight in a ring?", "Sports", 3, 0.28),
    ("Are they a movie hero?", "Movies", 3, 0.36),
    ("Are they a movie villain?", "Movies", 3, 0.34),
    ("Are they in cartoon movies?", "Movies", 3, 0.34),
    ("Are they in scary movies?", "Movies", 3, 0.30),
    ("Are they in love story movies?", "Movies", 3, 0.28),
    ("Are they in a police TV show?", "TV", 3, 0.30),
    ("Are they in a hospital TV show?", "TV", 3, 0.28),
    ("Are they in a family TV show?", "TV", 3, 0.32),
    ("Are they in a cooking TV show?", "TV", 3, 0.24),
    ("Do they train hard in anime?", "Anime", 3, 0.34),
    ("Do they go to school in anime?", "Anime", 3, 0.32),
    ("Do they have anime powers?", "Anime", 3, 0.36),
    ("Are they a talking cartoon animal?", "Cartoons", 3, 0.36),
    ("Are they a cartoon kid?", "Cartoons", 3, 0.32),
    ("Are they a cartoon adult?", "Cartoons", 3, 0.28),
    ("Do they explore game worlds?", "Gaming", 3, 0.34),
    ("Do they race in games?", "Gaming", 3, 0.28),
    ("Do they solve puzzles in games?", "Gaming", 3, 0.28),
    ("Do they build things in games?", "Gaming", 3, 0.26),
    ("Do they study living things?", "Science", 3, 0.32),
    ("Do they invent new things?", "Science", 3, 0.34),
    ("Do they work with computers?", "Science", 3, 0.30),
    ("Do they sing pop songs?", "Music", 3, 0.34),
    ("Do they sing rock songs?", "Music", 3, 0.30),
    ("Do they make classical music?", "Music", 3, 0.28),
    ("Do they write kids books?", "Literature", 3, 0.30),
    ("Do they write adventure books?", "Literature", 3, 0.30),
    ("Do they write mystery books?", "Literature", 3, 0.28),
    ("Are they a president?", "Politics", 3, 0.34),
    ("Are they a prime minister?", "Politics", 3, 0.32),
    ("Are they a king or queen?", "Politics", 3, 0.32),
    ("Did they start a tech company?", "Technology", 3, 0.34),
    ("Did they make cars or rockets?", "Technology", 3, 0.30),
    ("Are they a sky god?", "Mythology", 3, 0.28),
    ("Are they a sea god?", "Mythology", 3, 0.26),
    ("Are they a trickster in myths?", "Mythology", 3, 0.26),
    ("Did they lead armies long ago?", "History", 3, 0.34),
    ("Did they explore new lands?", "History", 3, 0.30),
    ("Did they help change laws?", "History", 3, 0.30),
    ("Are they on a famous team?", "Relationships", 3, 0.36),
    ("Do they have a famous rival?", "Relationships", 3, 0.32),
    ("Do they have a famous mentor?", "Relationships", 3, 0.28),
    ("Are they known for a special move?", "Sports", 3, 0.30),
    ("Are they known for a catchphrase?", "Personality", 3, 0.28),
    ("Do they wear team colors?", "Sports", 3, 0.28),
    ("Do they wear a cape?", "Movies", 3, 0.30),
    ("Do they fly or jump very high?", "Fictional traits", 3, 0.32),
    ("Do they use tools or gadgets?", "Technology", 3, 0.30),
    ("Do they work in a lab?", "Science", 3, 0.32),
    ("Do they perform on a stage?", "Music", 3, 0.34),
    ("Do they appear in comics too?", "Movies", 3, 0.30),
    ("Are they from Hindi movies?", "Movies", 3, 0.40),
    ("Are they from Telugu movies?", "Movies", 3, 0.38),
    ("Are they from Tamil movies?", "Movies", 3, 0.38),
    ("Are they from Malayalam movies?", "Movies", 3, 0.36),
    ("Are they from Kannada movies?", "Movies", 3, 0.36),
    ("Are they from Bengali movies?", "Movies", 3, 0.34),
    ("Are they from Marathi movies?", "Movies", 3, 0.32),
    ("Are they from Punjabi movies?", "Movies", 3, 0.32),
    ("Are they from Gujarati movies?", "Movies", 3, 0.28),
    ("Are they from Bhojpuri movies?", "Movies", 3, 0.28),
    ("Are they from Assamese movies?", "Movies", 3, 0.24),
    ("Are they from Odia movies?", "Movies", 3, 0.24),
    ("Are they a film director?", "Profession", 3, 0.36),
    ("Are they a freedom fighter?", "History", 3, 0.38),
    ("Are they linked to Maharashtra?", "Politics", 4, 0.30),
    ("Are they linked to Uttar Pradesh?", "Politics", 4, 0.30),
    ("Are they linked to West Bengal?", "Politics", 4, 0.28),
    ("Are they linked to Tamil Nadu?", "Politics", 4, 0.28),
    ("Are they linked to Karnataka?", "Politics", 4, 0.28),
    ("Are they linked to Kerala?", "Politics", 4, 0.26),
    ("Are they linked to Gujarat?", "Politics", 4, 0.28),
    ("Are they linked to Bihar?", "Politics", 4, 0.26),
    ("Are they linked to Andhra or Telangana?", "Politics", 4, 0.28),
    ("Are they linked to Punjab?", "Politics", 4, 0.26),
    ("Are they linked to Delhi?", "Politics", 4, 0.26),
    # --- Level 4 · Specific (sport subtypes are Level 3) ---
    ("Are they famous for cricket?", "Sports", 3, 0.42),
    ("Do they keep wickets in cricket?", "Sports", 4, 0.34),
    ("Are they mainly an opening batter?", "Sports", 4, 0.32),
    ("Are they mainly a bowler?", "Sports", 4, 0.32),
    ("Did they debut in cricket before 2000?", "Sports", 4, 0.32),
    ("Are they famous for football?", "Sports", 3, 0.44),
    ("Are they famous for basketball?", "Sports", 3, 0.40),
    ("Are they famous for tennis?", "Sports", 3, 0.36),
    ("Are they famous for baseball?", "Sports", 3, 0.34),
    ("Are they famous for boxing?", "Sports", 3, 0.34),
    ("Are they famous for badminton?", "Sports", 3, 0.32),
    ("Are they famous for golf?", "Sports", 3, 0.30),
    ("Are they famous for hockey?", "Sports", 3, 0.30),
    ("Are they famous for wrestling?", "Sports", 3, 0.30),
    ("Are they famous for car racing?", "Sports", 3, 0.30),
    ("Are they from the Middle East?", "Nationality", 2, 0.30),
    ("Are they an Olympic winner?", "Awards", 5, 0.32),
    ("Are they a singer?", "Profession", 4, 0.36),
    ("Are they an actor?", "Profession", 4, 0.36),
    ("Are they an actress?", "Profession", 4, 0.34),
    ("Did they win a Nobel science prize?", "Awards", 5, 0.30),
    ("Did they win a big music prize?", "Awards", 5, 0.30),
    ("Did they win a big movie prize?", "Awards", 5, 0.30),
    ("Are they a ninja or samurai?", "Anime", 5, 0.32),
    ("Are they a space traveler?", "Movies", 5, 0.30),
    ("Are they a pirate?", "Movies", 5, 0.26),
    ("Are they a detective?", "TV", 5, 0.28),
    ("Are they a doctor in the story?", "TV", 5, 0.26),
    ("Are they a teacher in the story?", "Anime", 5, 0.24),
    ("Are they a student in the story?", "Anime", 5, 0.28),
    ("Are they a robot or cyborg?", "Gaming", 5, 0.28),
    ("Are they a wizard?", "Fictional traits", 5, 0.30),
    ("Are they a princess?", "Fictional traits", 5, 0.28),
    ("Are they a knight?", "Fictional traits", 5, 0.26),
    ("Do they play guitar?", "Music", 4, 0.28),
    ("Do they play piano?", "Music", 4, 0.28),
    ("Do they play drums?", "Music", 4, 0.24),
    ("Do they write for kids?", "Literature", 4, 0.26),
    ("Do they write fantasy stories?", "Literature", 4, 0.28),
    ("Did they lead during a war?", "History", 4, 0.30),
    ("Did they invent something famous?", "Science", 4, 0.32),
    ("Did they discover something new?", "Science", 4, 0.30),
    ("Are they linked to phones?", "Technology", 4, 0.26),
    ("Are they linked to electric cars?", "Technology", 4, 0.24),
    ("Are they linked to online shops?", "Technology", 4, 0.24),
    ("Are they from a book series?", "Literature", 4, 0.28),
    ("Are they from a movie series?", "Movies", 4, 0.30),
    ("Are they from a game series?", "Gaming", 4, 0.28),
    ("Do they wear a sports jersey?", "Sports", 4, 0.28),
    ("Do they wear a school uniform?", "Anime", 4, 0.26),
    ("Do they fight with a sword?", "Anime", 4, 0.28),
    ("Do they use a shield?", "Mythology", 4, 0.24),
    ("Do they throw lightning?", "Mythology", 4, 0.24),
    ("Do they control the sea?", "Mythology", 4, 0.24),
    ("Are they known for speed?", "Sports", 4, 0.28),
    ("Are they known for goals scored?", "Sports", 4, 0.30),
    ("Are they known for home runs?", "Sports", 4, 0.24),
    ("Are they known for slam dunks?", "Sports", 4, 0.24),
    ("Are they known for serve and volley?", "Sports", 4, 0.22),
    ("Are they from the 2000s?", "Time period", 4, 0.26),
    ("Are they from the 1800s?", "Time period", 4, 0.26),
    ("Are they mainly from ancient times?", "Time period", 4, 0.28),
    # --- Level 5 · Rare ---
    ("Do they have blue skin?", "Physical appearance", 5, 0.18),
    ("Do they have green skin?", "Physical appearance", 5, 0.16),
    ("Do they have one eye?", "Physical appearance", 5, 0.16),
    ("Do they have wings?", "Fictional traits", 5, 0.22),
    ("Do they have a tail?", "Fictional traits", 5, 0.20),
    ("Are they a talking animal?", "Cartoons", 5, 0.28),
    ("Are they made of metal?", "Gaming", 5, 0.22),
    ("Are they invisible sometimes?", "Fictional traits", 5, 0.20),
    ("Can they shrink or grow?", "Fictional traits", 5, 0.18),
    ("Can they turn into animals?", "Fictional traits", 5, 0.20),
    ("Can they stop time?", "Fictional traits", 5, 0.18),
    ("Can they read minds?", "Fictional traits", 5, 0.18),
    ("Do they live underwater?", "Fictional traits", 5, 0.20),
    ("Do they live in space?", "Movies", 5, 0.22),
    ("Do they live underground?", "Gaming", 5, 0.18),
    ("Are they a ghost?", "Fictional traits", 5, 0.20),
    ("Are they a vampire?", "Movies", 5, 0.18),
    ("Are they a dragon?", "Mythology", 5, 0.20),
    ("Are they a giant?", "Mythology", 5, 0.18),
    ("Are they tiny like a toy?", "Cartoons", 5, 0.18),
    ("Do they have four arms?", "Mythology", 5, 0.16),
    ("Do they breathe fire?", "Mythology", 5, 0.18),
    ("Do they freeze things?", "Fictional traits", 5, 0.18),
    ("Do they shoot lasers?", "Movies", 5, 0.18),
    ("Do they ride a flying broom?", "Fictional traits", 5, 0.16),
    ("Do they ride a flying carpet?", "Mythology", 5, 0.14),
    ("Are they a clone or twin?", "Movies", 5, 0.16),
    ("Are they from the future?", "Time period", 5, 0.20),
    ("Are they from another planet?", "Movies", 5, 0.22),
    ("Are they from a dream world?", "Anime", 5, 0.18),
    ("Do they change shape?", "Fictional traits", 5, 0.20),
    ("Do they have no shadow?", "Fictional traits", 5, 0.14),
    ("Do they glow in the dark?", "Gaming", 5, 0.14),
    ("Are they stuck as a kid forever?", "Cartoons", 5, 0.18),
    ("Are they older than countries?", "Mythology", 5, 0.18),
]


def _word_count(text: str) -> int:
    return len(text.replace("?", " ").split())


def build_v2_questions() -> list[dict[str, Any]]:
    """Return deduplicated v2 question dicts ready for seed / DB sync."""
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for text, category, level, ig in _QUESTIONS:
        rewritten = to_akinator_style(text)
        key = rewritten.casefold().strip()
        if key in seen:
            continue
        if _word_count(rewritten) > MAX_WORDS:
            raise ValueError(f"Question exceeds {MAX_WORDS} words: {rewritten!r} (from {text!r})")
        if level not in LEVEL_NAMES:
            raise ValueError(f"Invalid hierarchy level {level} for {text!r}")
        seen.add(key)
        score = ig
        if rewritten in _CLASSIC_BOOST:
            score = min(0.65, score + 0.06)
        out.append(
            {
                "text": rewritten.strip(),
                "category": category,
                "hierarchy_level": level,
                "hierarchy_name": LEVEL_NAMES[level],
                "dataset": DATASET_ID,
                "is_active": True,
                "avg_information_gain": round(max(0.12, min(0.65, score)), 2),
                "times_asked": 0,
                "legacy_text": text.strip(),
            }
        )

    if not (MIN_COUNT <= len(out) <= MAX_COUNT):
        raise RuntimeError(
            f"v2 catalog has {len(out)} questions; expected {MIN_COUNT}-{MAX_COUNT}"
        )
    return out


def v2_question_texts() -> set[str]:
    return {q["text"] for q in build_v2_questions()}


def questions_by_level() -> dict[int, list[dict[str, Any]]]:
    grouped: dict[int, list[dict[str, Any]]] = {level: [] for level in LEVEL_NAMES}
    for q in build_v2_questions():
        grouped[int(q["hierarchy_level"])].append(q)
    return grouped
