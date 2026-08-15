"""Regression: Indian women cricketers stay in the candidate pool.

Smriti Mandhana must not vanish after correct answers, and a foreign
athlete such as Nadia Comăneci must not dominate that path.
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


SMRITI = uuid4()
NADIA = uuid4()
KOHLI = uuid4()
MESSI = uuid4()
MITHALI = uuid4()

Q_REAL = uuid4()
Q_ALIVE = uuid4()
Q_WOMAN = uuid4()
Q_INDIA = uuid4()
Q_SPORTS = uuid4()
Q_CRICKET = uuid4()

_KEEP = {
    "Smriti Mandhana",
    "Mithali Raj",
    "Harmanpreet Kaur",
    "Jemimah Rodrigues",
    "Virat Kohli",
    "MS Dhoni",
    "Sachin Tendulkar",
    "Rohit Sharma",
    "Lionel Messi",
    "Nadia Comăneci",
    "Naruto Uzumaki",
    "Batman",
}


def _L(v: float, n: int = 80) -> LikelihoodEntry:
    return LikelihoodEntry(v, n)


def _sports_catalog():
    """Same L conventions as Kohli / Messi trait overrides."""
    chars = [SMRITI, NADIA, KOHLI, MESSI, MITHALI]
    likelihoods = {}
    # Real / alive
    for cid in chars:
        likelihoods[(cid, Q_REAL)] = _L(0.96)
        likelihoods[(cid, Q_ALIVE)] = _L(0.92)
    # Gender
    likelihoods[(SMRITI, Q_WOMAN)] = _L(0.95)
    likelihoods[(MITHALI, Q_WOMAN)] = _L(0.95)
    likelihoods[(NADIA, Q_WOMAN)] = _L(0.95)
    likelihoods[(KOHLI, Q_WOMAN)] = _L(0.06)
    likelihoods[(MESSI, Q_WOMAN)] = _L(0.06)
    # India
    likelihoods[(SMRITI, Q_INDIA)] = _L(0.96)
    likelihoods[(MITHALI, Q_INDIA)] = _L(0.96)
    likelihoods[(KOHLI, Q_INDIA)] = _L(0.96)
    likelihoods[(NADIA, Q_INDIA)] = _L(0.08)
    likelihoods[(MESSI, Q_INDIA)] = _L(0.08)
    # Sports
    for cid in chars:
        likelihoods[(cid, Q_SPORTS)] = _L(0.97)
    # Cricket
    likelihoods[(SMRITI, Q_CRICKET)] = _L(0.96)
    likelihoods[(MITHALI, Q_CRICKET)] = _L(0.96)
    likelihoods[(KOHLI, Q_CRICKET)] = _L(0.96)
    likelihoods[(NADIA, Q_CRICKET)] = _L(0.08)
    likelihoods[(MESSI, Q_CRICKET)] = _L(0.10)
    return chars, likelihoods


def _play(steps: list[tuple[UUID, str]], *, popularity: dict[UUID, int] | None = None):
    chars, Lmap = _sports_catalog()
    pop = popularity or {
        SMRITI: 93,
        NADIA: 100,  # higher prior must not beat evidence
        KOHLI: 100,
        MESSI: 100,
        MITHALI: 88,
    }
    state = create_initial_state(chars, Lmap, popularity=pop)
    snapshots = []
    for qid, ans in steps:
        state, _ = process_answer(state, qid, ans)
        ranked = sorted(state.probabilities.items(), key=lambda x: -x[1])
        snapshots.append(
            {
                "count": len(state.probabilities),
                "p_smriti": state.probabilities.get(SMRITI, 0.0),
                "top": [cid for cid, _ in ranked[:5]],
            }
        )
    ranked = sorted(state.probabilities.items(), key=lambda x: -x[1])
    return state, ranked, snapshots


def test_smriti_exists_in_active_seed():
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    row = next((c for c in seed["characters"] if c["name"] == "Smriti Mandhana"), None)
    assert row is not None
    assert row["category"] == "Sports"
    assert row.get("is_active", True) is True
    assert int(row.get("popularity_score", 0)) >= popularity_for("Smriti Mandhana")
    aliases = {a.casefold() for a in (row.get("aliases") or [])}
    assert "mandhana" in aliases
    assert "smriti" in aliases


def test_smriti_metadata_matches_conventions():
    traits = traits_for("Smriti Mandhana", "Sports")
    assert traits is not None
    assert traits.real is True
    assert traits.alive is True
    assert traits.female is True
    assert "india" in traits.regions
    assert "cricket" in traits.sports


def test_smriti_has_required_likelihood_mappings():
    questions = [
        "Is your character a real person?",
        "Is your character still alive?",
        "Is your character a woman?",
        "Is your character from India?",
        "Is your character an athlete?",
        "Does your character play cricket?",
    ]
    by_q = {row["question"]: row for row in overrides_for_character("Smriti Mandhana", questions, category="Sports")}
    assert by_q["Is your character a real person?"]["likelihood"] >= 0.9
    assert by_q["Is your character still alive?"]["likelihood"] >= 0.9
    assert by_q["Is your character a woman?"]["likelihood"] >= 0.9
    assert by_q["Is your character from India?"]["likelihood"] >= 0.9
    assert by_q["Is your character an athlete?"]["likelihood"] >= 0.9
    assert by_q["Does your character play cricket?"]["likelihood"] >= 0.9

    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    indexed = {
        (o["character"].casefold(), o["question"].casefold()): float(o["likelihood"])
        for o in seed.get("likelihood_overrides") or []
    }
    assert indexed[("smriti mandhana", "is your character from india?")] >= 0.9
    assert indexed[("smriti mandhana", "does your character play cricket?")] >= 0.9
    assert indexed[("smriti mandhana", "is your character a woman?")] >= 0.9


def test_india_yes_favors_smriti_over_foreign_athletes():
    state, ranked, _ = _play([(Q_INDIA, "yes")])
    assert SMRITI in state.probabilities
    assert NADIA not in state.probabilities
    assert MESSI not in state.probabilities
    names_ahead = [cid for cid, _ in ranked if state.probabilities[cid] >= state.probabilities[SMRITI]]
    assert SMRITI in names_ahead


def test_sports_yes_keeps_smriti_eligible():
    state, _, snaps = _play([(Q_SPORTS, "yes")])
    assert SMRITI in state.probabilities
    assert snaps[-1]["p_smriti"] > 0
    assert snaps[-1]["count"] >= 1


def test_cricket_yes_strongly_favors_smriti():
    state, ranked, _ = _play([(Q_SPORTS, "yes"), (Q_CRICKET, "yes")])
    assert SMRITI in state.probabilities
    assert NADIA not in state.probabilities
    cricket_ids = {SMRITI, KOHLI, MITHALI}
    assert set(state.probabilities) <= cricket_ids
    assert ranked[0][0] in cricket_ids


def test_female_yes_keeps_smriti_and_drops_male_stars():
    state, _, _ = _play([(Q_WOMAN, "yes")])
    assert SMRITI in state.probabilities
    assert KOHLI not in state.probabilities
    assert MESSI not in state.probabilities


def test_smriti_is_top_on_matching_path():
    state, ranked, snaps = _play(
        [
            (Q_REAL, "yes"),
            (Q_ALIVE, "yes"),
            (Q_WOMAN, "yes"),
            (Q_INDIA, "yes"),
            (Q_SPORTS, "yes"),
            (Q_CRICKET, "yes"),
        ]
    )
    for snap in snaps:
        assert snap["p_smriti"] > 0, "Smriti disappeared after a correct answer"
    assert SMRITI in state.probabilities
    assert ranked[0][0] == SMRITI
    assert state.probabilities[SMRITI] >= 0.35
    assert NADIA not in state.probabilities


def test_nadia_does_not_dominate_smriti_path():
    state, ranked, _ = _play(
        [
            (Q_REAL, "yes"),
            (Q_WOMAN, "yes"),
            (Q_INDIA, "yes"),
            (Q_SPORTS, "yes"),
            (Q_CRICKET, "yes"),
        ]
    )
    assert ranked[0][0] != NADIA
    assert NADIA not in state.probabilities
    assert ranked[0][0] == SMRITI


def test_smriti_appears_in_wrong_guess_recovery():
    state, _, _ = _play(
        [
            (Q_REAL, "yes"),
            (Q_ALIVE, "yes"),
            (Q_WOMAN, "yes"),
            (Q_INDIA, "yes"),
            (Q_SPORTS, "yes"),
            (Q_CRICKET, "yes"),
        ]
    )
    names = {
        SMRITI: "Smriti Mandhana",
        NADIA: "Nadia Comăneci",
        KOHLI: "Virat Kohli",
        MESSI: "Lionel Messi",
        MITHALI: "Mithali Raj",
    }
    cats = {cid: "Sports" for cid in names}
    rows = remaining_candidates(
        state.probabilities,
        names,
        cats,
        category="Sports",
        exclude_ids={NADIA},
    )
    assert rows, "recovery must not be empty while plausible candidates remain"
    recovered = {r["name"] for r in rows}
    assert "Smriti Mandhana" in recovered
    assert "Nadia Comăneci" not in recovered


def _qid(snap, *needles: str) -> UUID:
    wanted = [n.casefold() for n in needles]
    for qid, ref in snap.question_refs.items():
        text = ref.text.casefold()
        if all(n in text for n in wanted):
            return qid
    raise AssertionError(f"No question matching {needles}")


def _by_name(snap) -> dict[str, UUID]:
    return {name.casefold(): cid for cid, name in snap.character_names.items()}


@pytest.fixture(scope="module")
def smriti_seed_snapshot():
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    want = {n.casefold() for n in _KEEP}
    subset = dict(data)
    subset["characters"] = [c for c in data["characters"] if c["name"].casefold() in want]
    names = {c["name"] for c in subset["characters"]}
    assert "Smriti Mandhana" in names
    snap = snapshot_from_seed_dict(subset)
    pop = {}
    for row in subset["characters"]:
        cid = _by_name(snap)[row["name"].casefold()]
        pop[cid] = int(row.get("popularity_score") or 0)
    # Give Nadia a high prior so evidence, not popularity, must win.
    nadia_id = _by_name(snap).get("nadia comăneci")
    if nadia_id is not None:
        pop[nadia_id] = 100
    return snap, pop


def test_seed_path_keeps_smriti_and_rejects_nadia(smriti_seed_snapshot):
    snap, pop = smriti_seed_snapshot
    ids = _by_name(snap)
    smriti = ids["smriti mandhana"]
    nadia = ids["nadia comăneci"]
    q_real = _qid(snap, "real person")
    q_alive = _qid(snap, "still alive")
    q_woman = _qid(snap, "a woman")
    q_india = _qid(snap, "from india")
    q_sports = _qid(snap, "an athlete")
    q_cricket = _qid(snap, "play cricket")

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
        (q_cricket, "yes"),
    ]:
        state, _ = process_answer(state, qid, ans)
        assert smriti in state.probabilities, "Smriti disappeared after a correct seed answer"

    ranked = sorted(state.probabilities.items(), key=lambda x: -x[1])
    assert ranked[0][0] == smriti
    assert nadia not in state.probabilities
    # Peers (Mithali, Harmanpreet, Jemimah) share mass; Smriti must still lead.
    assert state.probabilities[smriti] >= 0.2
    assert state.probabilities[smriti] > ranked[1][1]

    rows = remaining_candidates(
        state.probabilities,
        snap.character_names,
        snap.character_categories,
        category="Sports",
        exclude_ids={nadia},
        q="Mandhana",
    )
    assert rows
    assert rows[0]["name"] == "Smriti Mandhana"
