# Implementation: retriever.py + types.py — score contract documentation

## Goal

Make the `MemoryHit.score` contract explicit so callers no longer rely on implicit knowledge:
1. `types.py`: update `MemoryHit.score` field comment to state "higher is better; KNN: -distance".
2. `retriever.py`: add comment on the `score=-distance` line in `VectorRetriever.knn_search()`.
3. `retriever.py`: add comment on the RRF post-processing re-score in `HybridRetriever.search()`.

No logic changes — documentation only.

## Scope

- **Target files**: `scripts/agent/memory/retriever.py`, `scripts/agent/memory/types.py`
- **Not in scope**: `ingestion.py` (handled in Step 4), `_floats_to_blob` duplication (noted, not fixed).

## Assumptions

1. FTS5 `_score()` produces a combined float where higher is better (from `-bm25_rank + boosts`).
2. KNN returns raw L2 distance (lower = closer). `VectorRetriever` negates to align with "higher is better".
3. After RRF merge, `HybridRetriever.search()` re-runs `_score(bm25_rank=0.0, ...)` on merged hits.
   This is intentional: RRF rank drives ordering; final score is re-normalized via `_score`.
   The comment should explain why `bm25_rank=0.0` is passed (rank already captured by RRF).

## Implementation

### Target file

`scripts/agent/memory/types.py` and `scripts/agent/memory/retriever.py`

### Procedure

In `types.py`, update `MemoryHit.score` comment:
```python
score: float  # higher is better; FTS: BM25+boosts rescored; KNN: negated L2 distance
```

In `retriever.py` `VectorRetriever.knn_search()`:
```python
# Negate distance: MemoryHit.score convention is higher-is-better
hits.append(MemoryHit(entry=entry, score=-distance))
```

In `retriever.py` `HybridRetriever.search()` around lines 278-280:
```python
# After RRF merge, re-apply _score so FTS boosts (importance, pin, recency) are reflected.
# bm25_rank=0.0: RRF already captured rank signal; only apply the additive boosts here.
for hit in merged:
    hit.score = _score(0.0, hit.entry, project, repo, self._recency_days)
```

### Method

Direct textual edit (comment additions only).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/memory/retriever.py scripts/agent/memory/types.py` | 0 errors |
| Type | `uv run mypy scripts/agent/memory/retriever.py` | no new errors |
| Tests | `uv run pytest tests/test_memory_retriever.py -x -q` | all pass |
