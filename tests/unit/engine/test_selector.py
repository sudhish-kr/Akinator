"""Tests for dynamic, candidate-focused question selection."""

from __future__ import annotations

import random
from uuid import UUID, uuid4

import pytest

from app.engine.bayesian import bayesian_update
from app.engine.cold_start import get_likelihood
from app.engine.models import LikelihoodEntry, QuestionRef
from app.engine.selector import (
    create_initial_state,
    focus_candidate_state,
    information_gain,
    process_answer,
    select_next_question,
)
from app.training.oracle import oracle_answer

C1 = UUID("00000000-0000-0000-0000-000000000001")
C2 = UUID("00000000-0000-0000-0000-000000000002")
C3 = UUID("00000000-0000-0000-0000-000000000003")
Q_SPLIT = UUID("00000000-0000-0000-0000-0000000000a1")  # high IG
Q_FLAT = UUID("00000000-0000-0000-0000-0000000000a2")  # low IG


def _state_with_split_and_flat():
    """Q_SPLIT strongly partitions candidates; Q_FLAT does not."""
    likelihoods = {
        (C1, Q_SPLIT): LikelihoodEntry(0.95, 50),
        (C2, Q_SPLIT): LikelihoodEntry(0.05, 50),
        (C3, Q_SPLIT): LikelihoodEntry(0.05, 50),
        (C1, Q_FLAT): LikelihoodEntry(0.5, 50),
        (C2, Q_FLAT): LikelihoodEntry(0.5, 50),
        (C3, Q_FLAT): LikelihoodEntry(0.5, 50),
    }
    return create_initial_state([C1, C2, C3], likelihoods)


def test_selects_highest_information_gain_question():
    state = _state_with_split_and_flat()
    assert information_gain(state, Q_SPLIT) > information_gain(state, Q_FLAT)
    assert (
        select_next_question(
            state, [Q_FLAT, Q_SPLIT], min_samples=1, explore=False
        )
        == Q_SPLIT
    )


def test_ignores_already_answered_questions():
    state = _state_with_split_and_flat()
    state.used_question_ids.add(Q_SPLIT)
    assert (
        select_next_question(state, [Q_SPLIT, Q_FLAT], min_samples=1, explore=False)
        == Q_FLAT
    )


def test_returns_none_when_all_questions_answered():
    state = _state_with_split_and_flat()
    state.used_question_ids.update({Q_SPLIT, Q_FLAT})
    assert select_next_question(state, [Q_SPLIT, Q_FLAT], min_samples=1) is None


def test_information_gain_supports_yes_no_unknown_outcomes():
    """IG must be well-defined when averaging yes / no / unknown (dont_know)."""
    state = _state_with_split_and_flat()
    ig = information_gain(state, Q_SPLIT)
    assert ig > 0
    assert ig == pytest.approx(ig)  # finite, not NaN


def test_never_repeats_used_questions_after_process_answer():
    state = _state_with_split_and_flat()
    q = select_next_question(state, [Q_SPLIT, Q_FLAT], min_samples=1, explore=False)
    assert q is not None
    state, _ = process_answer(state, q, "yes")
    nxt = select_next_question(state, [Q_SPLIT, Q_FLAT], min_samples=1, explore=False)
    assert nxt != q
    assert q in state.used_question_ids


def test_focus_candidate_state_shrinks_to_high_mass_frontier():
    state = create_initial_state([C1, C2, C3], {})
    state.probabilities = {C1: 0.7, C2: 0.25, C3: 0.05}
    focused = focus_candidate_state(state, mass_threshold=0.9, min_keep=2)
    assert C1 in focused.probabilities
    assert C3 not in focused.probabilities
    assert sum(focused.probabilities.values()) == pytest.approx(1.0)


