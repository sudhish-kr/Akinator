"""Character-level likelihood overrides for discriminative guessing.

Category priors alone cannot separate peers (e.g. Kohli vs Messi on cricket /
India). These overrides supply per-character L(C,Q) for nationality, sport
subtype, gender, reality, and fictional media.
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


def _T(
    *,
    real: bool | None = True,
    alive: bool | None = True,
    female: bool | None = False,
    regions: frozenset[str] | set[str] = frozenset(),
    sports: frozenset[str] | set[str] = frozenset(),
    fictional_media: frozenset[str] | set[str] = frozenset(),
) -> CharacterTraits:
    return CharacterTraits(
        real=real,
        alive=alive,
        female=female,
        regions=frozenset(regions),
        sports=frozenset(sports),
        fictional_media=frozenset(fictional_media),
    )


# Explicit famous / high-traffic characters.
TRAIT_TABLE: dict[str, CharacterTraits] = {
    # --- Cricket ---
    "virat kohli": _T(regions={"india"}, sports={"cricket"}),
    "ms dhoni": _T(regions={"india"}, sports={"cricket"}),
    "sachin tendulkar": _T(regions={"india"}, sports={"cricket"}),
    "rohit sharma": _T(regions={"india"}, sports={"cricket"}),
    "smriti mandhana": _T(female=True, regions={"india"}, sports={"cricket"}),
    "mithali raj": _T(female=True, regions={"india"}, sports={"cricket"}),
    "harmanpreet kaur": _T(female=True, regions={"india"}, sports={"cricket"}),
    "jemimah rodrigues": _T(female=True, regions={"india"}, sports={"cricket"}),
    "rahul dravid": _T(regions={"india"}, sports={"cricket"}),
    "sourav ganguly": _T(regions={"india"}, sports={"cricket"}),
    "kapil dev": _T(regions={"india"}, sports={"cricket"}),
    "anil kumble": _T(regions={"india"}, sports={"cricket"}),
    "jasprit bumrah": _T(regions={"india"}, sports={"cricket"}),
    "hardik pandya": _T(regions={"india"}, sports={"cricket"}),
    "ravindra jadeja": _T(regions={"india"}, sports={"cricket"}),
    "brian lara": _T(regions={"americas"}, sports={"cricket"}),
    "ricky ponting": _T(regions={"australia"}, sports={"cricket"}),
    "steve smith": _T(regions={"australia"}, sports={"cricket"}),
    "joe root": _T(regions={"uk"}, sports={"cricket"}),
    "ben stokes": _T(regions={"uk"}, sports={"cricket"}),
    "kane williamson": _T(regions={"australia"}, sports={"cricket"}),
    "babar azam": _T(regions={"asia"}, sports={"cricket"}),
    # --- Football (soccer) ---
    "lionel messi": _T(regions={"americas", "europe"}, sports={"football"}),
    "lionel messi athlete": _T(regions={"americas", "europe"}, sports={"football"}),
    "cristiano ronaldo": _T(regions={"europe"}, sports={"football"}),
    "neymar": _T(regions={"americas"}, sports={"football"}),
    "kylian mbappé": _T(regions={"europe"}, sports={"football"}),
    "kylian mbappe": _T(regions={"europe"}, sports={"football"}),
    "pele": _T(alive=False, regions={"americas"}, sports={"football"}),
    "pelé": _T(alive=False, regions={"americas"}, sports={"football"}),
    "diego maradona": _T(alive=False, regions={"americas"}, sports={"football"}),
    "zinedine zidane": _T(regions={"europe"}, sports={"football"}),
    "david beckham": _T(regions={"uk", "europe"}, sports={"football"}),
    "erling haaland": _T(regions={"europe"}, sports={"football"}),
    "robert lewandowski": _T(regions={"europe"}, sports={"football"}),
    "karim benzema": _T(regions={"europe"}, sports={"football"}),
    "luka modrić": _T(regions={"europe"}, sports={"football"}),
    "luka modric": _T(regions={"europe"}, sports={"football"}),
    "andres iniesta": _T(regions={"europe"}, sports={"football"}),
    "xavi hernandez": _T(regions={"europe"}, sports={"football"}),
    "thierry henry": _T(regions={"europe"}, sports={"football"}),
    "frank lampard": _T(regions={"uk", "europe"}, sports={"football"}),
    "steven gerrard": _T(regions={"uk", "europe"}, sports={"football"}),
    "paul scholes": _T(regions={"uk", "europe"}, sports={"football"}),
    "ryan giggs": _T(regions={"uk", "europe"}, sports={"football"}),
    "eric cantona": _T(regions={"europe"}, sports={"football"}),
    "dennis bergkamp": _T(regions={"europe"}, sports={"football"}),
    "johan cruyff": _T(alive=False, regions={"europe"}, sports={"football"}),
    "franz beckenbauer": _T(alive=False, regions={"europe"}, sports={"football"}),
    "paolo maldini": _T(regions={"europe"}, sports={"football"}),
    "fabio cannavaro": _T(regions={"europe"}, sports={"football"}),
    "gianluigi buffon": _T(regions={"europe"}, sports={"football"}),
    "iker casillas": _T(regions={"europe"}, sports={"football"}),
    "manuel neuer": _T(regions={"europe"}, sports={"football"}),
    "ronaldinho": _T(regions={"americas"}, sports={"football"}),
    # --- Basketball ---
    "michael jordan": _T(regions={"usa"}, sports={"basketball"}),
    "lebron james": _T(regions={"usa"}, sports={"basketball"}),
    "kobe bryant": _T(alive=False, regions={"usa"}, sports={"basketball"}),
    "stephen curry": _T(regions={"usa"}, sports={"basketball"}),
    "kevin durant": _T(regions={"usa"}, sports={"basketball"}),
    "giannis antetokounmpo": _T(regions={"europe", "usa"}, sports={"basketball"}),
    "shaquille o'neal": _T(regions={"usa"}, sports={"basketball"}),
    "magic johnson": _T(regions={"usa"}, sports={"basketball"}),
    "kareem abdul-jabbar": _T(regions={"usa"}, sports={"basketball"}),
    "tim duncan": _T(regions={"usa"}, sports={"basketball"}),
    "wilt chamberlain": _T(alive=False, regions={"usa"}, sports={"basketball"}),
    "anthony davis": _T(regions={"usa"}, sports={"basketball"}),
    "james harden": _T(regions={"usa"}, sports={"basketball"}),
    "russell westbrook": _T(regions={"usa"}, sports={"basketball"}),
    "kawhi leonard": _T(regions={"usa"}, sports={"basketball"}),
    "ja morant": _T(regions={"usa"}, sports={"basketball"}),
    "zion williamson": _T(regions={"usa"}, sports={"basketball"}),
    "luka dončić": _T(regions={"europe", "usa"}, sports={"basketball"}),
    "luka doncic": _T(regions={"europe", "usa"}, sports={"basketball"}),
    "nikola jokic": _T(regions={"europe", "usa"}, sports={"basketball"}),
    "derrick rose": _T(regions={"usa"}, sports={"basketball"}),
    "dwyne wade": _T(regions={"usa"}, sports={"basketball"}),
    # --- Tennis ---
    "serena williams": _T(female=True, regions={"usa"}, sports={"tennis"}),
    "roger federer": _T(regions={"europe"}, sports={"tennis"}),
    "rafael nadal": _T(regions={"europe"}, sports={"tennis"}),
    "novak djokovic": _T(regions={"europe"}, sports={"tennis"}),
    "andre agassi": _T(regions={"usa"}, sports={"tennis"}),
    "pete sampras": _T(regions={"usa"}, sports={"tennis"}),
    "john mcenroe": _T(regions={"usa"}, sports={"tennis"}),
    "jimmy connors": _T(regions={"usa"}, sports={"tennis"}),
    "bjorn borg": _T(regions={"europe"}, sports={"tennis"}),
    "steffi graf": _T(female=True, regions={"europe"}, sports={"tennis"}),
    "martina navratilova": _T(female=True, regions={"europe", "usa"}, sports={"tennis"}),
    "chris evert": _T(female=True, regions={"usa"}, sports={"tennis"}),
    "naomi osaka": _T(female=True, regions={"japan", "usa"}, sports={"tennis"}),
    "coco gauff": _T(female=True, regions={"usa"}, sports={"tennis"}),
    "iga swiatek": _T(female=True, regions={"europe"}, sports={"tennis"}),
    "aryna sabalenka": _T(female=True, regions={"europe"}, sports={"tennis"}),
    "daniil medvedev": _T(regions={"europe"}, sports={"tennis"}),
    "carlos alcaraz": _T(regions={"europe"}, sports={"tennis"}),
    # --- Other sports ---
    "usain bolt": _T(regions={"americas"}, sports={"athletics"}),
    "simone biles": _T(female=True, regions={"usa"}, sports={"athletics"}),
    "nadia comăneci": _T(female=True, regions={"europe"}, sports={"athletics"}),
    "nadia comaneci": _T(female=True, regions={"europe"}, sports={"athletics"}),
    "muhammad ali": _T(alive=False, regions={"usa"}, sports={"boxing"}),
    "mike tyson": _T(regions={"usa"}, sports={"boxing"}),
    "tiger woods": _T(regions={"usa"}, sports={"golf"}),
    "tiger woods golfer": _T(regions={"usa"}, sports={"golf"}),
    "jack nicklaus": _T(regions={"usa"}, sports={"golf"}),
    "arnold palmer": _T(alive=False, regions={"usa"}, sports={"golf"}),
    "phil mickelson": _T(regions={"usa"}, sports={"golf"}),
    "rory mcilroy": _T(regions={"uk", "europe"}, sports={"golf"}),
    "scottie scheffler": _T(regions={"usa"}, sports={"golf"}),
    "lewis hamilton": _T(regions={"uk", "europe"}, sports={"racing"}),
    "babe ruth": _T(alive=False, regions={"usa"}, sports={"baseball"}),
    "shohei ohtani": _T(regions={"japan", "usa"}, sports={"baseball"}),
    "tom brady": _T(regions={"usa"}, sports={"other"}),
    "patrick mahomes": _T(regions={"usa"}, sports={"other"}),
    "peyton manning": _T(regions={"usa"}, sports={"other"}),
    "joe montana": _T(regions={"usa"}, sports={"other"}),
    "jerry rice": _T(regions={"usa"}, sports={"other"}),
    "lawrence taylor": _T(regions={"usa"}, sports={"other"}),
    "aaron rodgers": _T(regions={"usa"}, sports={"other"}),
    "deion sanders": _T(regions={"usa"}, sports={"other"}),
    "bo jackson": _T(regions={"usa"}, sports={"other"}),
    "wayne gretzky": _T(regions={"americas"}, sports={"hockey"}),
    "alexander ovechkin": _T(regions={"europe", "americas"}, sports={"hockey"}),
    "sidney crosby": _T(regions={"americas"}, sports={"hockey"}),
    "connor mcdavid": _T(regions={"americas"}, sports={"hockey"}),
    "mario lemieux": _T(regions={"americas"}, sports={"hockey"}),
    "bobby orr": _T(regions={"americas"}, sports={"hockey"}),
    "gordie howe": _T(alive=False, regions={"americas"}, sports={"hockey"}),
    "jaromir jagr": _T(regions={"europe", "americas"}, sports={"hockey"}),
    "pavel datsyuk": _T(regions={"europe", "americas"}, sports={"hockey"}),
    # India public figures / entertainment
    "shah rukh khan": _T(regions={"india"}),
    "amitabh bachchan": _T(regions={"india"}),
    "narendra modi": _T(regions={"india"}),
    "a.r. rahman": _T(regions={"india"}),
    "lata mangeshkar": _T(alive=False, female=True, regions={"india"}),
    # Science
    "albert einstein": _T(alive=False, regions={"europe", "usa"}),
    "isaac newton": _T(alive=False, regions={"uk", "europe"}),
    "marie curie": _T(alive=False, female=True, regions={"europe"}),
    # Fiction / Anime
    "naruto uzumaki": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "sasuke uchiha": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "goku": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "luffy": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "monkey d. luffy": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "zoro roronoa": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "light yagami": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "lelouch lamperouge": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "eren yeager": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "mikasa ackerman": _T(real=False, female=True, regions={"japan"}, fictional_media={"anime"}),
    "levi ackerman": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "edward elric": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "alphonse elric": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "sailor moon": _T(real=False, female=True, regions={"japan"}, fictional_media={"anime"}),
    "ichigo kurosaki": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "saitama": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "tanjiro kamado": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "gon freecss": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "killua zoldyck": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "spike spiegel": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "spike cowboy bebop": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "shinji ikari": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "rei ayanami": _T(real=False, female=True, regions={"japan"}, fictional_media={"anime"}),
    "asuka langley": _T(real=False, female=True, regions={"japan"}, fictional_media={"anime"}),
    "deku izuku midoriya": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "all might": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "satoru gojo": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "yuji itadori": _T(real=False, regions={"japan"}, fictional_media={"anime"}),
    "doraemon": _T(real=False, regions={"japan"}, fictional_media={"cartoon"}),
    # Movies / superheroes
    "batman": _T(real=False, regions={"usa"}, fictional_media={"movie", "superhero"}),
    "spider-man": _T(real=False, regions={"usa"}, fictional_media={"movie", "superhero"}),
    "tony stark": _T(real=False, regions={"usa"}, fictional_media={"movie", "superhero"}),
    "iron man": _T(real=False, regions={"usa"}, fictional_media={"movie", "superhero"}),
    "harry potter": _T(real=False, regions={"uk"}, fictional_media={"movie", "book"}),
    "hermione granger": _T(real=False, female=True, regions={"uk"}, fictional_media={"movie", "book"}),
    "wonder woman": _T(real=False, female=True, regions={"usa"}, fictional_media={"movie", "superhero"}),
    "black widow": _T(real=False, female=True, regions={"europe", "usa"}, fictional_media={"movie", "superhero"}),
    "captain america": _T(real=False, regions={"usa"}, fictional_media={"movie", "superhero"}),
    "thor odinson": _T(real=False, regions={"europe", "usa"}, fictional_media={"movie", "superhero"}),
    "the joker": _T(real=False, regions={"usa"}, fictional_media={"movie", "superhero"}),
    "darth vader": _T(real=False, regions={"usa"}, fictional_media={"movie"}),
    "luke skywalker": _T(real=False, regions={"usa"}, fictional_media={"movie"}),
    "james bond": _T(real=False, regions={"uk"}, fictional_media={"movie"}),
    "john wick": _T(real=False, regions={"usa"}, fictional_media={"movie"}),
    "neo": _T(real=False, regions={"usa"}, fictional_media={"movie"}),
}

# Name substrings → sport (applied when not in TRAIT_TABLE).
_NAME_SPORT_HINTS: tuple[tuple[str, str], ...] = (
    ("kohli", "cricket"),
    ("dhoni", "cricket"),
    ("tendulkar", "cricket"),
    ("mandhana", "cricket"),
    ("mithali", "cricket"),
    ("harmanpreet", "cricket"),
    ("jemimah", "cricket"),
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
    ("lewandowski", "football"),
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
    ("mandhana", "india"),
    ("mithali", "india"),
    ("harmanpreet", "india"),
    ("jemimah", "india"),
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

# Placeholder athlete name tokens → sport subtype.
_PLACEHOLDER_SPORT_TOKENS: tuple[tuple[str, str], ...] = (
    ("homerun", "baseball"),
    ("pitcher", "baseball"),
    ("slapshot", "hockey"),
    ("touchdown", "other"),
    ("fastbreak", "basketball"),
    ("marathon", "athletics"),
    ("highjump", "athletics"),
    ("goldmedal", "athletics"),
    ("fairplay", "other"),
    ("striker", "football"),
)

_FEMALE_NAME_HINTS: frozenset[str] = frozenset(
    {
        "smriti",
        "mandhana",
        "mithali",
        "harmanpreet",
        "jemimah",
        "serena",
        "simone",
        "naomi",
        "martina",
        "steffi",
        "chris evert",
        "coco",
        "iga",
        "aryna",
        "nadia",
        "sailor",
        "mikasa",
        "asuka",
        "rei ",
        "misa",
        "nobara",
        "uraraka",
        "hermione",
        "wonder woman",
        "black widow",
        "katniss",
    }
)


def _placeholder_sport(name: str) -> str | None:
    key = name.casefold()
    for token, sport in _PLACEHOLDER_SPORT_TOKENS:
        if token in key:
            return sport
    return None


def traits_for(name: str, category: str | None = None) -> CharacterTraits | None:
    key = name.strip().casefold()
    if key in TRAIT_TABLE:
        return TRAIT_TABLE[key]

    cat = (category or "").strip()
    sports: set[str] = set()
    regions: set[str] = set()
    for needle, sport in _NAME_SPORT_HINTS:
        if needle in key:
            sports.add(sport)
    for needle, region in _NAME_REGION_HINTS:
        if needle in key:
            regions.add(region)

    placeholder = _placeholder_sport(key)
    if placeholder and cat == "Sports":
        sports.add(placeholder)

    female: bool | None = None
    if any(h in key for h in _FEMALE_NAME_HINTS):
        female = True
    elif sports:
        female = False

    if cat == "Anime":
        return CharacterTraits(
            real=False,
            alive=True,
            female=female if female is not None else False,
            regions=frozenset(regions or {"japan"}),
            sports=frozenset(),
            fictional_media=frozenset({"anime"}),
        )

    if cat == "Sports":
        # Every athlete gets real/alive + sport/region when known.
        # Unknown sport → "other" so cricket/football defaults stay low via overrides.
        if not sports:
            sports.add("other")
        return CharacterTraits(
            real=True,
            alive=True,
            female=False if female is None else female,
            regions=frozenset(regions),
            sports=frozenset(sports),
        )

    if cat in {"Movies", "Cartoons", "Gaming", "TV Shows", "Mythology"}:
        media = {
            "Movies": "movie",
            "Cartoons": "cartoon",
            "Gaming": "game",
            "TV Shows": "tv",
            "Mythology": "myth",
        }[cat]
        return CharacterTraits(
            real=False,
            alive=True,
            female=female,
            regions=frozenset(regions),
            fictional_media=frozenset({media, "superhero"} if "spider" in key or "batman" in key or "iron" in key else {media}),
        )

    if cat in {
        "Scientists",
        "Politicians",
        "Musicians",
        "Business Leaders",
        "Historical Figures",
        "Literature",
    }:
        if not sports and not regions and female is None:
            # Still mark reality so Real=YES keeps them and drops fiction.
            return CharacterTraits(real=True, alive=None, female=female)
        return CharacterTraits(
            real=True,
            female=female,
            regions=frozenset(regions),
            sports=frozenset(sports),
        )

    if not sports and not regions:
        return None
    real = True if cat in {
        "Sports",
        "Scientists",
        "Politicians",
        "Musicians",
        "Business Leaders",
        "Historical Figures",
    } else None
    return CharacterTraits(
        real=real,
        female=False if sports else female,
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
            lik = 0.9 if traits.regions & {"americas", "usa"} else 0.12
        elif "another country" in t:
            lik = None
        elif "cricket" in t:
            lik = 0.96 if "cricket" in traits.sports else (0.08 if traits.sports else None)
        elif "football" in t or "soccer" in t:
            lik = 0.96 if "football" in traits.sports else (0.08 if traits.sports else None)
        elif "basketball" in t:
            lik = 0.96 if "basketball" in traits.sports else (0.08 if traits.sports else None)
        elif "tennis" in t:
            lik = 0.96 if "tennis" in traits.sports else (0.08 if traits.sports else None)
        elif "boxing" in t:
            lik = 0.96 if "boxing" in traits.sports else (0.08 if traits.sports else None)
        elif "baseball" in t:
            lik = 0.96 if "baseball" in traits.sports else (0.08 if traits.sports else None)
        elif "hockey" in t:
            lik = 0.96 if "hockey" in traits.sports else (0.08 if traits.sports else None)
        elif "golf" in t:
            lik = 0.96 if "golf" in traits.sports else (0.08 if traits.sports else None)
        elif ("sports player" in t or "an athlete" in t) and (
            traits.sports or (category or "") == "Sports"
        ):
            lik = 0.97
        elif "from anime" in t:
            if "anime" in traits.fictional_media:
                lik = 0.97
            elif traits.real is True:
                lik = 0.06
            elif traits.fictional_media:
                lik = 0.12
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
