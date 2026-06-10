# Implementation: memory/retriever.py — remove broad exceptions, fix hybrid score, remove session_id

## Goal

1. Remove `except Exception: return []` from FTS, KNN, top_semantic — search failures propagate.
2. Remove `_score(0.0, ...)` re-scoring after RRF merge; use RRF scores directly.
3. Remove `session_id` from `MemoryQuery` parameter access (field already removed from types.py).
4. Fix `_recency_boost` broad exception swallow.

## Scope

- `scripts/agent/memory/retriever.py` — primary
- `tests/test_memory_retriever.py` — update tests that expected empty list on error

## Assumptions

1. `MemoryQuery.session_id` is removed in Step 1 (types.py); retriever no longer references it.
2. After RRF merge, sorted by `rrf_scores[mid]` directly — no `_score(0.0, ...)` call.
   The RRF score captures rank fusion; FTS importance boosts are already embedded in FTS ranks.
3. `_recency_boost` broad exception (line 55-62): replace `except Exception: return 0.0`
   with specific `except (ValueError, OverflowError): return 0.0` — these are the only
   realistic errors from `datetime.fromisoformat` and arithmetic.
4. `FtsRetriever.search()` broad exception removal: SQL errors propagate to callers.
   `HybridRetriever.search()` is the primary external interface; its callers handle failures.

## Implementation

### FtsRetriever.search: remove except

```python
# Remove:
except Exception as e:
    logger.warning(f"FtsRetriever.search failed: {e}")
    return []
# Let sqlite3.OperationalError propagate.
```

### VectorRetriever.knn_search: remove except

```python
# Remove:
except Exception as e:
    logger.warning(f"VectorRetriever.knn_search failed: {e}")
    return []
```

### HybridRetriever.search: remove re-scoring after RRF

```python
# BEFORE:
merged = _rrf_merge([fts_hits, vec_hits], k=self._rrf_k)
for hit in merged:
    hit.score = _score(0.0, hit.entry, project, repo, self._recency_days)
merged.sort(key=lambda h: h.score, reverse=True)
return merged[: query.limit]

# AFTER:
rrf_scores: dict[str, float] = {}  # computed inside _rrf_merge but need access here
# Simplest approach: _rrf_merge returns (merged_list, rrf_scores) tuple
# OR: sort by MemoryHit.score that _rrf_merge already sets as the RRF score
```

Best approach: have `_rrf_merge` set `hit.score = rrf_score` before returning,
then just sort (remove the re-score loop):

```python
merged = _rrf_merge([fts_hits, vec_hits], k=self._rrf_k)
# _rrf_merge already set hit.score = rrf_score
merged.sort(key=lambda h: h.score, reverse=True)
return merged[: query.limit]
```

Update `_rrf_merge` to set `hit.score = rrf_scores[mid]` before returning.

### HybridRetriever.top_semantic: remove except

Remove `except Exception as e: logger.warning(...); return []`.

### _recency_boost: narrow except

```python
except (ValueError, OverflowError):
    return 0.0
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/memory/retriever.py` | 0 errors |
| Type | `uv run mypy scripts/agent/memory/retriever.py` | no new errors |
| Tests | `uv run pytest tests/test_memory_retriever.py -x -v` | all pass |
| No broad except | `grep -n "except Exception" scripts/agent/memory/retriever.py` | 0 hits |
