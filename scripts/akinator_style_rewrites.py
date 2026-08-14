"""Map previous v2 question texts → Akinator-style phrasing.

Used to rewrite the catalog and UPDATE live DB rows in place (same question id),
so character_answers likelihoods stay attached.
"""

from __future__ import annotations

# Hand-tuned Akinator-style phrasings (classic gameplay questions).
OVERRIDES: dict[str, str] = {
    "Is this a real person?": "Is your character a real person?",
    "Is this a made-up character?": "Is your character made-up?",
    "Is this person still alive?": "Is your character still alive?",
    "Are they male?": "Is your character a man?",
    "Are they a girl or woman?": "Is your character a woman?",
    "Are they a kid or teen?": "Is your character a kid?",
    "Are they a grown-up?": "Is your character a grown-up?",
    "Are they human?": "Is your character human?",
    "Are they an animal?": "Is your character an animal?",
    "Are they famous worldwide?": "Is your character famous?",
    "Do people still talk about them?": "Is your character still famous?",
    "Is this a sports player?": "Is your character an athlete?",
    "Is this from a movie?": "Is your character from a movie?",
    "Is this from a TV show?": "Is your character from TV?",
    "Is this from anime?": "Is your character from anime?",
    "Is this from a cartoon?": "Is your character from a cartoon?",
    "Is this from a video game?": "Is your character from a game?",
    "Is this a scientist?": "Is your character a scientist?",
    "Is this a musician?": "Is your character a musician?",
    "Is this a writer?": "Is your character a writer?",
    "Is this a political leader?": "Is your character a politician?",
    "Is this a business leader?": "Is your character a business person?",
    "Is this from an old legend?": "Is your character from a myth?",
    "Is this a superhero?": "Is your character a superhero?",
    "Is this about magic?": "Does your character use magic?",
    "Is this sci-fi?": "Is your character from sci-fi?",
    "Is this about space?": "Is your character linked to space?",
    "Is this from long ago?": "Is your character from long ago?",
    "Are they a hero?": "Is your character a hero?",
    "Are they a villain?": "Is your character a villain?",
    "Are they famous for cricket?": "Does your character play cricket?",
    "Are they famous for football?": "Does your character play football?",
    "Are they famous for basketball?": "Does your character play basketball?",
    "Are they famous for tennis?": "Does your character play tennis?",
    "Are they famous for baseball?": "Does your character play baseball?",
    "Are they famous for boxing?": "Does your character box?",
    "Are they famous for badminton?": "Does your character play badminton?",
    "Are they famous for golf?": "Does your character play golf?",
    "Are they famous for hockey?": "Does your character play hockey?",
    "Are they famous for wrestling?": "Does your character wrestle?",
    "Are they famous for car racing?": "Does your character race cars?",
    "Are they from the Middle East?": "Is your character from the Middle East?",
    "Are they a singer?": "Is your character a singer?",
    "Are they an actor?": "Is your character an actor?",
    "Are they an actress?": "Is your character an actress?",
    "Are they a ninja or samurai?": "Is your character a ninja?",
    "Are they a pirate?": "Is your character a pirate?",
    "Are they a knight?": "Does your character wear metal armor?",
    "Are they a wizard?": "Does your character cast magic spells?",
    "Are they a princess?": "Is your character a princess?",
    "Are they a detective?": "Does your character solve mysteries?",
    "Are they a robot or cyborg?": "Is your character part robot?",
    "Are they an Olympic winner?": "Did your character win sports gold?",
    "Are they a space traveler?": "Does your character go to space?",
    "Are they a teacher in the story?": "Is your character a teacher?",
    "Are they a student in the story?": "Is your character a student?",
    "Are they a doctor in the story?": "Is your character a doctor?",
    "Do they have anime powers?": "Does your character have powers?",
    "Do they fight with a sword?": "Does your character use a sword?",
    "Do they wear a cape?": "Does your character wear a cape?",
    "Are they known for goals scored?": "Is your character a forward?",
    "Are they known for batting?": "Is your character known for batting?",
    "Do they play with a ball?": "Does your character play with a ball?",
    "Do they sing songs?": "Does your character sing?",
    "Are they from India?": "Is your character from India?",
    "Are they from Japan?": "Is your character from Japan?",
    "Are they from the United States?": "Is your character from the USA?",
    "Are they from the United Kingdom?": "Is your character from the UK?",
    "Are they from Asia?": "Is your character from Asia?",
    "Are they from Europe?": "Is your character from Europe?",
    "Are they from the Americas?": "Is your character from America?",
    "Are they from Africa?": "Is your character from Africa?",
    "Are they from Australia?": "Is your character from Australia?",
    "Are they from modern times?": "Is your character from modern times?",
    "Are they from history?": "Is your character from history?",
    "Are they known today?": "Is your character known today?",
    "Have they won big awards?": "Has your character won awards?",
    "Do they wear a costume?": "Does your character wear a costume?",
    "Do they wear a mask?": "Does your character wear a mask?",
    "Are they linked to war?": "Is your character linked to war?",
    "Are they on a famous team?": "Is your character on a team?",
    "Do they wear a sports jersey?": "Does your character wear a jersey?",
    "Is this from long-ago history?": "Is your character from history books?",
    "Is this about sports games?": "Is your character about sports?",
    "Is this about school life?": "Is your character about school?",
    "Is this about music shows?": "Is your character about music?",
    "Is this about science work?": "Is your character about science?",
    "Is this about old wars?": "Is your character about war?",
    "Is this about kings and queens?": "Is your character a royal?",
    "Is this about computers?": "Is your character about computers?",
    "Is this about phones or apps?": "Is your character about phones?",
}


def to_akinator_style(text: str) -> str:
    """Convert a legacy/v2 question into Akinator-style wording."""
    raw = text.strip()
    if raw in OVERRIDES:
        return OVERRIDES[raw]

    out = raw
    prefixes = (
        ("Is this person ", "Is your character "),
        ("Is this a ", "Is your character a "),
        ("Is this from ", "Is your character from "),
        ("Is this about ", "Is your character about "),
        ("Is this sci-fi?", "Is your character from sci-fi?"),
        ("Are they a ", "Is your character a "),
        ("Are they ", "Is your character "),
        ("Do they ", "Does your character "),
        ("Did they ", "Did your character "),
        ("Were they ", "Was your character "),
        ("Have they ", "Has your character "),
        ("Can they ", "Can your character "),
    )
    for old, new in prefixes:
        if out.startswith(old):
            out = new + out[len(old) :]
            break

    out = out.replace("Is your character about ", "Is your character linked to ")
    return out


def rewrite_map(texts: list[str]) -> dict[str, str]:
    """old text → new text for every input."""
    mapping: dict[str, str] = {}
    used_new: set[str] = set()
    for old in texts:
        new = to_akinator_style(old)
        base = new
        n = 2
        while new.casefold() in used_new:
            new = f"{base[:-1]} ({n})?"
            n += 1
        used_new.add(new.casefold())
        mapping[old] = new
    return mapping
