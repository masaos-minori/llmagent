"""tests/tools/test_docs_similarity.py
Tests for tools/_docs_similarity.py.
"""

from __future__ import annotations

import random

import pytest

from tools._docs_similarity import (
    jaccard_similarity_above,
    similar_pair_indexes,
    tokenize_for_similarity,
)


def _brute_force(token_sets: list[set[str]], threshold: float) -> list[tuple[int, int]]:
    return [
        (i, j)
        for j in range(len(token_sets))
        for i in range(j)
        if jaccard_similarity_above(token_sets[i], token_sets[j], threshold=threshold)
    ]


def test_tokenize_strips_code_and_lowercases() -> None:
    text = "Hello `inline_code` World\n```py\nfenced = 1\n```\nHello2"

    assert tokenize_for_similarity(text) == {"hello", "world", "hello2"}


class TestSimilarPairIndexes:
    def test_empty_and_single_inputs_have_no_pairs(self) -> None:
        assert similar_pair_indexes([]) == []
        assert similar_pair_indexes([{"a", "b"}]) == []

    def test_empty_sets_never_pair(self) -> None:
        assert similar_pair_indexes([set(), set(), {"a"}]) == []

    def test_identical_sets_pair_and_disjoint_sets_do_not(self) -> None:
        words = {f"w{i}" for i in range(20)}
        other = {f"x{i}" for i in range(20)}

        assert similar_pair_indexes([words, other, set(words)]) == [(0, 2)]

    def test_threshold_boundary_matches_the_direct_test(self) -> None:
        base = {f"w{i}" for i in range(20)}
        # 17 shared of 20 + 3 extra on one side: 17 / 23 < 0.85 but 17 / 20 is not.
        near = {f"w{i}" for i in range(17)} | {"extra1", "extra2", "extra3"}
        sets = [base, near, {f"w{i}" for i in range(18)} | {"z1"}]

        for threshold in (0.5, 0.7, 0.85, 0.9, 1.0):
            assert similar_pair_indexes(sets, threshold=threshold) == _brute_force(
                sets, threshold
            )

    @pytest.mark.parametrize("seed", range(12))
    def test_matches_all_pairs_search_on_random_sets(self, seed: int) -> None:
        rng = random.Random(seed)
        vocabulary = [f"t{i}" for i in range(60)]
        sets: list[set[str]] = []
        for _ in range(40):
            if sets and rng.random() < 0.5:
                variant = set(rng.choice(sets))
                for _ in range(rng.randint(0, 4)):
                    variant ^= {rng.choice(vocabulary)}
                sets.append(variant)
            else:
                sets.append(set(rng.sample(vocabulary, rng.randint(0, 40))))
        for threshold in (0.5, 0.85, 0.95):
            assert similar_pair_indexes(sets, threshold=threshold) == sorted(
                _brute_force(sets, threshold), key=lambda pair: (pair[1], pair[0])
            )
