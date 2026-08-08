"""Question quality checks for curated Question Database v2."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SEED_PATH = ROOT / "data" / "knowledge" / "seed_v1.json"
QUESTIONS_V2_PATH = ROOT / "data" / "knowledge" / "questions_v2.json"

HARD_VOCAB = {
    "protagonist",
    "antagonist",
    "entrepreneurship",
    "astronomy",
    "quantum",
    "franchise",
    "manga",
    "androgynous",
    "canon",
}


def test_active_seed_questions_are_short_and_simple():
    data = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    active = [q for q in data["questions"] if q.get("is_active")]
    assert 220 <= len(active) <= 280
    assert data.get("active_question_dataset") == "v2"

    over_ten = [q["text"] for q in active if len(q["text"].split()) > 10]
    assert over_ten == [], f"Questions over 10 words: {over_ten[:5]}"

    for q in active:
        text = q["text"]
        assert text.endswith("?"), text
        lowered = text.casefold()
        for word in HARD_VOCAB:
            assert word not in lowered, f"Hard vocab {word!r} in {text!r}"
        assert q.get("category"), text
        assert q.get("dataset") == "v2"


def test_questions_v2_export_matches_active_seed():
    seed = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    exported = json.loads(QUESTIONS_V2_PATH.read_text(encoding="utf-8"))
    active_texts = {q["text"] for q in seed["questions"] if q.get("is_active")}
    export_texts = {q["text"] for q in exported["questions"]}
    assert active_texts == export_texts
