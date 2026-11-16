"""tools/_docs_similarity.py

Shared, non-CLI helper of `check_docs_quality.py`: word-set tokenization of a section
body, the Jaccard threshold test, and an exact all-pairs search over many word sets.

`similar_pair_indexes` returns the same pairs as testing every pair with
`jaccard_similarity_above`, but generates candidates with prefix filtering (a pair that
reaches the threshold must share a token among the first tokens of both sets once each set
is ordered rarest-token-first), so the pair count no longer grows with the square of the
number of sections. Every candidate is still decided by `jaccard_similarity_above`.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from collections.abc import Sequence


def tokenize_for_similarity(text: str) -> set[str]:
    """Tokenize section body text for Jaccard similarity comparison: strip
    fenced and inline code, then lowercase alphanumeric words."""
    text = re.sub(r"```[\s\S]*?```", "", text)
    text = re.sub(r"`[^`]+`", "", text)
    words = re.findall(r"[a-z0-9]+", text.lower())
    return set(words)


def jaccard_similarity_above(
    set_a: set[str], set_b: set[str], *, threshold: float = 0.85
) -> bool:
    """Return True if the two pre-tokenized word sets overlap above threshold."""
    lo, hi = sorted((len(set_a), len(set_b)))
    if not lo or lo / hi < threshold:  # Jaccard <= lo / hi
        return False
    both = len(set_a & set_b)
    return both / (lo + hi - both) >= threshold


def similar_pair_indexes(
    token_sets: Sequence[set[str]], *, threshold: float = 0.85
) -> list[tuple[int, int]]:
    """Return every index pair ``i < j`` that passes `jaccard_similarity_above`.

    Pairs are ordered by ``j`` then ``i``; callers that need another order sort them.
    """
    frequency = Counter(token for tokens in token_sets for token in tokens)
    index: dict[str, list[int]] = {}
    pairs: list[tuple[int, int]] = []
    for j, tokens in enumerate(token_sets):
        ordered = sorted(tokens, key=lambda token: (frequency[token], token))
        # Jaccard >= t implies an overlap of at least ceil(t * size) for both sets, so
        # a prefix of size - ceil(t * size) + 1 tokens must intersect. The epsilon only
        # ever lengthens the prefix, which keeps the filter conservative.
        prefix = len(ordered) - math.ceil(threshold * len(ordered) - 1e-9) + 1
        candidates: set[int] = set()
        for token in ordered[:prefix]:
            candidates.update(index.get(token, ()))
            index.setdefault(token, []).append(j)
        pairs.extend(
            (i, j)
            for i in sorted(candidates)
            if jaccard_similarity_above(
                token_sets[i], token_sets[j], threshold=threshold
            )
        )
    return pairs
