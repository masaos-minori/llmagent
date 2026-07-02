# Implementation Procedure: tests/test_rag_quality_regression.py

## Goal

Extend the existing RAG quality regression test suite with deterministic, non-flaky assertions
covering RRF score values, top-N retrieval count, semantic cache hit/miss paths, and RRF
ordering invariant. All new tests use patching to avoid real embed/DB calls.

## Scope

**In scope:**
- Add 5 new test methods inside `TestRagQualityRegression` in
  `tests/test_rag_quality_regression.py`
- All new tests use `patch("rag.stages.search._search_all_queries", ...)` or direct
  `SemanticCache` instantiation — no real DB/embed I/O

**Out of scope:**
- Changes to `scripts/rag/pipeline.py`, `cache.py`, `repository.py`
- Changes to any other test file

## Assumptions

1. `_make_rag_cfg()` and `_make_pipeline()` helpers are already defined and reusable.
2. `patch("rag.stages.search._search_all_queries", new_callable=AsyncMock)` is the
   correct injection point (established by existing `test_rrf_vs_no_rrf_fusion_mode`).
3. `SemanticCache` can be instantiated directly with `SemanticCache(max_size=10, threshold=0.9)`.
4. RRF score formula: `score = Σ 1/(rrf_k + rank)` per list; with `rrf_k=60`, a hit appearing
   in two lists scores `2/(60+0) = 0.0333...`; a hit in one list scores `1/61 ≈ 0.01639`.
5. `rag_top_k=3` in `_make_rag_cfg()` means `result.reranked` is capped at 3.
6. `SemanticCache.put(vector, history_context, augmented_context)` and `lookup(vector,
   history_context)` signatures — verify from `scripts/rag/cache.py` before writing tests.

## Implementation

### Target file

`tests/test_rag_quality_regression.py`

### Procedure

1. Read `scripts/rag/cache.py` to confirm `SemanticCache.put` / `lookup` signatures and the
   cosine similarity threshold semantics.
2. Read `scripts/rag/repository.py` lines 184–210 (`rrf_merge`) to confirm per-list rank reset
   behavior before writing score assertions.
3. Open `tests/test_rag_quality_regression.py` and locate `TestRagQualityRegression`.
4. Add the five test methods below inside the class.
5. Run `uv run pytest tests/test_rag_quality_regression.py -v` to verify all pass.

### Method

- Phases 1, 2, 5 (RRF and top-N): patch `_search_all_queries` with `AsyncMock` returning
  synthetic `RawHit` lists; call `pipeline.augment(query)` or directly call the stage.
- Phase 3, 4 (cache hit/miss): instantiate `SemanticCache` directly, no pipeline needed.

### Details

```python
# Phase 1: deterministic RRF score values
def test_rrf_score_values_with_known_hits(self):
    """Hit in both lists has strictly higher RRF score than hit in one list."""
    # chunk_id=1 appears in list A rank 0 and list B rank 1 → highest score
    list_a = [RawHit(chunk_id=1, ...)]
    list_b = [RawHit(chunk_id=2, ...), RawHit(chunk_id=1, ...)]
    with patch("rag.stages.search._search_all_queries", ...) as mock:
        mock.return_value = [list_a, list_b]
        result = await pipeline.augment("q")
    assert result.merged[0].chunk_id == 1
    assert result.merged[0].rrf_score > result.merged[1].rrf_score
    assert all(h.rrf_score > 0.0 for h in result.merged)

# Phase 2: top-N count
def test_top_n_retrieval_count(self):
    """reranked is sliced to rag_top_k; merged retains all hits."""
    five_hits = [RawHit(chunk_id=i, ...) for i in range(5)]
    with patch("rag.stages.search._search_all_queries", ...) as mock:
        mock.return_value = [five_hits]
        result = await pipeline.augment("q")
    assert len(result.reranked) == 3   # rag_top_k=3
    assert len(result.merged) == 5

# Phase 3: semantic cache hit
def test_semantic_cache_hit_returns_cached_result(self):
    cache = SemanticCache(max_size=10, threshold=0.9)
    vec = [1.0] * 384
    cache.put(vec, "", "expected_context")
    assert cache.lookup(vec, "") == "expected_context"
    assert cache.size == 1

# Phase 4: semantic cache miss below threshold
def test_semantic_cache_miss_below_threshold(self):
    cache = SemanticCache(max_size=10, threshold=0.99)
    cache.put([1.0] * 384, "", "ctx")
    assert cache.lookup([-1.0] * 384, "") is None   # cosine_sim ≈ -1.0 < 0.99

# Phase 5: RRF merged order is descending
def test_rrf_merged_order_is_descending(self):
    three_hits = [RawHit(chunk_id=i, ...) for i in range(3)]
    with patch("rag.stages.search._search_all_queries", ...) as mock:
        mock.return_value = [three_hits]
        result = await pipeline.augment("q")
    scores = [h.rrf_score for h in result.merged]
    assert scores == sorted(scores, reverse=True)
```

**Notes:**
- Fill in `RawHit(...)` constructor args by reading the `RawHit` dataclass definition.
- If `pipeline.augment` is `async`, use `pytest.mark.asyncio`.
- Use `use_rrf=True, rrf_k=60, use_rerank=False` in config for deterministic behavior.

## Validation plan

| Step | Command | Expected result |
|------|---------|----------------|
| Run all regression tests | `uv run pytest tests/test_rag_quality_regression.py -v` | all PASSED |
| Full test suite | `uv run pytest` | no regressions |
| Lint | `ruff check tests/test_rag_quality_regression.py` | 0 errors |
| Type check | `mypy tests/test_rag_quality_regression.py` | no new errors |
