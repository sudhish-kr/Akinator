"""Category values used by the wrong-guess learning UI.

Stored Character.category values stay untouched. A few learn-screen labels
map onto one existing category or a group of existing categories so the
filter can succeed without inserting new database rows.
"""

from __future__ import annotations

from app.engine.constants import FICTIONAL_CHARACTER_CATEGORIES
from app.engine.question_consistency import REAL_HUMAN_CATEGORIES

# Display-friendly labels that are stored under a different Character.category.
SINGLE_CATEGORY_ALIASES: dict[str, str] = {
    "Science": "Scientists",
    "Politics": "Politicians",
    "Music": "Musicians",
    "Business": "Business Leaders",
    "History": "Historical Figures",
    "TV": "TV Shows",
    "Games": "Gaming",
}

# Learn-screen worlds that are unions of existing stored categories.
GROUP_CATEGORY_ALIASES: dict[str, frozenset[str]] = {
    "Fictional Characters": FICTIONAL_CHARACTER_CATEGORIES,
    "Famous People": REAL_HUMAN_CATEGORIES,
    "Art & Entertainment": frozenset(
        {
            "Movies",
            "TV Shows",
            "Anime",
            "Cartoons",
            "Gaming",
            "Musicians",
            "Literature",
        }
    ),
}


def matching_character_categories(category: str | None) -> frozenset[str] | None:
    """Stored Character.category values that match a learn-filter string.

    None means no category filter. A single-item frozenset is a direct match.
    """
    wanted = (category or "").strip()
    if not wanted:
        return None
    grouped = GROUP_CATEGORY_ALIASES.get(wanted)
    if grouped:
        return grouped
    return frozenset({SINGLE_CATEGORY_ALIASES.get(wanted, wanted)})
