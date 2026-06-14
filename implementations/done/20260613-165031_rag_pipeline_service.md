# Implementation: rag/pipeline.py + mcp/rag_pipeline/service.py — last_reranked → last_fetch_result

## Goal

Replace `pipeline.last_reranked: list[RagHit]` with `pipeline.last_fetch_result: TwoStageFetchResult | None` in `pipeline.py`, update both callers in `service.py`, and fix all affected tests.

## Scope

- `scripts/rag/pipeline.py` — rename `last_reranked` to `last_fetch_result`; wrap assignments with `TwoStageFetchResult`
- `scripts/mcp/rag_pipeline/service.py` — update 2 access sites (lines 113 and 130) with `None` guard
- `tests/test_agent_rag.py` — update 4 direct references (lines 80, 103, 108, 143)
- `tests/test_rag_pipeline_mcp_service.py` — update 12 direct references (lines 116, 132, 145, 158, 180, 191, 234, 264, 278, 307, 317, 336)

## Assumptions

- `TwoStageFetchResult` is available in `rag/models.py` (implemented in the previous step)
- `pipeline.py` imports `TwoStageFetchResult` from `rag.models`
- `pipeline.run()` sets `self.last_reranked = ctx.reranked` at line 188
- `pipeline._augment_http()` sets `self.last_reranked = hits` at line 211, guarded by `if hits:`
- `service.py:113,130` access `pipeline.last_reranked` directly, converting each hit with `dict(h)`
- In HTTP mode, `hits` is `list[dict]` — `min_score_applied=0.0` and `max_chunks_per_doc=0` because score/dedup info is unavailable
- The `if hits:` guard in `_augment_http()` must be preserved: when hits is empty, `last_fetch_result` stays `None`

## Implementation

### Target file

- `scripts/rag/pipeline.py`
- `scripts/mcp/rag_pipeline/service.py`
- `tests/test_agent_rag.py`
- `tests/test_rag_pipeline_mcp_service.py`

### Procedure

1. Add `TwoStageFetchResult` to the import line in `pipeline.py`
2. Change `self.last_reranked: list[RagHit] = []` (line 102) to `self.last_fetch_result: TwoStageFetchResult | None = None`
3. Update `pipeline.run()` terminal assignment (line 188)
4. Update `pipeline._augment_http()` assignment (line 211)
5. Update `service.py:113` and `service.py:130`
6. Update test assertions and mock setups in `test_agent_rag.py` and `test_rag_pipeline_mcp_service.py`
7. Verify `grep -rn "last_reranked" scripts/ tests/` returns 0

### Method

- Edit tool for each file
- Use `grep -n "last_reranked"` to find all remaining occurrences before committing

### Details

**`pipeline.py` — import:**
```python
# Add TwoStageFetchResult to existing rag.models import
from rag.models import ..., TwoStageFetchResult
```

**`pipeline.py` line 102 — instance variable:**
```python
# Before
self.last_reranked: list[RagHit] = []
# After
self.last_fetch_result: TwoStageFetchResult | None = None
```

**`pipeline.py` line 188 — run() terminal:**
```python
# Before
self.last_reranked = ctx.reranked
# After
self.last_fetch_result = TwoStageFetchResult(
    hits=ctx.reranked,
    min_score_applied=self._cfg.rag_min_score,
    max_chunks_per_doc=self._cfg.max_chunks_per_doc,
)
```

**`pipeline.py` line 211 — _augment_http():**
```python
# Before
hits = body.get("selected_hits", [])
if hits:
    self.last_reranked = hits
# After
hits = body.get("selected_hits", [])
if hits:
    self.last_fetch_result = TwoStageFetchResult(
        hits=hits,
        min_score_applied=0.0,
        max_chunks_per_doc=0,
    )
```

**`service.py:113` (and same pattern at 130):**
```python
# Before
selected_hits: list[dict[str, Any]] = [dict(h) for h in pipeline.last_reranked]
# After
_fetch_result = pipeline.last_fetch_result
selected_hits: list[dict[str, Any]] = (
    [dict(h) for h in _fetch_result.hits] if _fetch_result is not None else []
)
```

**`test_agent_rag.py` changes:**
```python
# line 80
# Before: assert pipeline.last_reranked == hits
assert pipeline.last_fetch_result is not None
assert pipeline.last_fetch_result.hits == hits

# line 103 (setup)
# Before: pipeline.last_reranked = [initial_hit]
from rag.models import TwoStageFetchResult
pipeline.last_fetch_result = TwoStageFetchResult(hits=[initial_hit], min_score_applied=0.0, max_chunks_per_doc=0)

# line 108
# Before: assert pipeline.last_reranked == [initial_hit]
assert pipeline.last_fetch_result is not None
assert pipeline.last_fetch_result.hits == [initial_hit]

# line 143
# Before: assert pipeline.last_reranked == []
assert pipeline.last_fetch_result is None
```

**`test_rag_pipeline_mcp_service.py` changes (pattern for all 12 occurrences):**
```python
from rag.models import TwoStageFetchResult
# lines with hits: pipeline.last_reranked = [hit]  →  pipeline.last_fetch_result = TwoStageFetchResult(hits=[hit], min_score_applied=0.0, max_chunks_per_doc=0)
# lines with empty: pipeline.last_reranked = []  →  pipeline.last_fetch_result = None
# Full list: 116(hit), 132(empty), 145(empty), 158(empty), 180(hit), 191(empty), 234(hit), 264(hit), 278(empty), 307(hit), 317(empty), 336(empty)
```

## Validation plan

- `grep -rn "last_reranked" scripts/ tests/` — 0 matches
- `uv run mypy scripts/rag/pipeline.py scripts/mcp/rag_pipeline/service.py` — 0 new errors
- `uv run pytest tests/test_agent_rag.py tests/test_rag_pipeline_mcp_service.py -v` — all pass
- `uv run ruff check scripts/rag/pipeline.py scripts/mcp/rag_pipeline/service.py` — 0 errors
