"""Character-level likelihood overrides for discriminative guessing.

Category priors alone cannot separate Virat Kohli from Lionel Messi on
cricket / India questions. These overrides supply per-character L(C,Q)
for nationality, sport subtype, gender, and reality.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CharacterTraits:
    """Sparse traits — None means leave category prior untouched."""

    real: bool | None = None
    alive: bool | None = None
    female: bool | None = None
    regions: frozenset[str] = field(default_factory=frozenset)
    sports: frozenset[str] = field(default_factory=frozenset)
    fictional_media: frozenset[str] = field(default_factory=frozenset)


# Explicit famous / high-traffic characters.
TRAIT_TABLE: dict[str, CharacterTraits] = {
    # Cricket / India
    "virat kohli": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "ms dhoni": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "sachin tendulkar": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "rohit sharma": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "rahul dravid": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "sourav ganguly": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "kapil dev": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "anil kumble": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "jasprit bumrah": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "hardik pandya": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "ravindra jadeja": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"}), sports=frozenset({"cricket"})),
    "brian lara": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"americas"}), sports=frozenset({"cricket"})),
    "ricky ponting": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"australia"}), sports=frozenset({"cricket"})),
    "steve smith": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"australia"}), sports=frozenset({"cricket"})),
    "joe root": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"uk"}), sports=frozenset({"cricket"})),
    "ben stokes": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"uk"}), sports=frozenset({"cricket"})),
    "kane williamson": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"australia"}), sports=frozenset({"cricket"})),
    "babar azam": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"asia"}), sports=frozenset({"cricket"})),
    # Football
    "lionel messi": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"americas", "europe"}), sports=frozenset({"football"})),
    "cristiano ronaldo": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"europe"}), sports=frozenset({"football"})),
    "neymar": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"americas"}), sports=frozenset({"football"})),
    "kylian mbappé": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"europe"}), sports=frozenset({"football"})),
    "kylian mbappe": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"europe"}), sports=frozenset({"football"})),
    "pele": CharacterTraits(real=True, alive=False, female=False, regions=frozenset({"americas"}), sports=frozenset({"football"})),
    "pelé": CharacterTraits(real=True, alive=False, female=False, regions=frozenset({"americas"}), sports=frozenset({"football"})),
    "diego maradona": CharacterTraits(real=True, alive=False, female=False, regions=frozenset({"americas"}), sports=frozenset({"football"})),
    "zinedine zidane": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"europe"}), sports=frozenset({"football"})),
    "david beckham": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"uk", "europe"}), sports=frozenset({"football"})),
    # Other sports
    "michael jordan": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"usa"}), sports=frozenset({"basketball"})),
    "lebron james": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"usa"}), sports=frozenset({"basketball"})),
    "serena williams": CharacterTraits(real=True, alive=True, female=True, regions=frozenset({"usa"}), sports=frozenset({"tennis"})),
    "roger federer": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"europe"}), sports=frozenset({"tennis"})),
    "rafael nadal": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"europe"}), sports=frozenset({"tennis"})),
    "usain bolt": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"americas"}), sports=frozenset({"athletics"})),
    "muhammad ali": CharacterTraits(real=True, alive=False, female=False, regions=frozenset({"usa"}), sports=frozenset({"boxing"})),
    "mike tyson": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"usa"}), sports=frozenset({"boxing"})),
    "tiger woods": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"usa"}), sports=frozenset({"golf"})),
    "lewis hamilton": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"uk", "europe"}), sports=frozenset({"racing"})),
    # India public figures / entertainment
    "shah rukh khan": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"})),
    "amitabh bachchan": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"})),
    "narendra modi": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"})),
    "a.r. rahman": CharacterTraits(real=True, alive=True, female=False, regions=frozenset({"india"})),
    "lata mangeshkar": CharacterTraits(real=True, alive=False, female=True, regions=frozenset({"india"})),
    # Science
    "albert einstein": CharacterTraits(real=True, alive=False, female=False, regions=frozenset({"europe", "usa"})),
    "isaac newton": CharacterTraits(real=True, alive=False, female=False, regions=frozenset({"uk", "europe"})),
    "marie curie": CharacterTraits(real=True, alive=False, female=True, regions=frozenset({"europe"})),
    # Fiction
    "naruto uzumaki": CharacterTraits(real=False, alive=True, female=False, regions=frozenset({"japan"}), fictional_media=frozenset({"anime"})),
    "goku": CharacterTraits(real=False, alive=True, female=False, regions=frozenset({"japan"}), fictional_media=frozenset({"anime"})),
    "luffy": CharacterTraits(real=False, alive=True, female=False, regions=frozenset({"japan"}), fictional_media=frozenset({"anime"})),
    "monkey d. luffy": CharacterTraits(real=False, alive=True, female=False, regions=frozenset({"japan"}), fictional_media=frozenset({"anime"})),
    "doraemon": CharacterTraits(real=False, alive=True, female=False, regions=frozenset({"japan"}), fictional_media=frozenset({"cartoon"})),
    "batman": CharacterTraits(real=False, alive=True, female=False, regions=frozenset({"usa"}), fictional_media=frozenset({"movie", "superhero"})),
    "spider-man": CharacterTraits(real=False, alive=True, female=False, regions=frozenset({"usa"}), fictional_media=frozenset({"movie", "superhero"})),
    "tony stark": CharacterTraits(real=False, alive=True, female=False, regions=frozenset({"usa"}), fictional_media=frozenset({"movie", "superhero"})),
    "iron man": CharacterTraits(real=False, alive=True, female=False, regions=frozenset({"usa"}), fictional_media=frozenset({"movie", "superhero"})),
    "harry potter": CharacterTraits(real=False, alive=True, female=False, regions=frozenset({"uk"}), fictional_media=frozenset({"movie", "book"})),
    "hermione granger": CharacterTraits(real=False, alive=True, female=True, regions=frozenset({"uk"}), fictional_media=frozenset({"movie", "book"})),
}

# Name substrings → sport (applied when not in TRAIT_TABLE).
_NAME_SPORT_HINTS: tuple[tuple[str, str], ...] = (
    ("kohli", "cricket"),
    ("dhoni", "cricket"),
    ("tendulkar", "cricket"),
    ("ganguly", "cricket"),
    ("dravid", "cricket"),
    ("bumrah", "cricket"),
    ("jadeja", "cricket"),
    ("ponting", "cricket"),
    ("lara", "cricket"),
    ("messi", "football"),
    ("ronaldo", "football"),
    ("neymar", "football"),
    ("mbappé", "football"),
    ("mbappe", "football"),
    ("haaland", "football"),
    ("beckwski", "football"),
    ("zidane", "football"),
    ("beckham", "football"),
    ("jordan", "basketball"),
    ("lebron", "basketball"),
    ("curry", "basketball"),
    ("federer", "tennis"),
    ("nadal", "tennis"),
    ("djokovic", "tennis"),
    ("serena", "tennis"),
)

_NAME_REGION_HINTS: tuple[tuple[str, str], ...] = (
    ("kohli", "india"),
    ("dhoni", "india"),
    ("tendulkar", "india"),
    ("rohit sharma", "india"),
    ("modi", "india"),
    ("khan", "india"),
    ("bachchan", "india"),
    ("messi", "americas"),
    ("neymar", "americas"),
    ("ronaldo", "europe"),
    ("naruto", "japan"),
    ("goku", "japan"),
    ("doraemon", "japan"),
)


def traits_for(name: str, category: str | None = None) -> CharacterTraits | None:
    key = name.strip().casefold()
    if key in TRAIT_TABLE:
        return TRAIT_TABLE[key]
    sports: set[str] = set()
    regions: set[str] = set()
    for needle, sport in _NAME_SPORT_HINTS:
        if needle in key:
            sports.add(sport)
    for needle, region in _NAME_REGION_HINTS:
        if needle in key:
            regions.add(region)
    if not sports and not regions:
        return None
    real = True if (category or "") in {
        "Sports", "Scientists", "Politicians", "Musicians", "Business Leaders", "Historical Figures"
    } else None
    return CharacterTraits(
        real=real,
        female=False if sports else None,
        regions=frozenset(regions),
        sports=frozenset(sports),
    )


def _clamp(value: float) -> float:
    return round(max(0.02, min(0.98, float(value))), 3)


def overrides_for_character(
    name: str,
    question_texts: list[str],
    *,
    category: str | None = None,
    sample_size: int = 80,
) -> list[dict]:
    """Build likelihood_overrides rows for one character against known questions."""
    traits = traits_for(name, category)
    if traits is None:
        return []

    out: list[dict] = []
    for text in question_texts:
        t = text.casefold()
        lik: float | None = None

        if "real person" in t and traits.real is not None:
            lik = 0.96 if traits.real else 0.08
        elif ("made-up" in t or "fictional" in t) and traits.real is not None:
            lik = 0.08 if traits.real else 0.95
        elif ("still alive" in t or "alive today" in t) and traits.alive is not None:
            lik = 0.92 if traits.alive else 0.08
        elif ("girl or woman" in t or "a woman" in t or "are they female" in t) and traits.female is not None:
            lik = 0.95 if traits.female else 0.06
        elif ("are they male" in t or "a man?" in t or "character a man" in t) and traits.female is not None:
            lik = 0.06 if traits.female else 0.95
        elif "from india" in t:
            lik = 0.96 if "india" in traits.regions else 0.08
        elif "from japan" in t:
            lik = 0.96 if "japan" in traits.regions else 0.08
        elif "from asia" in t and "india" not in t:
            lik = 0.9 if traits.regions & {"japan", "asia", "india"} else 0.15
        elif "from europe" in t:
            lik = 0.9 if traits.regions & {"europe", "uk"} else 0.12
        elif "united states" in t or "from the usa" in t:
            lik = 0.94 if "usa" in traits.regions else 0.1
        elif "united kingdom" in t or "from the uk" in t:
            lik = 0.94 if "uk" in traits.regions else 0.1
        elif "from australia" in t:
            lik = 0.94 if "australia" in traits.regions else 0.08
        elif "americas" in t:
            lik = 0.9 if "americas" in traits.regions or "usa" in traits.regions else 0.12
        elif "another country" in t:
            # "another" is ambiguous; skip
            lik = None
        elif "cricket" in t:
            lik = 0.96 if "cricket" in traits.sports else (0.1 if traits.sports else None)
        elif "football" in t or "soccer" in t:
            lik = 0.96 if "football" in traits.sports else (0.1 if traits.sports else None)
        elif "basketball" in t:
            lik = 0.96 if "basketball" in traits.sports else (0.1 if traits.sports else None)
        elif "tennis" in t:
            lik = 0.96 if "tennis" in traits.sports else (0.1 if traits.sports else None)
        elif "boxing" in t:
            lik = 0.96 if "boxing" in traits.sports else (0.1 if traits.sports else None)
        elif ("sports player" in t or "an athlete" in t) and traits.sports:
            lik = 0.97
        elif "from anime" in t and "anime" in traits.fictional_media:
            lik = 0.97
        elif "from a cartoon" in t and "cartoon" in traits.fictional_media:
            lik = 0.97
        elif "superhero" in t and "superhero" in traits.fictional_media:
            lik = 0.95
        elif "from a movie" in t and "movie" in traits.fictional_media:
            lik = 0.94

        if lik is None:
            continue
        out.append(
            {
                "character": name,
                "question": text,
                "likelihood": _clamp(lik),
                "sample_size": sample_size,
            }
        )
    return out


def build_all_overrides(
    characters: list[dict],
    questions: list[dict],
    *,
    sample_size: int = 80,
) -> list[dict]:
    """Generate overrides for every character that has usable traits."""
    texts = [q["text"] for q in questions if isinstance(q.get("text"), str)]
    merged: dict[tuple[str, str], dict] = {}
    for row in characters:
        name = row.get("name")
        if not isinstance(name, str):
            continue
        for ov in overrides_for_character(
            name,
            texts,
            category=str(row.get("category") or ""),
            sample_size=sample_size,
        ):
            merged[(ov["character"].casefold(), ov["question"].casefold())] = ov
    return [merged[k] for k in sorted(merged)]
