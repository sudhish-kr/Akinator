"""Popular character priority scores for natural gameplay.

Higher scores are suggested first after a wrong guess. Does not change
Bayesian update math — listing / catalog ordering only.
"""

from __future__ import annotations

from knowledge_expansion_v2 import expansion_popularity  # noqa: E402

# name (casefold) → popularity_score
CHARACTER_POPULARITY: dict[str, int] = {
    "virat kohli": 100,
    "ms dhoni": 98,
    "sachin tendulkar": 97,
    "rohit sharma": 95,
    "smriti mandhana": 93,
    "mithali raj": 88,
    "harmanpreet kaur": 87,
    "jemimah rodrigues": 84,
    "sania mirza": 90,
    "lionel messi": 100,
    "cristiano ronaldo": 99,
    "shah rukh khan": 98,
    "amitabh bachchan": 96,
    "narendra modi": 94,
    "albert einstein": 95,
    "isaac newton": 92,
    "harry potter": 98,
    "spider-man": 97,
    "tony stark": 96,
    "iron man": 96,
    "batman": 97,
    "naruto uzumaki": 96,
    "goku": 95,
    "doraemon": 94,
    "shinchan": 93,
    "shin chan": 93,
    "mario": 96,
    "sonic the hedgehog": 92,
}
CHARACTER_POPULARITY.update(expansion_popularity())

# Characters that must exist in the knowledge base (name, category, aliases).
REQUIRED_FAMOUS_CHARACTERS: list[tuple[str, str, list[str]]] = [
    ("Virat Kohli", "Sports", ["Kohli", "King Kohli", "Virat"]),
    ("MS Dhoni", "Sports", ["Dhoni", "Mahendra Singh Dhoni", "MSD", "Mahi"]),
    ("Sachin Tendulkar", "Sports", ["Tendulkar", "Master Blaster"]),
    ("Rohit Sharma", "Sports", ["Rohit", "Hitman"]),
    ("Smriti Mandhana", "Sports", ["Mandhana", "Smriti"]),
    ("Mithali Raj", "Sports", ["Mithali"]),
    ("Harmanpreet Kaur", "Sports", ["Harmanpreet"]),
    ("Jemimah Rodrigues", "Sports", ["Jemimah"]),
    ("Sania Mirza", "Sports", ["Sania", "Mirza"]),
    ("Lionel Messi", "Sports", ["Messi", "Leo Messi"]),
    ("Cristiano Ronaldo", "Sports", ["Ronaldo", "CR7"]),
    ("Shah Rukh Khan", "Movies", ["SRK", "King Khan", "Shahrukh Khan"]),
    ("Amitabh Bachchan", "Movies", ["Big B", "Amitabh"]),
    ("Narendra Modi", "Politicians", ["Modi", "Narendra"]),
    ("Albert Einstein", "Scientists", ["Einstein", "Albert"]),
    ("Isaac Newton", "Scientists", ["Newton", "Sir Isaac Newton"]),
    ("Harry Potter", "Movies", ["Potter", "The Boy Who Lived"]),
    ("Spider-Man", "Movies", ["Spiderman", "Spider Man", "Peter Parker"]),
    ("Tony Stark", "Movies", ["Iron Man", "Stark"]),
    ("Batman", "Movies", ["Bruce Wayne", "The Dark Knight"]),
    ("Naruto Uzumaki", "Anime", ["Naruto", "Seventh Hokage"]),
    ("Goku", "Anime", ["Son Goku", "Kakarot"]),
    ("Doraemon", "Cartoons", ["Doramon"]),
    ("Shinchan", "Cartoons", ["Shin Chan", "Crayon Shin-chan", "Shinnosuke"]),
    ("Mario", "Gaming", ["Super Mario"]),
    ("Sonic the Hedgehog", "Gaming", ["Sonic"]),
]


def popularity_for(name: str) -> int:
    return CHARACTER_POPULARITY.get(name.strip().casefold(), 0)
