"""Deterministic character↔question likelihood priors (no randomness).

Maps character categories to question categories with curated affinities.
Category-specific questions are linked only where the prior is meaningful
(aligned or clearly anti-aligned); ambiguous cross-links are omitted so the
engine default (0.5) remains for unknown pairs.
"""

from __future__ import annotations

from typing import Iterable

# Character categories (must match knowledge_phase1_data.CATEGORIES)
CHAR_CATEGORIES = [
    "Movies",
    "TV Shows",
    "Anime",
    "Cartoons",
    "Sports",
    "Scientists",
    "Historical Figures",
    "Politicians",
    "Musicians",
    "Business Leaders",
    "Gaming",
    "Mythology",
    "Literature",
]

FICTIONAL_MEDIA = frozenset(
    {"Movies", "TV Shows", "Anime", "Cartoons", "Gaming", "Mythology", "Literature"}
)
REAL_WORLD = frozenset(
    {
        "Sports",
        "Scientists",
        "Historical Figures",
        "Politicians",
        "Musicians",
        "Business Leaders",
    }
)

# Question categories that apply to every character type (always linked).
UNIVERSAL_QUESTION_CATEGORIES = frozenset(
    {
        "Physical appearance",
        "Gender",
        "Age",
        "Nationality",
        "Profession",
        "Personality",
        "Relationships",
        "Awards",
        "Time period",
    }
)

# Domain question category → primary character category alignment.
PRIMARY_ALIGNMENT: dict[str, str] = {
    "Movies": "Movies",
    "TV": "TV Shows",
    "Anime": "Anime",
    "Cartoons": "Cartoons",
    "Gaming": "Gaming",
    "Sports": "Sports",
    "Science": "Scientists",
    "History": "Historical Figures",
    "Politics": "Politicians",
    "Music": "Musicians",
    "Literature": "Literature",
    "Mythology": "Mythology",
    "Technology": "Business Leaders",
    "Fictional traits": "Movies",  # refined per char cat below
}

