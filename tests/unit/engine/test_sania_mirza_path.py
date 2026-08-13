"""Regression: Indian women tennis players stay in the candidate pool.

Sania Mirza must not vanish after correct answers, and a foreign
tennis player such as Aryna Sabalenka must not dominate that path.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import UUID, uuid4

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
SEED_PATH = ROOT / "data" / "knowledge" / "seed_v1.json"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from character_popularity import popularity_for  # noqa: E402
from character_trait_priors import overrides_for_character, traits_for  # noqa: E402

from app.engine.explain import remaining_candidates
from app.engine.models import LikelihoodEntry
from app.engine.selector import create_initial_state, process_answer
from app.training.simulator import snapshot_from_seed_dict


SANIA = uuid4()
SABALENKA = uuid4()
KOHLI = uuid4()
MESSI = uuid4()
SERENA = uuid4()
SMRITI = uuid4()

Q_REAL = uuid4()
Q_ALIVE = uuid4()
Q_WOMAN = uuid4()
Q_INDIA = uuid4()
Q_SPORTS = uuid4()
Q_TENNIS = uuid4()

_KEEP = {
    "Sania Mirza",
    "Aryna Sabalenka",
    "Serena Williams",
    "Smriti Mandhana",
    "Virat Kohli",
    "Lionel Messi",
    "Naruto Uzumaki",
    "Batman",
}


def _L(v: float, n: int = 80) -> LikelihoodEntry:
    return LikelihoodEntry(v, n)


def _sports_catalog():
    """Same L conventions as Kohli / Smriti / Messi trait overrides."""
    chars = [SANIA, SABALENKA, KOHLI, MESSI, SERENA, SMRITI]
    likelihoods = {}
    for cid in chars:
        likelihoods[(cid, Q_REAL)] = _L(0.96)
        likelihoods[(cid, Q_ALIVE)] = _L(0.92)
        likelihoods[(cid, Q_SPORTS)] = _L(0.97)
    likelihoods[(SANIA, Q_WOMAN)] = _L(0.95)
    likelihoods[(SABALENKA, Q_WOMAN)] = _L(0.95)
    likelihoods[(SERENA, Q_WOMAN)] = _L(0.95)
    likelihoods[(SMRITI, Q_WOMAN)] = _L(0.95)
    likelihoods[(KOHLI, Q_WOMAN)] = _L(0.06)
    likelihoods[(MESSI, Q_WOMAN)] = _L(0.06)
    likelihoods[(SANIA, Q_INDIA)] = _L(0.96)
    likelihoods[(SMRITI, Q_INDIA)] = _L(0.96)
    likelihoods[(KOHLI, Q_INDIA)] = _L(0.96)
    likelihoods[(SABALENKA, Q_INDIA)] = _L(0.08)
    likelihoods[(SERENA, Q_INDIA)] = _L(0.08)
    likelihoods[(MESSI, Q_INDIA)] = _L(0.08)
    likelihoods[(SANIA, Q_TENNIS)] = _L(0.96)
    likelihoods[(SABALENKA, Q_TENNIS)] = _L(0.96)
    likelihoods[(SERENA, Q_TENNIS)] = _L(0.96)
    likelihoods[(SMRITI, Q_TENNIS)] = _L(0.08)
    likelihoods[(KOHLI, Q_TENNIS)] = _L(0.08)
    likelihoods[(MESSI, Q_TENNIS)] = _L(0.08)
    return chars, likelihoods


def _play(steps: list[tuple[UUID, str]], *, popularity: dict[UUID, int] | None = None):
    chars, Lmap = _sports_catalog()
    pop = popularity or {
        SANIA: 90,
        SABALENKA: 100,  # higher prior must not beat evidence
        SERENA: 99,
        KOHLI: 100,
        MESSI: 100,
        SMRITI: 93,
    }
    state = create_initial_state(chars, Lmap, popularity=pop)
    snapshots = []
    for qid, ans in steps:
        state, _ = process_answer(state, qid, ans)
        ranked = sorted(state.probabilities.items(), key=lambda x: -x[1])
        snapshots.append(
            {
                "count": len(state.probabilities),
                "p_sania": state.probabilities.get(SANIA, 0.0),
                "top": [cid for cid, _ in ranked[:5]],
            }
        )
    ranked = sorted(state.probabilities.items(), key=lambda x: -x[1])
    return state, ranked, snapshots


def test_sania_exists_in_active_seed():
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    row = next((c for c in seed["characters"] if c["name"] == "Sania Mirza"), None)
    assert row is not None
    assert row["category"] == "Sports"
    assert row.get("is_active", True) is True
    assert int(row.get("popularity_score", 0)) >= popularity_for("Sania Mirza")


def test_sania_aliases_resolve_searches():
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    row = next((c for c in seed["characters"] if c["name"] == "Sania Mirza"), None)
    assert row is not None
    aliases = {a.casefold() for a in (row.get("aliases") or [])}
    assert "sania" in aliases
    assert "mirza" in aliases
    name = row["name"].casefold()
    assert "sania mirza" == name
    assert "sania" in name
    # Phrase search is covered by name + tennis alias tokens, not a frontend hardcode.
    assert "sania" in aliases and row["category"] == "Sports"


def test_sania_metadata_matches_conventions():
    traits = traits_for("Sania Mirza", "Sports")
    assert traits is not None
    assert traits.real is True
    assert traits.alive is True
    assert traits.female is True
    assert "india" in traits.regions
    assert "tennis" in traits.sports


def test_sania_has_required_likelihood_mappings():
    questions = [
        "Is your character a real person?",
        "Is your character still alive?",
        "Is your character a woman?",
        "Is your character from India?",
        "Is your character an athlete?",
        "Does your character play tennis?",
    ]
    by_q = {
        row["question"]: row
        for row in overrides_for_character("Sania Mirza", questions, category="Sports")
    }
    assert by_q["Is your character a real person?"]["likelihood"] >= 0.9
    assert by_q["Is your character still alive?"]["likelihood"] >= 0.9
    assert by_q["Is your character a woman?"]["likelihood"] >= 0.9
    assert by_q["Is your character from India?"]["likelihood"] >= 0.9
    assert by_q["Is your character an athlete?"]["likelihood"] >= 0.9
    assert by_q["Does your character play tennis?"]["likelihood"] >= 0.9

    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    indexed = {
        (o["character"].casefold(), o["question"].casefold()): float(o["likelihood"])
        for o in seed.get("likelihood_overrides") or []
    }
    assert indexed[("sania mirza", "is your character from india?")] >= 0.9
    assert indexed[("sania mirza", "does your character play tennis?")] >= 0.9
    assert indexed[("sania mirza", "is your character a woman?")] >= 0.9


def test_india_yes_keeps_sania_eligible():
    state, _, snaps = _play([(Q_INDIA, "yes")])
    assert SANIA in state.probabilities
    assert SABALENKA not in state.probabilities
    assert MESSI not in state.probabilities
    assert snaps[-1]["p_sania"] > 0


def test_sports_yes_keeps_sania_eligible():
    state, _, snaps = _play([(Q_SPORTS, "yes")])
    assert SANIA in state.probabilities
    assert snaps[-1]["p_sania"] > 0


def test_tennis_yes_strongly_favors_sania():
    state, ranked, _ = _play([(Q_SPORTS, "yes"), (Q_TENNIS, "yes")])
    assert SANIA in state.probabilities
    tennis_ids = {SANIA, SABALENKA, SERENA}
    assert set(state.probabilities) <= tennis_ids
    assert ranked[0][0] in tennis_ids


def test_female_yes_keeps_sania_eligible():
    state, _, _ = _play([(Q_WOMAN, "yes")])
    assert SANIA in state.probabilities
    assert KOHLI not in state.probabilities
    assert MESSI not in state.probabilities


def test_sania_is_top_on_matching_path():
    state, ranked, snaps = _play(
        [
            (Q_REAL, "yes"),
            (Q_ALIVE, "yes"),
            (Q_WOMAN, "yes"),
            (Q_INDIA, "yes"),
            (Q_SPORTS, "yes"),
            (Q_TENNIS, "yes"),
        ]
    )
    for snap in snaps:
        assert snap["p_sania"] > 0, "Sania disappeared after a correct answer"
    assert SANIA in state.probabilities
    assert ranked[0][0] == SANIA
    assert state.probabilities[SANIA] >= 0.35
    assert SABALENKA not in state.probabilities


def test_sabalenka_does_not_dominate_sania_path():
    state, ranked, _ = _play(
        [
            (Q_REAL, "yes"),
            (Q_WOMAN, "yes"),
            (Q_INDIA, "yes"),
            (Q_SPORTS, "yes"),
            (Q_TENNIS, "yes"),
        ]
    )
    assert ranked[0][0] != SABALENKA
    assert SABALENKA not in state.probabilities
    assert ranked[0][0] == SANIA


def test_sania_appears_in_wrong_guess_recovery():
    state, _, _ = _play(
        [
            (Q_REAL, "yes"),
            (Q_ALIVE, "yes"),
            (Q_WOMAN, "yes"),
            (Q_INDIA, "yes"),
            (Q_SPORTS, "yes"),
            (Q_TENNIS, "yes"),
        ]
    )
    names = {
        SANIA: "Sania Mirza",
        SABALENKA: "Aryna Sabalenka",
        KOHLI: "Virat Kohli",
        MESSI: "Lionel Messi",
        SERENA: "Serena Williams",
        SMRITI: "Smriti Mandhana",
    }
    cats = {cid: "Sports" for cid in names}
    rows = remaining_candidates(
        state.probabilities,
        names,
        cats,
        category="Sports",
        exclude_ids={SABALENKA},
        q="Sania",
    )
    assert rows, "recovery must not be empty while plausible candidates remain"
    recovered = {r["name"] for r in rows}
    assert "Sania Mirza" in recovered
    assert "Aryna Sabalenka" not in recovered


def _qid(snap, *needles: str) -> UUID:
    wanted = [n.casefold() for n in needles]
    hits: list[tuple[UUID, str]] = []
    for qid, ref in snap.question_refs.items():
        text = ref.text.casefold()
        if all(n in text for n in wanted):
            hits.append((qid, text))
    if not hits:
        raise AssertionError(f"No question matching {needles}")
    hits.sort(key=lambda item: len(item[1]))
    return hits[0][0]


def _by_name(snap) -> dict[str, UUID]:
    return {name.casefold(): cid for cid, name in snap.character_names.items()}


@pytest.fixture(scope="module")
def sania_seed_snapshot():
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    want = {n.casefold() for n in _KEEP}
    subset = dict(data)
    subset["characters"] = [c for c in data["characters"] if c["name"].casefold() in want]
    names = {c["name"] for c in subset["characters"]}
    assert "Sania Mirza" in names
    snap = snapshot_from_seed_dict(subset)
    pop = {}
    for row in subset["characters"]:
        cid = _by_name(snap)[row["name"].casefold()]
        pop[cid] = int(row.get("popularity_score") or 0)
    sabalenka_id = _by_name(snap).get("aryna sabalenka")
    if sabalenka_id is not None:
        pop[sabalenka_id] = 100
    return snap, pop


def test_seed_path_keeps_sania_and_rejects_sabalenka(sania_seed_snapshot):
    snap, pop = sania_seed_snapshot
    ids = _by_name(snap)
    sania = ids["sania mirza"]
    sabalenka = ids["aryna sabalenka"]
    q_real = _qid(snap, "real person")
    q_alive = _qid(snap, "still alive")
    q_woman = _qid(snap, "a woman")
    q_india = _qid(snap, "from india")
    q_sports = _qid(snap, "an athlete")
    q_tennis = _qid(snap, "play tennis")

    state = create_initial_state(
        list(snap.character_ids),
        snap.likelihoods,
        popularity=pop,
    )
    for qid, ans in [
        (q_real, "yes"),
        (q_alive, "yes"),
        (q_woman, "yes"),
        (q_india, "yes"),
        (q_sports, "yes"),
        (q_tennis, "yes"),
    ]:
        state, _ = process_answer(state, qid, ans)
        assert sania in state.probabilities, "Sania disappeared after a correct seed answer"

    ranked = sorted(state.probabilities.items(), key=lambda x: -x[1])
    assert ranked[0][0] == sania
    assert sabalenka not in state.probabilities
    assert state.probabilities[sania] >= 0.2
    if len(ranked) > 1:
        assert state.probabilities[sania] > ranked[1][1]

    rows = remaining_candidates(
        state.probabilities,
        snap.character_names,
        snap.character_categories,
        category="Sports",
        exclude_ids={sabalenka},
        q="Sania",
    )
    assert rows
    assert rows[0]["name"] == "Sania Mirza"
