#!/usr/bin/env python3
"""agent/memory/rrf.py — Reciprocal Rank Fusion merge logic."""

from agent.memory.types import MemoryHit

# RRF constant
RRF_K = 60


def rrf_merge(
    hit_lists: list[list[MemoryHit]],
    k: int = RRF_K,
) -> list[MemoryHit]:
    """Reciprocal Rank Fusion: merge multiple ranked hit lists by rank position.

    Each list contributes 1/(k + rank) to the memory_id's final RRF score.
    Sets hit.score to the RRF score before returning.
    Returns a deduplicated list sorted by descending RRF score.
    """
    rrf_scores: dict[str, float] = {}
    by_id: dict[str, MemoryHit] = {}
    for lst in hit_lists:
        for rank, hit in enumerate(lst):
            mid = hit.entry.memory_id
            rrf_scores[mid] = rrf_scores.get(mid, 0.0) + 1.0 / (k + rank + 1)
            by_id[mid] = hit
    for mid, hit in by_id.items():
        hit.score = rrf_scores[mid]
    return sorted(by_id.values(), key=lambda h: h.score, reverse=True)