# Base P(yes | character_category, question_category). Curated, not random.
# Values near 0.5 are treated as non-links for domain questions.
_BASE: dict[str, dict[str, float]] = {
    "Movies": {
        "Movies": 0.92,
        "TV": 0.28,
        "Anime": 0.08,
        "Cartoons": 0.18,
        "Gaming": 0.12,
        "Sports": 0.08,
        "Science": 0.12,
        "History": 0.18,
        "Politics": 0.08,
        "Music": 0.15,
        "Literature": 0.22,
        "Mythology": 0.2,
        "Technology": 0.12,
        "Fictional traits": 0.88,
        "Physical appearance": 0.55,
        "Gender": 0.5,
        "Age": 0.45,
        "Nationality": 0.5,
        "Profession": 0.35,
        "Personality": 0.55,
        "Relationships": 0.5,
        "Awards": 0.55,
        "Time period": 0.55,
    },
    "TV Shows": {
        "Movies": 0.32,
        "TV": 0.93,
        "Anime": 0.1,
        "Cartoons": 0.22,
        "Gaming": 0.1,
        "Sports": 0.08,
        "Science": 0.12,
        "History": 0.15,
        "Politics": 0.1,
        "Music": 0.15,
        "Literature": 0.18,
        "Mythology": 0.15,
        "Technology": 0.12,
        "Fictional traits": 0.88,
        "Physical appearance": 0.55,
        "Gender": 0.5,
        "Age": 0.48,
        "Nationality": 0.5,
        "Profession": 0.35,
        "Personality": 0.55,
        "Relationships": 0.52,
        "Awards": 0.5,
        "Time period": 0.58,
    },
    "Anime": {
        "Movies": 0.35,
        "TV": 0.4,
        "Anime": 0.96,
        "Cartoons": 0.25,
        "Gaming": 0.2,
        "Sports": 0.08,
        "Science": 0.12,
        "History": 0.12,
        "Politics": 0.06,
        "Music": 0.15,
        "Literature": 0.15,
        "Mythology": 0.35,
        "Technology": 0.12,
        "Fictional traits": 0.94,
        "Physical appearance": 0.55,
        "Gender": 0.5,
        "Age": 0.55,
        "Nationality": 0.5,  # geography refined per question text (Japan≠India)
        "Profession": 0.3,
        "Personality": 0.55,
        "Relationships": 0.55,
        "Awards": 0.35,
        "Time period": 0.5,
    },
    "Cartoons": {
        "Movies": 0.3,
        "TV": 0.7,
        "Anime": 0.12,
        "Cartoons": 0.95,
        "Gaming": 0.15,
        "Sports": 0.08,
        "Science": 0.1,
        "History": 0.1,
        "Politics": 0.05,
        "Music": 0.12,
        "Literature": 0.12,
        "Mythology": 0.2,
        "Technology": 0.1,
        "Fictional traits": 0.94,
        "Physical appearance": 0.6,
        "Gender": 0.5,
        "Age": 0.55,
        "Nationality": 0.55,
        "Profession": 0.25,
        "Personality": 0.6,
        "Relationships": 0.55,
        "Awards": 0.3,
        "Time period": 0.5,
    },
    "Sports": {
        "Movies": 0.12,
        "TV": 0.15,
        "Anime": 0.03,
        "Cartoons": 0.03,
        "Gaming": 0.05,
        "Sports": 0.96,
        "Science": 0.08,
        "History": 0.15,
        "Politics": 0.08,
        "Music": 0.1,
        "Literature": 0.08,
        "Mythology": 0.04,
        "Technology": 0.1,
        "Fictional traits": 0.06,
        "Physical appearance": 0.65,
        "Gender": 0.5,
        "Age": 0.55,
        "Nationality": 0.55,
        "Profession": 0.75,
        "Personality": 0.5,
        "Relationships": 0.45,
        "Awards": 0.78,
        "Time period": 0.6,
    },
    "Scientists": {
        "Movies": 0.12,
        "TV": 0.1,
        "Anime": 0.03,
        "Cartoons": 0.03,
        "Gaming": 0.04,
        "Sports": 0.06,
        "Science": 0.95,
        "History": 0.35,
        "Politics": 0.12,
        "Music": 0.1,
        "Literature": 0.2,
        "Mythology": 0.05,
        "Technology": 0.7,
        "Fictional traits": 0.06,
        "Physical appearance": 0.45,
        "Gender": 0.5,
        "Age": 0.4,
        "Nationality": 0.55,
        "Profession": 0.9,
        "Personality": 0.5,
        "Relationships": 0.4,
        "Awards": 0.7,
        "Time period": 0.55,
    },
    "Historical Figures": {
        "Movies": 0.1,
        "TV": 0.08,
        "Anime": 0.03,
        "Cartoons": 0.03,
        "Gaming": 0.04,
        "Sports": 0.1,
        "Science": 0.25,
        "History": 0.94,
        "Politics": 0.55,
        "Music": 0.15,
        "Literature": 0.25,
        "Mythology": 0.2,
        "Technology": 0.12,
        "Fictional traits": 0.08,
        "Physical appearance": 0.45,
        "Gender": 0.5,
        "Age": 0.15,  # usually not alive
        "Nationality": 0.55,
        "Profession": 0.7,
        "Personality": 0.5,
        "Relationships": 0.45,
        "Awards": 0.35,
        "Time period": 0.85,
    },
    "Politicians": {
        "Movies": 0.1,
        "TV": 0.15,
        "Anime": 0.03,
        "Cartoons": 0.03,
        "Gaming": 0.04,
        "Sports": 0.08,
        "Science": 0.12,
        "History": 0.55,
        "Politics": 0.95,
        "Music": 0.1,
        "Literature": 0.15,
        "Mythology": 0.05,
        "Technology": 0.2,
        "Fictional traits": 0.05,
        "Physical appearance": 0.45,
        "Gender": 0.5,
        "Age": 0.6,
        "Nationality": 0.6,
        "Profession": 0.88,
        "Personality": 0.55,
        "Relationships": 0.5,
        "Awards": 0.45,
        "Time period": 0.65,
    },
    "Musicians": {
        "Movies": 0.18,
        "TV": 0.15,
        "Anime": 0.05,
        "Cartoons": 0.04,
        "Gaming": 0.05,
        "Sports": 0.08,
        "Science": 0.08,
        "History": 0.2,
        "Politics": 0.1,
        "Music": 0.96,
        "Literature": 0.2,
        "Mythology": 0.06,
        "Technology": 0.15,
        "Fictional traits": 0.12,
        "Physical appearance": 0.55,
        "Gender": 0.5,
        "Age": 0.55,
        "Nationality": 0.55,
        "Profession": 0.88,
        "Personality": 0.55,
        "Relationships": 0.5,
        "Awards": 0.72,
        "Time period": 0.6,
    },
    "Business Leaders": {
        "Movies": 0.1,
        "TV": 0.1,
        "Anime": 0.03,
        "Cartoons": 0.03,
        "Gaming": 0.08,
        "Sports": 0.08,
        "Science": 0.35,
        "History": 0.2,
        "Politics": 0.25,
        "Music": 0.1,
        "Literature": 0.12,
        "Mythology": 0.04,
        "Technology": 0.92,
        "Fictional traits": 0.05,
        "Physical appearance": 0.45,
        "Gender": 0.5,
        "Age": 0.65,
        "Nationality": 0.55,
        "Profession": 0.9,
        "Personality": 0.55,
        "Relationships": 0.45,
        "Awards": 0.55,
        "Time period": 0.7,
    },
    "Gaming": {
        "Movies": 0.3,
        "TV": 0.15,
        "Anime": 0.2,
        "Cartoons": 0.18,
        "Gaming": 0.96,
        "Sports": 0.1,
        "Science": 0.12,
        "History": 0.12,
        "Politics": 0.06,
        "Music": 0.12,
        "Literature": 0.12,
        "Mythology": 0.25,
        "Technology": 0.35,
        "Fictional traits": 0.92,
        "Physical appearance": 0.6,
        "Gender": 0.5,
        "Age": 0.5,
        "Nationality": 0.5,
        "Profession": 0.3,
        "Personality": 0.55,
        "Relationships": 0.5,
        "Awards": 0.35,
        "Time period": 0.55,
    },
    "Mythology": {
        "Movies": 0.25,
        "TV": 0.15,
        "Anime": 0.2,
        "Cartoons": 0.15,
        "Gaming": 0.2,
        "Sports": 0.05,
        "Science": 0.08,
        "History": 0.55,
        "Politics": 0.15,
        "Music": 0.1,
        "Literature": 0.35,
        "Mythology": 0.96,
        "Technology": 0.05,
        "Fictional traits": 0.9,
        "Physical appearance": 0.55,
        "Gender": 0.5,
        "Age": 0.2,
        "Nationality": 0.55,
        "Profession": 0.35,
        "Personality": 0.55,
        "Relationships": 0.6,
        "Awards": 0.2,
        "Time period": 0.75,
    },
    "Literature": {
        "Movies": 0.3,
        "TV": 0.15,
        "Anime": 0.1,
        "Cartoons": 0.1,
        "Gaming": 0.1,
        "Sports": 0.06,
        "Science": 0.12,
        "History": 0.3,
        "Politics": 0.12,
        "Music": 0.12,
        "Literature": 0.9,
        "Mythology": 0.3,
        "Technology": 0.08,
        "Fictional traits": 0.85,
        "Physical appearance": 0.5,
        "Gender": 0.5,
        "Age": 0.45,
        "Nationality": 0.55,
        "Profession": 0.55,
        "Personality": 0.6,
        "Relationships": 0.55,
        "Awards": 0.4,
        "Time period": 0.65,
    },
}