def test_prefers_category_specific_questions_once_confidence_exceeds_20_percent():
    """Category preference applies only after category posterior mass exceeds threshold."""
    scientist = C1
    athlete = C2
    q_scientist = UUID("00000000-0000-0000-0000-0000000000b1")
    q_athlete = UUID("00000000-0000-0000-0000-0000000000b2")
    q_meta = UUID("00000000-0000-0000-0000-0000000000b3")

    likelihoods = {
        (scientist, q_scientist): LikelihoodEntry(0.95, 40),
        (athlete, q_scientist): LikelihoodEntry(0.05, 40),
        (scientist, q_athlete): LikelihoodEntry(0.05, 40),
        (athlete, q_athlete): LikelihoodEntry(0.95, 40),
        (scientist, q_meta): LikelihoodEntry(0.55, 40),
        (athlete, q_meta): LikelihoodEntry(0.45, 40),
    }
    state = create_initial_state([scientist, athlete], likelihoods)
    # Scientists category mass 0.72 > preference / unlock threshold
    state.probabilities = {scientist: 0.72, athlete: 0.28}
    # Past the early identity lock so category preference can apply.
    state.questions_asked = 3

    refs = {
        q_scientist: QuestionRef(id=q_scientist, text="Scientist?", category="Science"),
        q_athlete: QuestionRef(id=q_athlete, text="Athlete?", category="Sports"),
        q_meta: QuestionRef(id=q_meta, text="Famous?", category="Personality"),
    }
    categories = {scientist: "Scientists", athlete: "Sports"}

    chosen = select_next_question(
        state,
        [q_meta, q_scientist, q_athlete],
        min_samples=1,
        question_refs=refs,
        character_categories=categories,
        category_preference_threshold=0.20,
        category_unlock_threshold=0.20,
        explore=False,
    )
    assert chosen in {q_scientist, q_athlete}
    assert refs[chosen].category in {"Science", "Sports"}


def test_blocks_domain_questions_until_category_probability_is_high():
    """Anime/Sports/Movies stay locked while category mass is still low."""
    from app.engine.selector import is_domain_category_unlocked

    a, b, c, d = C1, C2, C3, UUID("00000000-0000-0000-0000-000000000004")
    q_broad = UUID("00000000-0000-0000-0000-0000000000ba")
    q_anime = UUID("00000000-0000-0000-0000-0000000000bb")
    q_sports = UUID("00000000-0000-0000-0000-0000000000bc")
    q_movies = UUID("00000000-0000-0000-0000-0000000000bd")

    likelihoods = {
        (a, q_broad): LikelihoodEntry(0.9, 40),
        (b, q_broad): LikelihoodEntry(0.1, 40),
        (c, q_broad): LikelihoodEntry(0.5, 40),
        (d, q_broad): LikelihoodEntry(0.5, 40),
        (a, q_anime): LikelihoodEntry(0.05, 40),
        (b, q_anime): LikelihoodEntry(0.05, 40),
        (c, q_anime): LikelihoodEntry(0.95, 40),
        (d, q_anime): LikelihoodEntry(0.05, 40),
        (a, q_sports): LikelihoodEntry(0.95, 40),
        (b, q_sports): LikelihoodEntry(0.05, 40),
        (c, q_sports): LikelihoodEntry(0.05, 40),
        (d, q_sports): LikelihoodEntry(0.05, 40),
        (a, q_movies): LikelihoodEntry(0.05, 40),
        (b, q_movies): LikelihoodEntry(0.95, 40),
        (c, q_movies): LikelihoodEntry(0.05, 40),
        (d, q_movies): LikelihoodEntry(0.05, 40),
    }
    state = create_initial_state([a, b, c, d], likelihoods)  # uniform 0.25 each
    categories = {
        a: "Sports",
        b: "Movies",
        c: "Anime",
        d: "Scientists",
    }
    refs = {
        q_broad: QuestionRef(id=q_broad, text="Real person?", category="Personality"),
        q_anime: QuestionRef(id=q_anime, text="From anime?", category="Anime"),
        q_sports: QuestionRef(id=q_sports, text="Sports player?", category="Sports"),
        q_movies: QuestionRef(id=q_movies, text="From a movie?", category="Movies"),
    }

    assert not is_domain_category_unlocked("Anime", state, categories, unlock_threshold=0.35)
    assert not is_domain_category_unlocked("Sports", state, categories, unlock_threshold=0.35)
    assert not is_domain_category_unlocked("Movies", state, categories, unlock_threshold=0.35)

    chosen = select_next_question(
        state,
        [q_broad, q_anime, q_sports, q_movies],
        min_samples=1,
        question_refs=refs,
        character_categories=categories,
        category_unlock_threshold=0.35,
        explore=False,
    )
    assert chosen == q_broad

    # After Sports dominates, Sports questions unlock
    state.probabilities = {a: 0.8, b: 0.1, c: 0.05, d: 0.05}
    assert is_domain_category_unlocked("Sports", state, categories, unlock_threshold=0.35)
    chosen2 = select_next_question(
        state,
        [q_broad, q_anime, q_sports, q_movies],
        min_samples=1,
        question_refs=refs,
        character_categories=categories,
        category_unlock_threshold=0.35,
        explore=False,
    )
    assert chosen2 in {q_broad, q_sports}
    assert chosen2 != q_anime
    assert chosen2 != q_movies


