"""Generate data/knowledge/seed_v1.json — 500+ characters across categories.

Run: python scripts/generate_knowledge_seed.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "knowledge" / "seed_v1.json"

CATEGORIES = [
    "Movies",
    "Anime",
    "Sports",
    "Scientists",
    "Historical",
    "Gaming",
    "Music",
    "Literature",
    "TV",
    "Comics",
    "Business",
    "Politics",
]

# Base named characters (hand-curated seeds expanded programmatically to 500+)
BASE: dict[str, list[tuple[str, list[str]]]] = {
    "Scientists": [
        ("Albert Einstein", ["Einstein"]),
        ("Marie Curie", ["Madame Curie"]),
        ("Isaac Newton", ["Newton"]),
        ("Nikola Tesla", ["Tesla"]),
        ("Charles Darwin", ["Darwin"]),
        ("Galileo Galilei", ["Galileo"]),
        ("Stephen Hawking", ["Hawking"]),
        ("Ada Lovelace", ["Lovelace"]),
        ("Alan Turing", ["Turing"]),
        ("Richard Feynman", ["Feynman"]),
        ("Jane Goodall", []),
        ("Carl Sagan", ["Sagan"]),
        ("Rosalind Franklin", []),
        ("Niels Bohr", ["Bohr"]),
        ("James Watson", []),
        ("Francis Crick", []),
        ("Tim Berners-Lee", ["Berners-Lee"]),
        ("Katherine Johnson", []),
        ("George Washington Carver", []),
        ("Hypatia", []),
    ],
    "Sports": [
        ("Lionel Messi", ["Messi"]),
        ("Cristiano Ronaldo", ["Ronaldo", "CR7"]),
        ("Serena Williams", []),
        ("Michael Jordan", ["MJ", "Air Jordan"]),
        ("Usain Bolt", ["Bolt"]),
        ("Simone Biles", []),
        ("Roger Federer", ["Federer"]),
        ("Rafael Nadal", ["Nadal"]),
        ("Muhammad Ali", ["Ali", "Cassius Clay"]),
        ("Pelé", ["Pele"]),
        ("Tiger Woods", []),
        ("Lewis Hamilton", []),
        ("Tom Brady", []),
        ("Babe Ruth", []),
        ("Nadia Comăneci", ["Nadia Comaneci"]),
        ("Sachin Tendulkar", ["Tendulkar"]),
        ("Virat Kohli", ["Kohli"]),
        ("Diego Maradona", ["Maradona"]),
        ("Mike Tyson", ["Tyson"]),
        ("Shohei Ohtani", ["Ohtani"]),
    ],
    "Movies": [
        ("Harry Potter", []),
        ("Hermione Granger", ["Hermione"]),
        ("Luke Skywalker", []),
        ("Darth Vader", ["Anakin Skywalker", "Vader"]),
        ("Indiana Jones", ["Indy"]),
        ("James Bond", ["007", "Bond"]),
        ("Ellen Ripley", ["Ripley"]),
        ("Neo", ["Thomas Anderson"]),
        ("Forrest Gump", []),
        ("Tony Stark", ["Iron Man"]),
        ("Jack Sparrow", ["Captain Jack Sparrow"]),
        ("Katniss Everdeen", ["Katniss"]),
        ("Frodo Baggins", ["Frodo"]),
        ("Gandalf", []),
        ("Sherlock Holmes", ["Holmes"]),
        ("John Wick", []),
        ("Maximus", ["Maximus Decimus Meridius"]),
        ("Clarice Starling", []),
        ("The Joker", ["Joker"]),
        ("Wonder Woman", ["Diana Prince"]),
    ],
    "Anime": [
        ("Naruto Uzumaki", ["Naruto"]),
        ("Sasuke Uchiha", ["Sasuke"]),
        ("Goku", ["Son Goku", "Kakarot"]),
        ("Vegeta", []),
        ("Monkey D. Luffy", ["Luffy"]),
        ("Light Yagami", ["Light"]),
        ("Lelouch Lamperouge", ["Lelouch"]),
        ("Eren Yeager", ["Eren"]),
        ("Mikasa Ackerman", ["Mikasa"]),
        ("Spike Spiegel", ["Spike"]),
        ("Edward Elric", ["Ed"]),
        ("Alphonse Elric", ["Al"]),
        ("Sailor Moon", ["Usagi Tsukino"]),
        ("Ichigo Kurosaki", ["Ichigo"]),
        ("Levi Ackerman", ["Levi"]),
        ("Saitama", ["Caped Baldy"]),
        ("Tanjiro Kamado", ["Tanjiro"]),
        ("Gon Freecss", ["Gon"]),
        ("Killua Zoldyck", ["Killua"]),
        ("Asuka Langley", ["Asuka"]),
    ],
    "Historical": [
        ("Cleopatra", ["Cleopatra VII"]),
        ("Julius Caesar", ["Caesar"]),
        ("Alexander the Great", ["Alexander"]),
        ("Napoleon Bonaparte", ["Napoleon"]),
        ("Joan of Arc", []),
        ("Genghis Khan", []),
        ("Queen Elizabeth I", ["Elizabeth I"]),
        ("Abraham Lincoln", ["Lincoln"]),
        ("Mahatma Gandhi", ["Gandhi"]),
        ("Winston Churchill", ["Churchill"]),
        ("Hatshepsut", []),
        ("Tutankhamun", ["King Tut"]),
        ("Leonardo da Vinci", ["da Vinci"]),
        ("Michelangelo", []),
        ("William Shakespeare", ["Shakespeare"]),
        ("Socrates", []),
        ("Confucius", []),
        ("Harriet Tubman", []),
        ("Nelson Mandela", ["Mandela"]),
        ("Martin Luther King Jr.", ["MLK", "Martin Luther King"]),
    ],
    "Gaming": [
        ("Mario", ["Super Mario"]),
        ("Luigi", []),
        ("Link", []),
        ("Zelda", ["Princess Zelda"]),
        ("Master Chief", ["John-117"]),
        ("Lara Croft", []),
        ("Sonic the Hedgehog", ["Sonic"]),
        ("Pikachu", []),
        ("Cloud Strife", ["Cloud"]),
        ("Geralt of Rivia", ["Geralt"]),
        ("Kratos", ["God of War"]),
        ("Aloy", []),
        ("Solid Snake", ["Snake"]),
        ("Samus Aran", ["Samus"]),
        ("Pac-Man", ["Pacman"]),
        ("Steve", ["Minecraft Steve"]),
        ("Tracer", ["Lena Oxton"]),
        ("Joel Miller", ["Joel"]),
        ("Ellie", ["Ellie Williams"]),
        ("Commander Shepard", ["Shepard"]),
    ],
    "Music": [
        ("Beyoncé", ["Beyonce"]),
        ("Taylor Swift", []),
        ("Michael Jackson", ["King of Pop"]),
        ("Elvis Presley", ["Elvis"]),
        ("Madonna", []),
        ("The Beatles", ["Beatles"]),
        ("Freddie Mercury", []),
        ("Bob Dylan", ["Dylan"]),
        ("Aretha Franklin", []),
        ("Eminem", ["Marshall Mathers", "Slim Shady"]),
        ("Drake", []),
        ("Rihanna", []),
        ("David Bowie", ["Bowie"]),
        ("Prince", []),
        ("Whitney Houston", []),
        ("Adele", []),
        ("Ed Sheeran", []),
        ("Billie Eilish", []),
        ("Mozart", ["Wolfgang Amadeus Mozart"]),
        ("Beethoven", ["Ludwig van Beethoven"]),
    ],
    "Literature": [
        ("Harry Dresden", []),
        ("Holden Caulfield", []),
        ("Elizabeth Bennet", ["Lizzy Bennet"]),
        ("Jay Gatsby", ["Gatsby"]),
        ("Atticus Finch", []),
        ("Huckleberry Finn", ["Huck Finn"]),
        ("Jane Eyre", []),
        ("Don Quixote", []),
        ("Odysseus", ["Ulysses"]),
        ("Anna Karenina", []),
        ("Heathcliff", []),
        ("Dorian Gray", []),
        ("Lisbeth Salander", []),
        ("Ender Wiggin", ["Ender"]),
        ("Paul Atreides", ["Muad'Dib"]),
        ("Tyrion Lannister", ["Tyrion"]),
        ("Bilbo Baggins", ["Bilbo"]),
        ("Scout Finch", []),
        ("Pip", ["Philip Pirrip"]),
        ("Ahab", ["Captain Ahab"]),
    ],
    "TV": [
        ("Walter White", ["Heisenberg"]),
        ("Jesse Pinkman", ["Jesse"]),
        ("Daenerys Targaryen", ["Khaleesi", "Dany"]),
        ("Jon Snow", []),
        ("Eleven", ["Jane Hopper", "El"]),
        ("Michael Scott", []),
        ("Dwight Schrute", ["Dwight"]),
        ("Rachel Green", []),
        ("Chandler Bing", ["Chandler"]),
        ("Homer Simpson", ["Homer"]),
        ("Lisa Simpson", []),
        ("Tony Soprano", []),
        ("Carrie Bradshaw", []),
        ("Doctor Who", ["The Doctor"]),
        ("Dana Scully", ["Scully"]),
        ("Fox Mulder", ["Mulder"]),
        ("Rick Sanchez", ["Rick"]),
        ("Morty Smith", ["Morty"]),
        ("Omar Little", ["Omar"]),
        ("Stringer Bell", []),
    ],
    "Comics": [
        ("Spider-Man", ["Peter Parker", "Spiderman"]),
        ("Batman", ["Bruce Wayne"]),
        ("Superman", ["Clark Kent", "Kal-El"]),
        ("Nightwing", ["Dick Grayson"]),
        ("Black Panther", ["T'Challa"]),
        ("Captain America", ["Steve Rogers"]),
        ("Thor", []),
        ("Hulk", ["Bruce Banner"]),
        ("Deadpool", ["Wade Wilson"]),
        ("Wolverine", ["Logan"]),
        ("Storm", ["Ororo Munroe"]),
        ("Jean Grey", ["Phoenix"]),
        ("Doctor Strange", ["Stephen Strange"]),
        ("Scarlet Witch", ["Wanda Maximoff"]),
        ("Black Widow", ["Natasha Romanoff"]),
        ("Flash", ["Barry Allen"]),
        ("Aquaman", ["Arthur Curry"]),
        ("Green Lantern", ["Hal Jordan"]),
        ("Harley Quinn", []),
        ("Catwoman", ["Selina Kyle"]),
    ],
    "Business": [
        ("Elon Musk", ["Musk"]),
        ("Jeff Bezos", ["Bezos"]),
        ("Bill Gates", ["Gates"]),
        ("Steve Jobs", ["Jobs"]),
        ("Oprah Winfrey", ["Oprah"]),
        ("Warren Buffett", ["Buffett"]),
        ("Mark Zuckerberg", ["Zuckerberg", "Zuck"]),
        ("Sundar Pichai", ["Pichai"]),
        ("Satya Nadella", ["Nadella"]),
        ("Indra Nooyi", []),
        ("Sheryl Sandberg", []),
        ("Jack Ma", []),
        ("Larry Page", []),
        ("Sergey Brin", []),
        ("Tim Cook", []),
        ("Reed Hastings", []),
        ("Brian Chesky", []),
        ("Whitney Wolfe Herd", []),
        ("Madam C.J. Walker", ["CJ Walker"]),
        ("Andrew Carnegie", ["Carnegie"]),
    ],
    "Politics": [
        ("Barack Obama", ["Obama"]),
        ("Angela Merkel", ["Merkel"]),
        ("Jacinda Ardern", ["Ardern"]),
        ("Volodymyr Zelenskyy", ["Zelensky", "Zelenskyy"]),
        ("Narendra Modi", ["Modi"]),
        ("Joe Biden", ["Biden"]),
        ("Kamala Harris", ["Harris"]),
        ("Justin Trudeau", ["Trudeau"]),
        ("Margaret Thatcher", ["Thatcher", "Iron Lady"]),
        ("Franklin D. Roosevelt", ["FDR", "Roosevelt"]),
        ("John F. Kennedy", ["JFK", "Kennedy"]),
        ("Indira Gandhi", []),
        ("Golda Meir", []),
        ("Cyrus the Great", []),
        ("Aung San Suu Kyi", []),
        ("Emmanuel Macron", ["Macron"]),
        ("Xi Jinping", []),
        ("Vladimir Putin", ["Putin"]),
        ("Rishi Sunak", ["Sunak"]),
        ("Alexandria Ocasio-Cortez", ["AOC"]),
    ],
}

FIRST = [
    "Alex", "Jordan", "Sam", "Riley", "Casey", "Avery", "Quinn", "Morgan", "Jamie", "Taylor",
    "Cameron", "Drew", "Reese", "Skyler", "Harper", "Parker", "Rowan", "Blake", "Finley", "Hayden",
    "Kai", "Noah", "Liam", "Emma", "Olivia", "Sophia", "Mia", "Lucas", "Ethan", "Aria",
    "Nora", "Leo", "Iris", "Owen", "Clara", "Miles", "Elena", "Felix", "Nina", "Hugo",
]
LAST = [
    "Vance", "Cole", "Brooks", "Hayes", "Reed", "Ford", "Lane", "West", "Stone", "Wilder",
    "Ash", "Blair", "Cross", "Dale", "Frost", "Glen", "Hart", "Ivy", "Jade", "Kade",
    "Lake", "Moss", "Nash", "Pike", "Quill", "Raven", "Sage", "Thorpe", "Vale", "Wynn",
    "York", "Zell", "Arrow", "Bright", "Cloud", "Dawn", "Echo", "Flint", "Grove", "Harbor",
]

QUESTIONS = [
    ("Is this character fictional?", "meta"),
    ("Is this a real person?", "meta"),
    ("Is this person alive today?", "bio"),
    ("Is this associated with movies?", "media"),
    ("Is this from anime or manga?", "media"),
    ("Is this from a video game?", "media"),
    ("Is this from television?", "media"),
    ("Is this from comics or superhero media?", "media"),
    ("Is this an athlete or sports figure?", "domain"),
    ("Is this a scientist or inventor?", "domain"),
    ("Is this a historical figure from before 1900?", "domain"),
    ("Is this known for music?", "domain"),
    ("Is this known for literature or writing?", "domain"),
    ("Is this a political leader?", "domain"),
    ("Is this known for business or technology entrepreneurship?", "domain"),
    ("Is this character primarily a hero / protagonist?", "traits"),
    ("Is this character a villain or antagonist?", "traits"),
    ("Is this associated with magic or fantasy?", "traits"),
    ("Is this associated with science fiction?", "traits"),
    ("Is this person/character from Asia?", "origin"),
    ("Is this person/character from Europe?", "origin"),
    ("Is this person/character from the Americas?", "origin"),
    ("Is this primarily known in the 21st century?", "era"),
    ("Is this primarily known from the 20th century?", "era"),
    ("Does this character wear a costume or mask?", "traits"),
    ("Is this a child or teenager (in their main story)?", "traits"),
    ("Is this known for winning major awards or titles?", "fame"),
    ("Is this associated with space or astronomy?", "domain"),
    ("Is this associated with war or military leadership?", "domain"),
    ("Is this a member of a famous team or group?", "traits"),
]

# category -> question text -> default likelihood
RULES: dict[str, dict[str, float]] = {
    "Scientists": {
        "Is this a real person?": 0.95,
        "Is this character fictional?": 0.05,
        "Is this a scientist or inventor?": 0.95,
        "Is this associated with movies?": 0.15,
        "Is this from anime or manga?": 0.02,
        "Is this from a video game?": 0.02,
        "Is this an athlete or sports figure?": 0.05,
        "Is this associated with science fiction?": 0.25,
        "Is this associated with space or astronomy?": 0.45,
    },
    "Sports": {
        "Is this a real person?": 0.95,
        "Is this character fictional?": 0.05,
        "Is this an athlete or sports figure?": 0.97,
        "Is this person alive today?": 0.7,
        "Is this known for winning major awards or titles?": 0.75,
        "Is this a scientist or inventor?": 0.05,
    },
    "Movies": {
        "Is this character fictional?": 0.9,
        "Is this a real person?": 0.15,
        "Is this associated with movies?": 0.95,
        "Is this from television?": 0.25,
        "Is this from anime or manga?": 0.05,
        "Is this from a video game?": 0.1,
    },
    "Anime": {
        "Is this character fictional?": 0.97,
        "Is this a real person?": 0.03,
        "Is this from anime or manga?": 0.97,
        "Is this associated with movies?": 0.35,
        "Is this person/character from Asia?": 0.85,
        "Is this associated with magic or fantasy?": 0.55,
    },
    "Historical": {
        "Is this a real person?": 0.97,
        "Is this character fictional?": 0.05,
        "Is this a historical figure from before 1900?": 0.75,
        "Is this person alive today?": 0.05,
        "Is this associated with war or military leadership?": 0.45,
    },
    "Gaming": {
        "Is this character fictional?": 0.95,
        "Is this a real person?": 0.05,
        "Is this from a video game?": 0.97,
        "Is this associated with movies?": 0.3,
        "Does this character wear a costume or mask?": 0.4,
    },
    "Music": {
        "Is this a real person?": 0.9,
        "Is this character fictional?": 0.1,
        "Is this known for music?": 0.97,
        "Is this primarily known in the 21st century?": 0.45,
    },
    "Literature": {
        "Is this character fictional?": 0.85,
        "Is this a real person?": 0.2,
        "Is this known for literature or writing?": 0.7,
        "Is this associated with magic or fantasy?": 0.4,
    },
    "TV": {
        "Is this character fictional?": 0.9,
        "Is this from television?": 0.95,
        "Is this associated with movies?": 0.3,
    },
    "Comics": {
        "Is this character fictional?": 0.97,
        "Is this from comics or superhero media?": 0.97,
        "Does this character wear a costume or mask?": 0.8,
        "Is this associated with movies?": 0.7,
    },
    "Business": {
        "Is this a real person?": 0.97,
        "Is this character fictional?": 0.03,
        "Is this known for business or technology entrepreneurship?": 0.95,
        "Is this person alive today?": 0.75,
    },
    "Politics": {
        "Is this a real person?": 0.97,
        "Is this character fictional?": 0.03,
        "Is this a political leader?": 0.95,
        "Is this person alive today?": 0.65,
    },
}


def _expand_to_target(target: int = 520) -> list[dict]:
    seen_names: set[str] = set()
    characters: list[dict] = []

    def add(name: str, category: str, aliases: list[str]) -> None:
        key = name.casefold().strip()
        if not key or key in seen_names:
            return
        clean_aliases = []
        alias_seen = set()
        for a in aliases:
            ak = a.casefold().strip()
            if not ak or ak == key or ak in seen_names or ak in alias_seen:
                continue
            alias_seen.add(ak)
            clean_aliases.append(a.strip())
        seen_names.add(key)
        for a in clean_aliases:
            seen_names.add(a.casefold())
        characters.append(
            {
                "name": name.strip(),
                "category": category,
                "aliases": clean_aliases,
                "is_active": True,
            }
        )

    for category, rows in BASE.items():
        for name, aliases in rows:
            add(name, category, aliases)

    # Programmatic fillers to reach 500+ while staying category-tagged
    idx = 0
    cats = list(CATEGORIES)
    pool = len(FIRST) * len(LAST)
    while len(characters) < target:
        category = cats[len(characters) % len(cats)]
        first = FIRST[idx % len(FIRST)]
        last = LAST[(idx // len(FIRST)) % len(LAST)]
        cycle = idx // pool
        name = f"{first} {last}" if cycle == 0 else f"{first} {last} {cycle + 1}"
        aliases = [f"{first[0]}. {last}"] if cycle == 0 else [f"{first[0]}. {last} {cycle + 1}"]
        add(name, category, aliases)
        idx += 1
        if idx > target * 5:
            break

    return characters


def build_seed() -> dict:
    characters = _expand_to_target(520)
    questions = [
        {"text": text, "category": cat, "is_active": True} for text, cat in QUESTIONS
    ]
    overrides = [
        {
            "character": "Albert Einstein",
            "question": "Is this a scientist or inventor?",
            "likelihood": 0.99,
            "sample_size": 100,
        },
        {
            "character": "Lionel Messi",
            "question": "Is this an athlete or sports figure?",
            "likelihood": 0.99,
            "sample_size": 100,
        },
        {
            "character": "Mario",
            "question": "Is this from a video game?",
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Naruto Uzumaki",
            "question": "Is this from anime or manga?",
            "likelihood": 0.99,
            "sample_size": 80,
        },
        {
            "character": "Darth Vader",
            "question": "Is this character a villain or antagonist?",
            "likelihood": 0.95,
            "sample_size": 80,
        },
    ]
    return {
        "version": 1,
        "categories": CATEGORIES,
        "characters": characters,
        "questions": questions,
        "likelihood_rules": [
            {"category": cat, "question": q, "likelihood": lik, "sample_size": 40}
            for cat, mapping in RULES.items()
            for q, lik in mapping.items()
        ],
        "likelihood_overrides": overrides,
        "default_likelihood": 0.5,
        "default_sample_size": 10,
    }


def main() -> None:
    seed = build_seed()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(seed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT} with {len(seed['characters'])} characters, "
        f"{len(seed['questions'])} questions, "
        f"{len(seed['likelihood_rules'])} rules."
    )


if __name__ == "__main__":
    main()
