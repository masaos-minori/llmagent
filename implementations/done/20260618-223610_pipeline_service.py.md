# Implementation: Improve Ingestion and Query Diagnostics — Pipeline Service

## Goal

Preserve `min_score_applied`/`max_chunks_per_doc` from HTTP response body in `call_rag_service()`.

## Scope

- `scripts/rag/pipeline_service.py` — parse `min_score_applied`/`max_chunks_per_doc` from HTTP response body

## Assumptions

1. External RAG service response body may include `min_score_applied` and `max_chunks_per_doc` fields (to be documented as API contract).
2. `TwoStageFetchResult` already has these fields (`models_data.py:60-65`).

## Current State

### HTTP response handling (`pipeline_service.py:67-74`)

```python
body = orjson.loads(resp.content)
hits = body.get("selected_hits", [])
if hits:
    set_fetch_result(
        TwoStageFetchResult(
            hits=hits,
            min_score_applied=0.0,  # <-- hardcoded
            max_chunks_per_doc=0,   # <-- hardcoded
        )
    )
```

**Gap:** `min_score_applied` and `max_chunks_per_doc` are always `0` — the external service's actual values are not extracted from the response body.

### TwoStageFetchResult (`models_data.py:60-65`)

```python
@dataclass(frozen=True)
class TwoStageFetchResult:
    hits: list[Any]  # list[RagHit] in-process; list[dict] HTTP mode
    min_score_applied: float  # rag_min_score used (0.0 = no score filter)
    max_chunks_per_doc: int  # per-doc dedup limit applied
```

Fields exist — just need to populate them from HTTP response body.

## Proposed Changes

### `pipeline_service.py` lines 67-74

```python
body = orjson.loads(resp.content)
hits = body.get("selected_hits", [])
min_score = body.get("min_score_applied", 0.0)
max_chunks = body.get("max_chunks_per_doc", 0)
if hits:
    set_fetch_result(
        TwoStageFetchResult(
            hits=hits,
            min_score_applied=float(min_score),
            max_chunks_per_doc=int(max_chunks),
        )
    )
```

### Fallback paths (no change needed)

The existing fallback paths (4xx, transport error, JSON parse error, all retries exhausted on 5xx) return `None` and do NOT call `set_fetch_result`. This is correct — no hits means no fetch result to store. The in-process pipeline will handle the query when `context_raw` is `None`.

## Implementation Steps (for future code implementation)

1. Extract `min_score_applied` and `max_chunks_per_doc` from HTTP response body before constructing `TwoStageFetchResult`
2. Cast to `float` / `int` for type safety
3. Default to `0.0` / `0` if fields are absent in the response body

## Validation plan

| Check | Tool | Target |
|---|---|---|
| HTTP response fields propagated | Manual: mock RAG service returning `min_score_applied=0.3`, `max_chunks_per_doc=5` | `last_fetch_result.min_score_applied == 0.3`, `last_fetch_result.max_chunks_per_doc == 5` |
| Missing fields default to 0 | Manual: mock RAG service without these fields | `min_score_applied == 0.0`, `max_chunks_per_doc == 0` |
| Lint | `ruff check scripts/rag/pipeline_service.py` | 0 errors |
| Type check | `mypy scripts/rag/pipeline_service.py` | no new errors |