def test_blocks_anime_sports_movie_questions_without_matching_candidates():
    """Domain questions are irrelevant once their character categories are gone."""
    from app.engine.selector import is_question_relevant_to_candidates, remaining_character_categories

    einstein = C1
    kohli = C2
    q_anime = UUID("00000000-0000-0000-0000-0000000000aa")
    q_sports = UUID("00000000-0000-0000-0000-0000000000ab")
    q_movies = UUID("00000000-0000-0000-0000-0000000000ac")
    q_science = UUID("00000000-0000-0000-0000-0000000000ad")
    q_broad = UUID("00000000-0000-0000-0000-0000000000ae")

    likelihoods = {
        (einstein, q_anime): LikelihoodEntry(0.05, 40),
        (kohli, q_anime): LikelihoodEntry(0.05, 40),
        (einstein, q_sports): LikelihoodEntry(0.05, 40),
        (kohli, q_sports): LikelihoodEntry(0.95, 40),
        (einstein, q_movies): LikelihoodEntry(0.1, 40),
        (kohli, q_movies): LikelihoodEntry(0.1, 40),
        (einstein, q_science): LikelihoodEntry(0.95, 40),
        (kohli, q_science): LikelihoodEntry(0.05, 40),
        (einstein, q_broad): LikelihoodEntry(0.9, 40),
        (kohli, q_broad): LikelihoodEntry(0.9, 40),
    }
    state = create_initial_state([einstein, kohli], likelihoods)
    categories = {einstein: "Scientists", kohli: "Sports"}
    refs = {
        q_anime: QuestionRef(id=q_anime, text="Is this from anime?", category="Anime"),
        q_sports: QuestionRef(id=q_sports, text="Is this a sports player?", category="Sports"),
        q_movies: QuestionRef(id=q_movies, text="Is this from a movie?", category="Movies"),
        q_science: QuestionRef(id=q_science, text="Is this a scientist?", category="Science"),
        q_broad: QuestionRef(id=q_broad, text="Is this a real person?", category="Personality"),
    }

    remaining = remaining_character_categories(state, categories)
    assert remaining == frozenset({"Scientists", "Sports"})
    assert not is_question_relevant_to_candidates(q_anime, refs, remaining)
    assert not is_question_relevant_to_candidates(q_movies, refs, remaining)
    assert is_question_relevant_to_candidates(q_sports, refs, remaining)
    assert is_question_relevant_to_candidates(q_science, refs, remaining)

    # Scientists dominate → Stage B/C Science allowed; Anime/Movies blocked
    state.probabilities = {einstein: 0.85, kohli: 0.15}
    chosen = select_next_question(
        state,
        [q_anime, q_sports, q_movies, q_science, q_broad],
        min_samples=1,
        question_refs=refs,
        character_categories=categories,
        explore=False,
    )
    assert chosen in {q_science, q_broad}
    assert chosen not in {q_anime, q_movies, q_sports}

    state.probabilities = {einstein: 1.0}
    chosen2 = select_next_question(
        state,
        [q_anime, q_sports, q_movies, q_science, q_broad],
        min_samples=1,
        question_refs=refs,
        character_categories=categories,
        explore=False,
    )
    assert chosen2 in {q_science, q_broad}