# Minimum |prior - 0.5| to emit a domain (non-universal) rule.
DOMAIN_LINK_THRESHOLD = 0.15

DEFAULT_SAMPLE_SIZE = 40


def _clamp(value: float) -> float:
    return round(max(0.02, min(0.98, value)), 3)


def base_prior(character_category: str, question_category: str) -> float | None:
    """Return curated base prior, or None if unknown category pair."""
    row = _BASE.get(character_category)
    if not row:
        return None
    return row.get(question_category)


def refine_prior(
    character_category: str,
    question_text: str,
    question_category: str,
    prior: float,
) -> float:
    """Deterministic keyword refinements on top of category priors."""
    text = question_text.casefold()
    p = prior

    # Reality / fiction
    if "real person" in text:
        p = 0.92 if character_category in REAL_WORLD else 0.1
    elif "made-up" in text or "fictional" in text:
        p = 0.92 if character_category in FICTIONAL_MEDIA else 0.08
    elif "still alive" in text or "alive today" in text:
        if character_category in {"Historical Figures", "Mythology"}:
            p = 0.06
        elif character_category in {"Sports", "Politicians", "Musicians", "Business Leaders"}:
            p = 0.72
        elif character_category == "Scientists":
            p = 0.35

    # Strong domain anchors
    anchors = [
        ("video game", "Gaming", 0.96, 0.08),
        ("from anime", "Anime", 0.96, 0.06),
        ("from a cartoon", "Cartoons", 0.95, 0.08),
        ("tv show", "TV Shows", 0.94, 0.2),
        ("from a movie", "Movies", 0.94, 0.2),
        ("sports player", "Sports", 0.96, 0.07),
        ("a scientist", "Scientists", 0.95, 0.08),
        ("political leader", "Politicians", 0.95, 0.08),
        ("a musician", "Musicians", 0.96, 0.1),
        ("a writer", "Literature", 0.88, 0.15),
        ("old legend", "Mythology", 0.96, 0.08),
        ("business leader", "Business Leaders", 0.94, 0.12),
        ("from long ago", "Historical Figures", 0.8, 0.15),
    ]
    for needle, match_cat, high, low in anchors:
        if needle in text:
            p = high if character_category == match_cat else min(p, low)

    # Geography — defaults stay LOW so YES hard-constraints eliminate mismatches.
    # Character overrides raise true matches (India cricket stars, USA athletes, …).
    if "from india" in text:
        if character_category == "Anime":
            p = 0.08
        elif character_category in {"Sports", "Politicians", "Musicians", "Business Leaders", "Movies"}:
            p = 0.12  # below constraint affirm_max; overrides raise Indians
        else:
            p = min(p, 0.15)
    elif "from japan" in text:
        if character_category == "Anime":
            p = 0.88
        elif character_category in REAL_WORLD:
            p = min(p, 0.12)
        else:
            p = min(p, 0.2)
    elif "japan" in text or ("asia" in text and "india" not in text):
        if character_category == "Anime":
            p = max(p, 0.85)
        elif character_category in REAL_WORLD:
            p = min(p, 0.18)
    if "europe" in text and character_category in {"Historical Figures", "Literature"}:
        p = max(p, 0.55)
    elif "from europe" in text and character_category in REAL_WORLD:
        p = min(p, 0.18)
    if "united states" in text or "from the usa" in text or "from america" in text:
        if character_category in {"Sports", "Movies", "Business Leaders", "Musicians"}:
            p = 0.15  # overrides raise US stars
        elif character_category == "Anime":
            p = min(p, 0.12)
    if "from australia" in text and character_category in REAL_WORLD:
        p = min(p, 0.12)
    if "from the uk" in text or "united kingdom" in text:
        if character_category in REAL_WORLD:
            p = min(p, 0.15)
        if character_category in {"Historical Figures", "Literature"}:
            p = max(p, 0.4)

    # Sport subtypes — category Sports is NOT enough; defaults stay low so
    # cricket≠football. Character overrides raise the matching athletes.
    sport_needles = (
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
        "wrestling",
        "swimming",
        "athletics",
        "formula",
        "racing",
        "wicket",
        "opening batter",
        "an opener",
        "a bowler",
        "mainly a bowler",
        "volleyball",
    )
    if any(n in text for n in sport_needles) and "sports player" not in text and "athlete" not in text:
        if character_category == "Sports":
            p = 0.12  # below affirm_max; overrides raise the matching sport
        else:
            p = min(p, 0.08)

    cinema_needles = (
        "hindi movies",
        "telugu movies",
        "tamil movies",
        "malayalam movies",
        "kannada movies",
        "bengali movies",
        "marathi movies",
        "punjabi movies",
        "gujarati movies",
        "bhojpuri movies",
        "assamese movies",
        "odia movies",
        "bollywood",
    )
    if any(n in text for n in cinema_needles):
        p = 0.12 if character_category == "Movies" else min(p, 0.08)

    if "film director" in text:
        p = 0.12 if character_category == "Movies" else min(p, 0.08)

    if "freedom fighter" in text:
        if character_category in {"Historical Figures", "Politicians"}:
            p = 0.12
        else:
            p = min(p, 0.08)

    state_needles = (
        "maharashtra",
        "uttar pradesh",
        "west bengal",
        "tamil nadu",
        "karnataka",
        "kerala",
        "gujarat",
        "bihar",
        "andhra",
        "telangana",
        "punjab",
        "delhi",
    )
    if any(n in text for n in state_needles) and "movies" not in text:
        p = 0.12 if character_category in {"Politicians", "Historical Figures"} else min(p, 0.10)

    # Gender — category defaults are uninformative; keep near-neutral here.
    if "girl or woman" in text or "a woman" in text or "are they female" in text:
        p = 0.48
    if "are they male" in text or "a man?" in text or "character a man" in text:
        p = 0.52

    # Era
    if "known today" in text or "21st century" in text:
        if character_category in {"Business Leaders", "Sports", "Politicians", "Gaming"}:
            p = max(p, 0.7)
        if character_category in {"Historical Figures", "Mythology"}:
            p = min(p, 0.15)
    if "1900s" in text or "20th century" in text:
        if character_category == "Historical Figures":
            p = max(p, 0.45)

    # Appearance / costume more common in fiction & sports
    if "costume" in text or "mask" in text:
        if character_category in {"Movies", "Gaming", "Cartoons", "Anime"}:
            p = max(p, 0.55)
        elif character_category in REAL_WORLD:
            p = min(p, 0.2)

    # Space leans Scientists
    if "about space" in text or "astronomy" in text:
        p = 0.7 if character_category == "Scientists" else min(p, 0.25)

    # War leans Historical / Politicians / Mythology
    if "linked to war" in text or "military" in text:
        if character_category in {"Historical Figures", "Politicians", "Mythology"}:
            p = max(p, 0.55)
        elif character_category in {"Sports", "Musicians"}:
            p = min(p, 0.2)

    # Ignore unused question_category arg except for clarity in callers
    _ = question_category
    return _clamp(p)


