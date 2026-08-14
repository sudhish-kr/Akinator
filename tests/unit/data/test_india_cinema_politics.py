"""Regression tests for the Indian cinema and politics knowledge base."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
SEED_PATH = ROOT / "data" / "knowledge" / "seed_v1.json"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from character_popularity import popularity_for  # noqa: E402
from character_trait_priors import overrides_for_character, traits_for  # noqa: E402
from app.engine.models import LikelihoodEntry  # noqa: E402
from app.engine.selector import create_initial_state, process_answer  # noqa: E402


REGRESSION = {
    "Shah Rukh Khan": {
        "category": "Movies",
        "aliases": ["SRK", "Shahrukh Khan"],
        "industries": {"hindi"},
        "roles": {"actor"},
        "female": False,
        "alive": True,
    },
    "Amitabh Bachchan": {
        "category": "Movies",
        "aliases": ["Big B"],
        "industries": {"hindi"},
        "roles": {"actor"},
        "female": False,
        "alive": True,
    },
    "Rajinikanth": {
        "category": "Movies",
        "aliases": ["Rajini"],
        "industries": {"tamil"},
        "roles": {"actor"},
        "female": False,
        "alive": True,
    },
    "Allu Arjun": {
        "category": "Movies",
        "aliases": ["Stylish Star"],
        "industries": {"telugu"},
        "roles": {"actor"},
        "female": False,
        "alive": True,
    },
    "Prabhas": {
        "category": "Movies",
        "aliases": ["Rebel Star"],
        "industries": {"telugu"},
        "roles": {"actor"},
        "female": False,
        "alive": True,
    },
    "Yash": {
        "category": "Movies",
        "aliases": ["Rocking Star Yash"],
        "industries": {"kannada"},
        "roles": {"actor"},
        "female": False,
        "alive": True,
    },
    "Mammootty": {
        "category": "Movies",
        "aliases": ["Mammootty Actor"],
        "industries": {"malayalam"},
        "roles": {"actor"},
        "female": False,
        "alive": True,
    },
    "Mohanlal": {
        "category": "Movies",
        "aliases": ["Lalettan"],
        "industries": {"malayalam"},
        "roles": {"actor"},
        "female": False,
        "alive": True,
    },
    "Diljit Dosanjh": {
        "category": {"Movies", "Musicians"},
        "aliases": ["Diljit"],
        "industries": {"punjabi"},
        "roles": {"actor"},
        "female": False,
        "alive": True,
    },
    "Deepika Padukone": {
        "category": "Movies",
        "aliases": ["Deepika"],
        "industries": {"hindi"},
        "roles": {"actor"},
        "female": True,
        "alive": True,
    },
    "Priyanka Chopra": {
        "category": "Movies",
        "aliases": ["Priyanka"],
        "industries": {"hindi"},
        "roles": {"actor"},
        "female": True,
        "alive": True,
    },
    "Narendra Modi": {
        "category": "Politicians",
        "aliases": ["Modi"],
        "states": {"gujarat"},
        "roles": {"politician"},
        "female": False,
        "alive": True,
    },
    "Mahatma Gandhi": {
        "category": "Historical Figures",
        "aliases": ["Gandhi", "Bapu"],
        "states": {"gujarat"},
        "roles": {"freedom_fighter"},
        "female": False,
        "alive": False,
    },
    "Indira Gandhi": {
        "category": "Politicians",
        "aliases": ["Indira"],
        "states": {"uttar_pradesh"},
        "roles": {"politician"},
        "female": True,
        "alive": False,
    },
    "Atal Bihari Vajpayee": {
        "category": "Politicians",
        "aliases": ["Vajpayee"],
        "roles": {"politician"},
        "female": False,
        "alive": False,
    },
    "B. R. Ambedkar": {
        "category": "Historical Figures",
        "aliases": ["Ambedkar", "Dr. B. R. Ambedkar", "Babasaheb"],
        "states": {"maharashtra"},
        "roles": {"freedom_fighter"},
        "female": False,
        "alive": False,
    },
    "Subhas Chandra Bose": {
        "category": "Historical Figures",
        "aliases": ["Netaji"],
        "states": {"west_bengal"},
        "roles": {"freedom_fighter"},
        "female": False,
        "alive": False,
    },
}

CORE_QUESTIONS = [
    "Is your character a real person?",
    "Is your character still alive?",
    "Is your character a man?",
    "Is your character a woman?",
    "Is your character from India?",
    "Is your character an actor?",
    "Is your character an actress?",
    "Is your character a politician?",
    "Is your character from a movie?",
    "Is your character from Hindi movies?",
    "Is your character from Tamil movies?",
    "Is your character from Telugu movies?",
    "Is your character from Malayalam movies?",
    "Is your character from Kannada movies?",
    "Is your character from Punjabi movies?",
    "Is your character a freedom fighter?",
    "Is your character linked to Maharashtra?",
    "Is your character linked to Gujarat?",
    "Is your character linked to West Bengal?",
]


def _index_seed(seed: dict) -> tuple[dict[str, dict], dict[str, str]]:
    by_name = {c["name"].casefold(): c for c in seed["characters"]}
    alias_to_name: dict[str, str] = {}
    for c in seed["characters"]:
        alias_to_name[c["name"].casefold()] = c["name"]
        for alias in c.get("aliases") or []:
            alias_to_name[alias.casefold()] = c["name"]
    return by_name, alias_to_name


def _resolve(lookup, name: str) -> dict:
    by_name, alias_to_name = lookup
    canonical = alias_to_name.get(name.casefold())
    assert canonical, f"Missing character or alias: {name}"
    return by_name[canonical.casefold()]


def _lik_map(name: str, category: str) -> dict[str, float]:
    rows = overrides_for_character(name, CORE_QUESTIONS, category=category)
    return {row["question"]: float(row["likelihood"]) for row in rows}


def test_regression_characters_exist_with_category_and_aliases(seed, lookup):
    for name, spec in REGRESSION.items():
        row = _resolve(lookup, name)
        expected = spec["category"]
        if isinstance(expected, set):
            assert row["category"] in expected, (name, row["category"])
        else:
            assert row["category"] == expected, (name, row["category"])
        assert row.get("is_active", True) is True
        have = {a.casefold() for a in (row.get("aliases") or [])}
        have.add(row["name"].casefold())
        for alias in spec["aliases"]:
            assert alias.casefold() in have, (name, alias)
        assert popularity_for(row["name"]) > 0


def test_india_traits_and_regional_metadata():
    for name, spec in REGRESSION.items():
        category = spec["category"]
        if isinstance(category, set):
            category = next(iter(category))
        traits = traits_for(name, category)
        assert traits is not None, name
        assert traits.real is True
        assert traits.alive is spec["alive"], name
        assert traits.female is spec["female"], name
        assert "india" in traits.regions, name
        if "industries" in spec:
            assert spec["industries"] <= set(traits.industries), (name, traits.industries)
        if "states" in spec:
            assert spec["states"] <= set(traits.states), (name, traits.states)
        if "roles" in spec:
            assert spec["roles"] <= set(traits.roles), (name, traits.roles)


def test_india_actor_and_politician_mappings():
    srk = _lik_map("Shah Rukh Khan", "Movies")
    assert srk["Is your character a real person?"] >= 0.9
    assert srk["Is your character from India?"] >= 0.9
    assert srk["Is your character an actor?"] >= 0.9
    assert srk["Is your character from Hindi movies?"] >= 0.9
    assert srk["Is your character from Tamil movies?"] <= 0.15
    assert srk.get("Is your character a politician?", 0.12) <= 0.2

    rajini = _lik_map("Rajinikanth", "Movies")
    assert rajini["Is your character from Tamil movies?"] >= 0.9
    assert rajini["Is your character from Hindi movies?"] <= 0.2 or "hindi" in (
        traits_for("Rajinikanth", "Movies").industries or set()
    )

    allu = _lik_map("Allu Arjun", "Movies")
    assert allu["Is your character from Telugu movies?"] >= 0.9

    yash = _lik_map("Yash", "Movies")
    assert yash["Is your character from Kannada movies?"] >= 0.9

    mammootty = _lik_map("Mammootty", "Movies")
    assert mammootty["Is your character from Malayalam movies?"] >= 0.9

    diljit = _lik_map("Diljit Dosanjh", "Musicians")
    assert diljit["Is your character from Punjabi movies?"] >= 0.9
    assert diljit["Is your character an actor?"] >= 0.9

    deepika = _lik_map("Deepika Padukone", "Movies")
    assert deepika["Is your character a woman?"] >= 0.9
    assert deepika["Is your character an actress?"] >= 0.9

    modi = _lik_map("Narendra Modi", "Politicians")
    assert modi["Is your character a politician?"] >= 0.9
    assert modi["Is your character from India?"] >= 0.9
    assert modi["Is your character linked to Gujarat?"] >= 0.9
    assert modi["Is your character an actor?"] <= 0.2

    gandhi = _lik_map("Mahatma Gandhi", "Historical Figures")
    assert gandhi["Is your character a freedom fighter?"] >= 0.9
    assert gandhi["Is your character still alive?"] <= 0.15

    ambedkar = _lik_map("B. R. Ambedkar", "Historical Figures")
    assert ambedkar["Is your character linked to Maharashtra?"] >= 0.9
    assert ambedkar["Is your character a freedom fighter?"] >= 0.9

    bose = _lik_map("Subhas Chandra Bose", "Historical Figures")
    assert bose["Is your character linked to West Bengal?"] >= 0.9


def test_aliases_resolve_in_seed(lookup):
    assert _resolve(lookup, "SRK")["name"] == "Shah Rukh Khan"
    assert _resolve(lookup, "Big B")["name"] == "Amitabh Bachchan"
    assert _resolve(lookup, "Rajini")["name"] == "Rajinikanth"
    assert _resolve(lookup, "Netaji")["name"] == "Subhas Chandra Bose"
    assert _resolve(lookup, "Bapu")["name"] == "Mahatma Gandhi"
    assert _resolve(lookup, "Dr. B. R. Ambedkar")["name"] == "B. R. Ambedkar"
    assert _resolve(lookup, "Modi")["name"] == "Narendra Modi"


def test_tamil_evidence_beats_global_bollywood_fame():
    rajini_id, srk_id, modi_id, cruise_id = uuid4(), uuid4(), uuid4(), uuid4()
    q_india, q_actor, q_tamil = uuid4(), uuid4(), uuid4()
    ids = {
        "Rajinikanth": rajini_id,
        "Shah Rukh Khan": srk_id,
        "Narendra Modi": modi_id,
        "Tom Cruise": cruise_id,
    }
    questions = {
        q_india: "Is your character from India?",
        q_actor: "Is your character an actor?",
        q_tamil: "Is your character from Tamil movies?",
    }
    cats = {
        "Rajinikanth": "Movies",
        "Shah Rukh Khan": "Movies",
        "Narendra Modi": "Politicians",
        "Tom Cruise": "Movies",
    }
    likelihoods = {}
    for name, cid in ids.items():
        mapped = {
            row["question"]: row["likelihood"]
            for row in overrides_for_character(name, list(questions.values()), category=cats[name])
        }
        for qid, text in questions.items():
            likelihoods[(cid, qid)] = LikelihoodEntry(
                likelihood=mapped.get(text, 0.12),
                sample_size=80,
            )
    popularity = {rajini_id: 96, srk_id: 98, modi_id: 96, cruise_id: 92}
    state = create_initial_state(list(ids.values()), likelihoods, popularity=popularity)
    for qid, ans in ((q_india, "yes"), (q_actor, "yes"), (q_tamil, "yes")):
        state, _ = process_answer(state, qid, ans)
        assert rajini_id in state.probabilities
    ranked = sorted(state.probabilities.items(), key=lambda x: -x[1])
    assert ranked[0][0] == rajini_id
    assert ranked[0][1] > state.probabilities.get(srk_id, 0)


def test_maharashtra_politics_beats_national_fame():
    pawar_id, modi_id, srk_id = uuid4(), uuid4(), uuid4()
    q_india, q_pol, q_mh = uuid4(), uuid4(), uuid4()
    ids = {
        "Sharad Pawar": pawar_id,
        "Narendra Modi": modi_id,
        "Shah Rukh Khan": srk_id,
    }
    questions = {
        q_india: "Is your character from India?",
        q_pol: "Is your character a politician?",
        q_mh: "Is your character linked to Maharashtra?",
    }
    cats = {
        "Sharad Pawar": "Politicians",
        "Narendra Modi": "Politicians",
        "Shah Rukh Khan": "Movies",
    }
    likelihoods = {}
    for name, cid in ids.items():
        mapped = {
            row["question"]: row["likelihood"]
            for row in overrides_for_character(name, list(questions.values()), category=cats[name])
        }
        for qid, text in questions.items():
            likelihoods[(cid, qid)] = LikelihoodEntry(
                likelihood=mapped.get(text, 0.12),
                sample_size=80,
            )
    state = create_initial_state(
        list(ids.values()),
        likelihoods,
        popularity={pawar_id: 78, modi_id: 96, srk_id: 98},
    )
    for qid, ans in ((q_india, "yes"), (q_pol, "yes"), (q_mh, "yes")):
        state, _ = process_answer(state, qid, ans)
        assert pawar_id in state.probabilities
    ranked = sorted(state.probabilities.items(), key=lambda x: -x[1])
    assert ranked[0][0] == pawar_id


def test_no_duplicate_regression_names(seed):
    names = [c["name"].casefold() for c in seed["characters"]]
    assert len(names) == len(set(names))


@pytest.fixture(scope="module")
def seed():
    assert SEED_PATH.exists()
    return json.loads(SEED_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def lookup(seed):
    return _index_seed(seed)