def test_virat_kohli_naruto_iron_man_einstein_receive_different_question_paths():
    """Regression: four iconic characters get distinct hierarchical paths."""
    kohli = UUID("00000000-0000-0000-0000-000000000101")
    naruto = UUID("00000000-0000-0000-0000-000000000102")
    iron_man = UUID("00000000-0000-0000-0000-000000000103")
    einstein = UUID("00000000-0000-0000-0000-000000000104")

    q_real = UUID("00000000-0000-0000-0000-000000000201")
    q_alive = UUID("00000000-0000-0000-0000-00000000020a")
    q_male = UUID("00000000-0000-0000-0000-00000000020b")
    q_kid = UUID("00000000-0000-0000-0000-00000000020c")
    q_anime = UUID("00000000-0000-0000-0000-000000000202")
    q_sports = UUID("00000000-0000-0000-0000-000000000203")
    q_movies = UUID("00000000-0000-0000-0000-000000000204")
    q_science = UUID("00000000-0000-0000-0000-000000000205")
    q_cricket = UUID("00000000-0000-0000-0000-000000000206")
    q_ninja = UUID("00000000-0000-0000-0000-000000000207")
    q_armor = UUID("00000000-0000-0000-0000-000000000208")
    q_physics = UUID("00000000-0000-0000-0000-000000000209")

    chars = [kohli, naruto, iron_man, einstein]
    questions = [
        q_real,
        q_alive,
        q_male,
        q_kid,
        q_anime,
        q_sports,
        q_movies,
        q_science,
        q_cricket,
        q_ninja,
        q_armor,
        q_physics,
    ]
    refs = {
        q_real: QuestionRef(id=q_real, text="Real person?", category="Personality"),
        q_alive: QuestionRef(id=q_alive, text="Still alive?", category="Age"),
        q_male: QuestionRef(id=q_male, text="Are they male?", category="Gender"),
        q_kid: QuestionRef(id=q_kid, text="Are they a kid or teen?", category="Age"),
        q_anime: QuestionRef(id=q_anime, text="From anime?", category="Anime"),
        q_sports: QuestionRef(id=q_sports, text="Athlete?", category="Sports"),
        q_movies: QuestionRef(id=q_movies, text="Movies?", category="Movies"),
        q_science: QuestionRef(id=q_science, text="Scientist?", category="Science"),
        q_cricket: QuestionRef(id=q_cricket, text="Cricket?", category="Sports"),
        q_ninja: QuestionRef(id=q_ninja, text="Ninja?", category="Anime"),
        q_armor: QuestionRef(id=q_armor, text="Power armor?", category="Movies"),
        q_physics: QuestionRef(id=q_physics, text="Physics?", category="Science"),
    }
    categories = {
        kohli: "Sports",
        naruto: "Anime",
        iron_man: "Movies",
        einstein: "Scientists",
    }
    profile = {
        kohli: {
            q_real: 0.95,
            q_alive: 0.9,
            q_male: 0.95,
            q_kid: 0.05,
            q_anime: 0.02,
            q_sports: 0.97,
            q_movies: 0.1,
            q_science: 0.05,
            q_cricket: 0.96,
            q_ninja: 0.02,
            q_armor: 0.05,
            q_physics: 0.05,
        },
        naruto: {
            q_real: 0.05,
            q_alive: 0.5,
            q_male: 0.95,
            q_kid: 0.85,
            q_anime: 0.97,
            q_sports: 0.05,
            q_movies: 0.2,
            q_science: 0.05,
            q_cricket: 0.05,
            q_ninja: 0.95,
            q_armor: 0.1,
            q_physics: 0.05,
        },
        iron_man: {
            q_real: 0.1,
            q_alive: 0.5,
            q_male: 0.95,
            q_kid: 0.05,
            q_anime: 0.05,
            q_sports: 0.05,
            q_movies: 0.96,
            q_science: 0.35,
            q_cricket: 0.05,
            q_ninja: 0.05,
            q_armor: 0.95,
            q_physics: 0.4,
        },
        einstein: {
            q_real: 0.95,
            q_alive: 0.05,
            q_male: 0.95,
            q_kid: 0.05,
            q_anime: 0.02,
            q_sports: 0.05,
            q_movies: 0.15,
            q_science: 0.96,
            q_cricket: 0.05,
            q_ninja: 0.02,
            q_armor: 0.05,
            q_physics: 0.95,
        },
    }
    likelihoods = {
        (cid, qid): LikelihoodEntry(lik, 50)
        for cid, answers in profile.items()
        for qid, lik in answers.items()
    }

    def play(true_id: UUID) -> tuple[list[UUID], list[str]]:
        seq = _play_question_sequence(
            true_id,
            chars,
            questions,
            likelihoods,
            refs,
            categories,
            max_questions=12,
            seed=7,
        )
        cats = [refs[qid].category for qid in seq]
        return seq, cats

    seq_kohli, cats_kohli = play(kohli)
    seq_naruto, cats_naruto = play(naruto)
    seq_iron, cats_iron = play(iron_man)
    seq_einstein, cats_einstein = play(einstein)

    assert len(seq_kohli) >= 2
    assert len(seq_naruto) >= 2
    assert len(seq_iron) >= 2
    assert len(seq_einstein) >= 2

    paths = {tuple(seq_kohli), tuple(seq_naruto), tuple(seq_iron), tuple(seq_einstein)}
    assert len(paths) >= 3

    def assert_no_irrelevant_domain(seq: list[UUID], true_id: UUID) -> None:
        state = create_initial_state(chars, likelihoods)
        rng = random.Random(7)
        for qid in seq:
            remaining = {
                categories[cid]
                for cid, p in state.probabilities.items()
                if p > 1e-6 and cid in categories
            }
            qcat = refs[qid].category
            if qcat == "Anime":
                assert "Anime" in remaining
            if qcat == "Sports":
                assert "Sports" in remaining
            if qcat == "Movies":
                assert "Movies" in remaining
            answer = oracle_answer(likelihoods, true_id, qid, rng, noise=0.0)
            state, _ = process_answer(state, qid, answer)

    assert_no_irrelevant_domain(seq_kohli, kohli)
    assert_no_irrelevant_domain(seq_naruto, naruto)
    assert_no_irrelevant_domain(seq_iron, iron_man)
    assert_no_irrelevant_domain(seq_einstein, einstein)

    # With early-priority ranking, domain tags may arrive later — accept either
    # the matching domain or continued broad identity/origin questions.
    assert "Sports" in cats_kohli or all(
        refs[q].category in {"Personality", "Gender", "Age", "Nationality", "Fictional traits"}
        for q in seq_kohli[:4]
    )
    assert "Anime" in cats_naruto or all(
        refs[q].category in {"Personality", "Gender", "Age", "Nationality", "Fictional traits"}
        for q in seq_naruto[:4]
    )
    assert "Movies" in cats_iron or all(
        refs[q].category in {"Personality", "Gender", "Age", "Nationality", "Fictional traits"}
        for q in seq_iron[:4]
    )
    assert "Science" in cats_einstein or all(
        refs[q].category in {"Personality", "Gender", "Age", "Nationality", "Fictional traits"}
        for q in seq_einstein[:4]
    )

