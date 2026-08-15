"""Logical filters for question selection (not Bayesian scoring).

Tags are inferred from question text so the database schema stays unchanged.
Information gain is applied only among questions that pass these checks.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.engine.models import GameEngineState, QuestionRef

# Character KB categories that are real-world people (not fictional / animals).
REAL_HUMAN_CATEGORIES: frozenset[str] = frozenset(
    {
        "Sports",
        "Scientists",
        "Historical Figures",
        "Politicians",
        "Musicians",
        "Business Leaders",
    }
)
FICTIONAL_ONLY_CATEGORIES: frozenset[str] = frozenset(
    {
        "Anime",
        "Cartoons",
        "Gaming",
        "Mythology",
    }
)
ANIMAL_CATEGORIES: frozenset[str] = frozenset({"Animals"})

# Exclusive families: a YES on one polarity forbids the others.
_EXCLUSIVE_FAMILIES: frozenset[str] = frozenset(
    {"entity", "realness", "gender", "origin", "sport"}
)

_BOILERPLATE_PREFIXES: tuple[str, ...] = (
    "is your character ",
    "does your character ",
    "did your character ",
    "can your character ",
    "are they ",
    "were they ",
    "is this person ",
    "is this ",
    "is it ",
    "did they ",
    "do they ",
    "was this ",
    "was it ",
)

_SPORT_SUBTYPES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("cricket", ("cricket", "cricketer")),
    ("football", ("football", "soccer", "footballer")),
    ("tennis", ("tennis",)),
    ("basketball", ("basketball",)),
    ("baseball", ("baseball",)),
    ("hockey", ("hockey",)),
    ("golf", ("golf",)),
    ("boxing", ("boxing", "boxer")),
    ("skating", ("skating", "skater")),
    ("fencing", ("fencing", "fencer")),
    ("martial_arts", ("martial arts",)),
    ("swimming", ("swimming", "swimmer")),
    ("running", ("running", "sprinter", "runner")),
    ("gymnastics", ("gymnastics",)),
    ("racing", ("racing", "racer")),
    ("rugby", ("rugby",)),
    ("volleyball", ("volleyball",)),
    ("wrestling", ("wrestling", "wrestler")),
    ("archery", ("archery",)),
    ("cycling", ("cycling", "cyclist")),
)

_CRICKET_TRAITS: tuple[str, ...] = (
    "opening batter",
    "batter",
    "batsman",
    "batting",
    "bowler",
    "all-rounder",
    "all rounder",
    "wicket",
    "captain the",
    "debut",
)
_FOOTBALL_TRAITS: tuple[str, ...] = (
    "goalkeeper",
    "midfielder",
    "striker",
    "forward",
)


@dataclass(frozen=True)
class QuestionTags:
    """Lightweight metadata inferred from question text."""

    semantic_key: str
    family: str | None = None
    polarity: str | None = None
    exclusive: bool = False
    requires: frozenset[str] = field(default_factory=frozenset)
    compatible_entity_types: frozenset[str] | None = None
    real_person_only: bool = False
    fictional_only: bool = False
    human_specific: bool = False
    india_relevant: bool = False
    hierarchy_level: int = 5


@dataclass
class EstablishedFacts:
    """Facts established from answers (not from candidate probability)."""

    values: dict[str, str] = field(default_factory=dict)
    answered_keys: set[str] = field(default_factory=set)
    negated: set[tuple[str, str]] = field(default_factory=set)
    pool_real_human: bool = False
    pool_fictional: bool = False
    pool_animal: bool = False


def normalize_question_text(text: str) -> str:
    """Strip Akinator-style boilerplate so equivalent wordings share a key."""
    t = " ".join((text or "").casefold().split())
    t = t.replace("?", "").strip()
    for prefix in _BOILERPLATE_PREFIXES:
        if t.startswith(prefix):
            t = t[len(prefix) :]
            break
    return t.strip(" .")


def _contains(text: str, *phrases: str) -> bool:
    return any(p in text for p in phrases)


def classify_question(ref: QuestionRef | None) -> QuestionTags:
    """Infer hierarchy / compatibility tags from question text."""
    if ref is None:
        return QuestionTags(semantic_key="")
    raw = (ref.text or "").casefold()
    text = normalize_question_text(ref.text or "")
    category = (ref.category or "").strip()

    # --- Level 1: entity type (specific phrases before generic "animal") ---
    if _contains(raw, "talking cartoon animal", "talking animal", "animal stories"):
        return QuestionTags(
            semantic_key="fictional_animal",
            fictional_only=True,
            hierarchy_level=5,
        )
    if _contains(raw, "turn into animals", "turn into an animal"):
        return QuestionTags(
            semantic_key="shape_shift_animal",
            fictional_only=True,
            hierarchy_level=5,
        )
    if _contains(
        raw,
        "an animal",
        "are they an animal",
        "character an animal",
        "is this an animal",
        "is it an animal",
        "are they animal",
    ) or text in {"animal", "animal?"}:
        return QuestionTags(
            semantic_key="entity_animal",
            family="entity",
            polarity="animal",
            exclusive=True,
            compatible_entity_types=frozenset({"animal"}),
            hierarchy_level=1,
        )
    if _contains(
        raw,
        "are they human",
        "character human",
        "character a human",
        "is this a human",
        "is it a human",
        "a human?",
    ) or text in {"human", "human?"}:
        return QuestionTags(
            semantic_key="entity_human",
            family="entity",
            polarity="human",
            exclusive=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=1,
        )
    if _contains(raw, "a place", "a location", "is this a country") or text in {
        "place",
        "a place",
    }:
        return QuestionTags(
            semantic_key="entity_place",
            family="entity",
            polarity="place",
            exclusive=True,
            compatible_entity_types=frozenset({"place"}),
            hierarchy_level=1,
        )
    if _contains(raw, "an object", "a thing", "inanimate") or text in {
        "object",
        "a thing",
        "a thing/object",
    }:
        return QuestionTags(
            semantic_key="entity_object",
            family="entity",
            polarity="object",
            exclusive=True,
            compatible_entity_types=frozenset({"object"}),
            hierarchy_level=1,
        )

    # --- Real vs fictional ---
    if _contains(raw, "made-up guild"):
        return QuestionTags(
            semantic_key="fictional_guild",
            fictional_only=True,
            hierarchy_level=5,
        )
    if _contains(
        raw,
        "made-up character",
        "made-up?",
        "character made-up",
        "fictional character",
        "a fictional",
    ) or text in {"made-up", "fictional"}:
        return QuestionTags(
            semantic_key="realness_fictional",
            family="realness",
            polarity="fictional",
            exclusive=True,
            hierarchy_level=1,
        )
    if _contains(raw, "real person", "a real person") or text in {"real", "real?"}:
        return QuestionTags(
            semantic_key="realness_real",
            family="realness",
            polarity="real",
            exclusive=True,
            real_person_only=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=1,
        )

    # --- Gender / alive / famous (broad identity) ---
    if _contains(raw, "girl or woman", "a woman", "are they female", "character a woman") or text in {
        "female",
        "female?",
        "woman",
    }:
        return QuestionTags(
            semantic_key="gender_female",
            family="gender",
            polarity="female",
            exclusive=True,
            human_specific=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=2,
        )
    if _contains(raw, "are they male", "a man", "character a man") or text in {
        "male",
        "male?",
        "man",
    }:
        return QuestionTags(
            semantic_key="gender_male",
            family="gender",
            polarity="male",
            exclusive=True,
            human_specific=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=2,
        )
    if _contains(
        raw,
        "still alive",
        "alive today",
        "are they alive",
        "character still alive",
        "alive?",
    ):
        return QuestionTags(
            semantic_key="life_alive",
            family="life",
            polarity="alive",
            compatible_entity_types=frozenset({"human", "animal"}),
            hierarchy_level=2,
        )
    if _contains(
        raw,
        "famous worldwide",
        "are they famous",
        "character famous",
        "still famous",
        "people still talk",
    ) or text in {"famous", "famous?"}:
        return QuestionTags(
            semantic_key="fame_famous",
            family="fame",
            polarity="famous",
            hierarchy_level=2,
        )

    # --- Origin (India aliases share one semantic key) ---
    india_origin = _contains(raw, "from india", "from india?") or (
        "indian" in raw
        and "indiana" not in raw
        and "indianapol" not in raw
        and "cricket" not in raw
        and "tennis" not in raw
        and "football" not in raw
        and "hockey" not in raw
    )
    if india_origin:
        return QuestionTags(
            semantic_key="origin_india",
            family="origin",
            polarity="india",
            exclusive=True,
            human_specific=True,
            india_relevant=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=2,
        )
    origin_map = (
        ("japan", "from japan"),
        ("usa", "from the united states"),
        ("usa", "from the usa"),
        ("uk", "from the united kingdom"),
        ("uk", "from the uk"),
        ("australia", "from australia"),
        ("europe", "from europe"),
        ("americas", "from the americas"),
        ("america", "from america"),
        ("africa", "from africa"),
        ("asia", "from asia"),
        ("argentina", "from argentina"),
        ("other", "another country"),
        ("other", "from your country"),
    )
    for polarity, phrase in origin_map:
        if phrase in raw:
            return QuestionTags(
                semantic_key=f"origin_{polarity}",
                family="origin",
                polarity=polarity,
                exclusive=True,
                human_specific=True,
                compatible_entity_types=frozenset({"human"}),
                hierarchy_level=2,
            )

    # --- Sport specifics before subtypes (batter vs cricket) ---
    for trait in _CRICKET_TRAITS:
        if _contains(raw, trait):
            key = trait.replace(" ", "_")
            return QuestionTags(
                semantic_key=f"sport_trait_cricket_{key}",
                family="sport_trait",
                polarity=key,
                requires=frozenset({"sport:cricket"}),
                human_specific=True,
                india_relevant="india" in raw,
                compatible_entity_types=frozenset({"human"}),
                hierarchy_level=5,
            )
    if _contains(raw, "play for india"):
        return QuestionTags(
            semantic_key="sport_india_team",
            family="sport_trait",
            polarity="india_team",
            requires=frozenset({"domain:sports"}),
            human_specific=True,
            india_relevant=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=5,
        )
    football_token = next((t for t in _FOOTBALL_TRAITS if _contains(raw, t)), None)
    if football_token is not None or _contains(raw, "play for argentina", "for argentina"):
        key = (football_token or "club").replace(" ", "_")
        return QuestionTags(
            semantic_key=f"sport_trait_football_{key}",
            family="sport_trait",
            polarity=key,
            requires=frozenset({"sport:football"}),
            human_specific=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=5,
        )

    # Indian <sport> player — subcategory after the sport is known.
    if "indian cricket" in raw:
        return QuestionTags(
            semantic_key="sport_cricket_india",
            family="sport",
            polarity="cricket_india",
            requires=frozenset({"sport:cricket"}),
            human_specific=True,
            india_relevant=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=4,
        )
    if "indian tennis" in raw:
        return QuestionTags(
            semantic_key="sport_tennis_india",
            family="sport",
            polarity="tennis_india",
            requires=frozenset({"sport:tennis"}),
            human_specific=True,
            india_relevant=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=4,
        )

    for sport, phrases in _SPORT_SUBTYPES:
        if _contains(raw, *phrases):
            return QuestionTags(
                semantic_key=f"sport_{sport}",
                family="sport",
                polarity=sport,
                exclusive=True,
                requires=frozenset({"domain:sports"}),
                human_specific=True,
                india_relevant=sport == "cricket",
                compatible_entity_types=frozenset({"human"}),
                hierarchy_level=4,
            )

    # --- Broad domains ---
    if _contains(
        raw,
        "sports player",
        "sportsperson",
        "an athlete",
        "your character an athlete",
        "from sports",
        "a sports",
    ) or text in {"athlete", "athlete?"}:
        return QuestionTags(
            semantic_key="domain_sports",
            family="domain",
            polarity="sports",
            human_specific=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=3,
        )
    if _contains(raw, "from a movie", "from movies") or text in {
        "movie",
        "movies",
        "from a movie",
    }:
        return QuestionTags(
            semantic_key="domain_movies",
            family="domain",
            polarity="movies",
            hierarchy_level=3,
        )
    if _contains(raw, "from anime") or text in {"anime", "from anime"}:
        return QuestionTags(
            semantic_key="domain_anime",
            family="domain",
            polarity="anime",
            fictional_only=True,
            hierarchy_level=3,
        )
    if _contains(raw, "from a cartoon", "from cartoons"):
        return QuestionTags(
            semantic_key="domain_cartoons",
            family="domain",
            polarity="cartoons",
            fictional_only=True,
            hierarchy_level=3,
        )
    if _contains(raw, "from a video game", "from a game", "from gaming"):
        return QuestionTags(
            semantic_key="domain_gaming",
            family="domain",
            polarity="gaming",
            fictional_only=True,
            hierarchy_level=3,
        )
    if _contains(raw, "a musician", "a singer") or text in {"musician", "musician?"}:
        return QuestionTags(
            semantic_key="domain_music",
            family="domain",
            polarity="music",
            human_specific=True,
            real_person_only=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=3,
        )
    if _contains(raw, "political leader", "a politician") or text in {
        "politician",
        "politician?",
    }:
        return QuestionTags(
            semantic_key="domain_politics",
            family="domain",
            polarity="politics",
            human_specific=True,
            real_person_only=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=3,
        )
    if _contains(raw, "a scientist") or text in {"scientist", "scientist?"}:
        return QuestionTags(
            semantic_key="domain_science",
            family="domain",
            polarity="science",
            human_specific=True,
            real_person_only=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=3,
        )
    if _contains(raw, "business leader", "business person"):
        return QuestionTags(
            semantic_key="domain_business",
            family="domain",
            polarity="business",
            human_specific=True,
            real_person_only=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=3,
        )
    if _contains(raw, "from a tv show", "from tv"):
        return QuestionTags(
            semantic_key="domain_tv",
            family="domain",
            polarity="tv",
            hierarchy_level=3,
        )

    if category in {"Science", "Politics", "Music", "History"}:
        return QuestionTags(
            semantic_key=f"domain_{category.casefold()}",
            family="domain",
            polarity=category.casefold(),
            human_specific=True,
            real_person_only=True,
            compatible_entity_types=frozenset({"human"}),
            hierarchy_level=3,
        )

    if _contains(
        raw,
        "superhero",
        "ice powers",
        "fire powers",
        "lightning powers",
        "special powers",
        "ninja",
        "samurai",
        "wizard",
        "jedi",
        "vampire",
        "power armor",
    ):
        return QuestionTags(
            semantic_key=normalize_question_text(ref.text or "") or "fictional_trait",
            fictional_only=True,
            hierarchy_level=5,
        )

    # Fallback: normalized wording is the semantic identity.
    return QuestionTags(
        semantic_key=text or raw,
        human_specific=category in {"Profession", "Awards", "Politics", "Science"},
        real_person_only=category in {"Science", "Politics"},
        hierarchy_level=5,
    )


def infer_established_facts(
    state: GameEngineState,
    question_refs: dict | None,
    remaining_categories: frozenset[str] | None = None,
) -> EstablishedFacts:
    """Build established facts from the answer log, then apply pool inferences."""
    facts = EstablishedFacts()
    remaining = remaining_categories or frozenset()
    if remaining:
        facts.pool_real_human = remaining <= REAL_HUMAN_CATEGORIES
        facts.pool_fictional = remaining <= FICTIONAL_ONLY_CATEGORIES
        facts.pool_animal = remaining <= ANIMAL_CATEGORIES

    if not question_refs:
        return facts

    for qid, ans in state.answer_log.items():
        ref = question_refs.get(qid)
        if ref is None:
            continue
        tags = classify_question(ref)
        if not tags.semantic_key:
            continue
        if ans == "dont_know":
            facts.answered_keys.add(tags.semantic_key)
            continue
        facts.answered_keys.add(tags.semantic_key)
        if tags.family and tags.polarity:
            if ans in {"yes", "probably_yes"}:
                facts.values[tags.family] = tags.polarity
                # Sport YES also establishes the sports domain.
                if tags.family == "sport":
                    facts.values.setdefault("domain", "sports")
                    facts.values["entity"] = "human"
                if tags.family == "domain" and tags.polarity == "sports":
                    facts.values["entity"] = "human"
                if tags.family == "entity" and tags.polarity == "human":
                    pass
                if tags.family == "realness" and tags.polarity == "real":
                    facts.values.setdefault("entity", "human")
                if tags.family == "origin":
                    facts.values.setdefault("entity", "human")
            elif ans in {"no", "probably_no"}:
                facts.negated.add((tags.family, tags.polarity))

    # Pool flags already capture entity/realness locks. Do not copy them into
    # `values`, or the establishing questions (human / real / made-up) would
    # be treated as redundant before they are asked.

    return facts


def _requirement_met(req: str, facts: EstablishedFacts, remaining_categories: frozenset[str]) -> bool:
    del remaining_categories  # pool unlocks are applied via facts, not this helper
    family, _, value = req.partition(":")
    if family == "domain" and value == "sports":
        return facts.values.get("domain") == "sports"
    if family == "sport":
        return facts.values.get("sport") == value
    return facts.values.get(family) == value


def is_logically_valid_question(
    ref: QuestionRef | None,
    facts: EstablishedFacts,
    remaining_categories: frozenset[str] | None = None,
) -> bool:
    """Return False when the question is redundant, contradictory, or gated."""
    if ref is None:
        return False
    remaining = remaining_categories or frozenset()
    tags = classify_question(ref)

    # Exact / semantic duplicate of an already-resolved question.
    if tags.semantic_key and tags.semantic_key in facts.answered_keys:
        return False

    # Already-known polarity (YES) — asking again is redundant.
    if tags.family and tags.polarity and facts.values.get(tags.family) == tags.polarity:
        return False

    # Exclusive family already decided a different way.
    if tags.exclusive and tags.family and tags.polarity:
        current = facts.values.get(tags.family)
        if current is not None and current != tags.polarity:
            return False

    # Compatible entity types vs established entity.
    entity = facts.values.get("entity")
    if entity and tags.compatible_entity_types is not None:
        if entity not in tags.compatible_entity_types:
            return False

    if tags.human_specific and entity == "animal":
        return False
    if tags.real_person_only and (
        facts.values.get("realness") == "fictional" or facts.pool_fictional
    ):
        return False
    if tags.fictional_only and (
        facts.values.get("realness") == "real" or facts.pool_real_human
    ):
        return False
    if tags.fictional_only and tags.hierarchy_level >= 4:
        if facts.values.get("realness") != "fictional" and not facts.pool_fictional:
            if facts.values.get("domain") not in {"anime", "cartoons", "gaming", "movies"}:
                return False

    # Pool-level entity lock (do not rely only on posterior IG).
    if facts.pool_real_human and tags.family == "entity" and tags.polarity == "animal":
        return False
    if facts.pool_animal and tags.family == "entity" and tags.polarity == "human":
        return False

    for req in tags.requires:
        if not _requirement_met(req, facts, remaining):
            return False

    return True


def india_relevant_score_bonus(ref: QuestionRef | None, facts: EstablishedFacts) -> float:
    """Small ranking bonus among *valid* questions after India is established."""
    if facts.values.get("origin") != "india":
        return 0.0
    if ref is None:
        return 0.0
    tags = classify_question(ref)
    if tags.india_relevant:
        return 0.05
    return 0.0