def should_link(
    character_category: str,
    question_category: str,
    prior: float,
) -> bool:
    """Link only universal questions or meaningfully skewed domain priors."""
    if question_category in UNIVERSAL_QUESTION_CATEGORIES:
        return True
    # Always link primary domain alignment and strong anti-alignment
    primary = PRIMARY_ALIGNMENT.get(question_category)
    if primary == character_category:
        return True
    if character_category in FICTIONAL_MEDIA and question_category == "Fictional traits":
        return True
    if character_category in REAL_WORLD and question_category == "Fictional traits":
        return True
    return abs(prior - 0.5) >= DOMAIN_LINK_THRESHOLD


def build_likelihood_rules(
    questions: Iterable[dict],
    *,
    sample_size: int = DEFAULT_SAMPLE_SIZE,
    explicit_rules: dict[str, dict[str, float]] | None = None,
) -> list[dict]:
    """
    Build category→question likelihood_rules for the seed.

    ``explicit_rules`` (legacy hand-tuned RULES) win over generated priors.
    """
    explicit = explicit_rules or {}
    # (category, question_text) -> (likelihood, sample_size)
    merged: dict[tuple[str, str], tuple[float, int]] = {}

    for question in questions:
        text = question["text"].strip()
        q_cat = question["category"].strip()
        for char_cat in CHAR_CATEGORIES:
            base = base_prior(char_cat, q_cat)
            if base is None:
                continue
            prior = refine_prior(char_cat, text, q_cat, base)
            if not should_link(char_cat, q_cat, prior):
                continue
            merged[(char_cat, text)] = (prior, sample_size)

    # Explicit legacy RULES override generated values
    for char_cat, mapping in explicit.items():
        for text, lik in mapping.items():
            merged[(char_cat, text)] = (_clamp(float(lik)), sample_size)

    rules = [
        {
            "category": char_cat,
            "question": text,
            "likelihood": lik,
            "sample_size": sample,
        }
        for (char_cat, text), (lik, sample) in sorted(
            merged.items(), key=lambda item: (item[0][0], item[0][1])
        )
    ]
    return rules