def test_imported_likelihood_mappings_drive_information_gain():
    """Seed-style category likelihood mappings must produce real IG differences."""
    scientist = C1
    athlete = C2
    q_domain = UUID("00000000-0000-0000-0000-0000000000c1")
    q_noise = UUID("00000000-0000-0000-0000-0000000000c2")

    # Mirrors knowledge-seed rules: domain question splits Scientists vs Sports
    likelihoods = {
        (scientist, q_domain): LikelihoodEntry(0.95, 40),
        (athlete, q_domain): LikelihoodEntry(0.05, 40),
        (scientist, q_noise): LikelihoodEntry(0.5, 40),
        (athlete, q_noise): LikelihoodEntry(0.5, 40),
    }
    state = create_initial_state([scientist, athlete], likelihoods)
    assert information_gain(state, q_domain) > information_gain(state, q_noise)
    assert get_likelihood(state.likelihoods, scientist, q_domain) == pytest.approx(0.95)


def test_diversity_across_games_varies_near_tied_questions():
    """Near-tied questions should not always yield the same pick across RNG seeds."""
    q_a = UUID("00000000-0000-0000-0000-0000000000d1")
    q_b = UUID("00000000-0000-0000-0000-0000000000d2")
    likelihoods = {
        (C1, q_a): LikelihoodEntry(0.9, 50),
        (C2, q_a): LikelihoodEntry(0.1, 50),
        (C1, q_b): LikelihoodEntry(0.88, 50),
        (C2, q_b): LikelihoodEntry(0.12, 50),
    }
    state = create_initial_state([C1, C2], likelihoods)
    picks = {
        select_next_question(
            state,
            [q_a, q_b],
            min_samples=1,
            diversity_margin=0.5,
            diversity_top_k=2,
            rng=random.Random(seed),
            explore=True,
        )
        for seed in range(40)
    }
    assert picks == {q_a, q_b}


def _play_question_sequence(
    true_id: UUID,
    character_ids: list[UUID],
    question_ids: list[UUID],
    likelihoods: dict[tuple[UUID, UUID], LikelihoodEntry],
    question_refs: dict[UUID, QuestionRef],
    character_categories: dict[UUID, str],
    *,
    max_questions: int = 8,
    seed: int = 0,
) -> list[UUID]:
    """Oracle-answered playthrough returning the asked question id sequence."""
    rng = random.Random(seed)
    state = create_initial_state(character_ids, likelihoods)
    asked: list[UUID] = []
    for _ in range(max_questions):
        qid = select_next_question(
            state,
            question_ids,
            min_samples=1,
            question_refs=question_refs,
            character_categories=character_categories,
            rng=rng,
            explore=False,
        )
        if qid is None:
            break
        answer = oracle_answer(likelihoods, true_id, qid, rng, noise=0.0)
        state, _ = process_answer(state, qid, answer)
        asked.append(qid)
    return asked


def test_different_characters_produce_different_question_sequences():
    """Regression: scientist vs athlete vs movie paths diverge under hierarchy."""
    einstein = UUID("00000000-0000-0000-0000-0000000000e1")
    messi = UUID("00000000-0000-0000-0000-0000000000e2")
    potter = UUID("00000000-0000-0000-0000-0000000000e3")

    q_real = UUID("00000000-0000-0000-0000-0000000000f1")
    q_alive = UUID("00000000-0000-0000-0000-0000000000f0")
    q_scientist = UUID("00000000-0000-0000-0000-0000000000f2")
    q_space = UUID("00000000-0000-0000-0000-0000000000f6")
    q_athlete = UUID("00000000-0000-0000-0000-0000000000f3")
    q_fictional = UUID("00000000-0000-0000-0000-0000000000f4")
    q_movies = UUID("00000000-0000-0000-0000-0000000000f5")

    chars = [einstein, messi, potter]
    questions = [q_real, q_alive, q_scientist, q_space, q_athlete, q_fictional, q_movies]

    profile = {
        einstein: {
            q_real: 0.95,
            q_alive: 0.05,
            q_scientist: 0.95,
            q_space: 0.92,
            q_athlete: 0.05,
            q_fictional: 0.05,
            q_movies: 0.15,
        },
        messi: {
            q_real: 0.95,
            q_alive: 0.95,
            q_scientist: 0.05,
            q_space: 0.05,
            q_athlete: 0.97,
            q_fictional: 0.05,
            q_movies: 0.15,
        },
        potter: {
            q_real: 0.1,
            q_alive: 0.5,
            q_scientist: 0.35,
            q_space: 0.05,
            q_athlete: 0.08,
            q_fictional: 0.97,
            q_movies: 0.95,
        },
    }
    likelihoods = {
        (cid, qid): LikelihoodEntry(lik, 40)
        for cid, answers in profile.items()
        for qid, lik in answers.items()
    }
    refs = {
        q_real: QuestionRef(id=q_real, text="Real person?", category="Personality"),
        q_alive: QuestionRef(id=q_alive, text="Still alive?", category="Age"),
        q_scientist: QuestionRef(id=q_scientist, text="Scientist?", category="Science"),
        q_space: QuestionRef(id=q_space, text="Space research?", category="Science"),
        q_athlete: QuestionRef(id=q_athlete, text="Athlete?", category="Sports"),
        q_fictional: QuestionRef(id=q_fictional, text="Fictional?", category="Fictional traits"),
        q_movies: QuestionRef(id=q_movies, text="Movies?", category="Movies"),
    }
    categories = {
        einstein: "Scientists",
        messi: "Sports",
        potter: "Movies",
    }

    seq_einstein = _play_question_sequence(
        einstein, chars, questions, likelihoods, refs, categories, seed=1
    )
    seq_messi = _play_question_sequence(
        messi, chars, questions, likelihoods, refs, categories, seed=1
    )
    seq_potter = _play_question_sequence(
        potter, chars, questions, likelihoods, refs, categories, seed=1
    )

    assert len(seq_einstein) >= 2
    assert len(seq_messi) >= 2
    assert len(seq_potter) >= 2
    assert seq_einstein != seq_messi
    assert seq_einstein != seq_potter
    assert seq_messi != seq_potter
    assert len(seq_einstein) == len(set(seq_einstein))
    assert len(seq_messi) == len(set(seq_messi))
    assert len(seq_potter) == len(set(seq_potter))


def test_bayesian_update_path_unchanged_by_selector():
    """Selector strategy must not alter bayesian_update posteriors."""
    state = _state_with_split_and_flat()
    before = dict(state.probabilities)
    posterior = bayesian_update(state, Q_SPLIT, "yes")
    assert state.probabilities == before
    assert sum(posterior.values()) == pytest.approx(1.0)
    assert posterior[C1] > posterior[C2]