def estimate_character_coverage(
    characters: list[dict],
    rules: list[dict],
) -> dict[str, int]:
    """Return mapping count per character name from category rules."""
    by_cat: dict[str, int] = {}
    for rule in rules:
        by_cat[rule["category"]] = by_cat.get(rule["category"], 0) + 1
    return {c["name"]: by_cat.get(c["category"], 0) for c in characters}


def assert_mapping_quality(
    characters: list[dict],
    questions: list[dict],
    rules: list[dict],
    *,
    min_per_character: int = 80,
) -> None:
    """Raise RuntimeError if mappings fail coverage / appropriateness checks."""
    if not rules:
        raise RuntimeError("No likelihood rules generated")

    q_by_text = {q["text"]: q for q in questions}
    for rule in rules:
        if rule["question"] not in q_by_text:
            raise RuntimeError(f"Rule references unknown question: {rule['question']!r}")
        if rule["category"] not in CHAR_CATEGORIES:
            raise RuntimeError(f"Rule references unknown category: {rule['category']!r}")
        lik = float(rule["likelihood"])
        if not 0.0 <= lik <= 1.0:
            raise RuntimeError(f"Invalid likelihood {lik} for {rule}")

    coverage = estimate_character_coverage(characters, rules)
    thin = sorted(
        (name, n) for name, n in coverage.items() if n < min_per_character
    )
    if thin:
        raise RuntimeError(
            f"{len(thin)} characters have fewer than {min_per_character} mapped "
            f"questions; examples: {thin[:5]}"
        )

    # Category-specific appropriateness: primary domain questions must be high
    # for their aligned category and low for a clearly wrong real/fiction pair.
    checks = [
        ("Is this from anime?", "Anime", "Sports", 0.8, 0.25),
        ("Is this a sports player?", "Sports", "Anime", 0.8, 0.25),
        ("Is this a scientist?", "Scientists", "Cartoons", 0.8, 0.25),
        ("Is this from a video game?", "Gaming", "Politicians", 0.8, 0.25),
        ("Is this from an old legend?", "Mythology", "Business Leaders", 0.8, 0.25),
    ]
    index = {(r["category"], r["question"]): float(r["likelihood"]) for r in rules}
    for text, high_cat, low_cat, high_min, low_max in checks:
        if text not in q_by_text:
            continue
        high = index.get((high_cat, text))
        low = index.get((low_cat, text))
        if high is None or low is None:
            raise RuntimeError(f"Missing appropriateness rules for {text!r}")
        if high < high_min or low > low_max:
            raise RuntimeError(
                f"Inappropriate mapping for {text!r}: "
                f"{high_cat}={high}, {low_cat}={low}"
            )
