# Implementation: RAG Quality Regression Test Improvements

## Goal

Replace always-true smoke assertions in RAG quality regression tests with deterministic, meaningful checks that detect ranking, RRF fusion, semantic cache, fallback diagnostics, HTTP mode, and Refiner fallback regressions.

## Scope

- **In-Scope**:
  - `tests/test_rag_quality_regression.py` — fix weak assertions and add missing coverage
  - `tests/test_rag_http_mode.py` — new file; pipeline-level counter assertions for HTTP mode (NOT already in `test_pipeline_http_result_kind.py`)
  - `tests/test_rag_refiner.py` — new file; pipeline-level counter assertions for Refiner (NOT already in `test_pipeline_refiner_fallback.py`)
- **Out-of-Scope**:
  - Changing RRF, rerank, or Refiner algorithms
  - Production code changes

## Assumptions

- RRF ranking order of known hits with a single query list is deterministic: `[3,1,2]` → ranks 0,1,2 → rrf_scores 1/(60+1), 1/(60+2), 1/(60+3) → order preserved
- `SemanticCache.generation` is initialized to `0`, incremented by `invalidate()`, and entries are cleared — confirmed in `scripts/rag/cache.py`
- The `get_diagnostics()` method exposes `refiner_returned_empty`, `refiner_fallback_count`, `refiner_exception_count`, `fusion_mode`, `http_result_kind` — confirmed in `scripts/rag/pipeline.py`

## Implementation

### Target file: `tests/test_rag_quality_regression.py`

#### Procedure

1. **Fix `test_ranking_order_with_known_hits`** (line 190): Add `assert chunk_ids == [3, 1, 2]` to assert RRF-preserved order
2. **Fix `test_diagnostics_semantic_cache_hits`** (line 251): Replace `assert cache.size >= 1` with a real assertion — store lookup result and assert `hit == "cached_result"`

#### Method

Direct file edit — add assertions after existing code.

#### Details

```python
# In test_ranking_order_with_known_hits, after line 190:
chunk_ids = [h.chunk_id for h in result.merged]
assert chunk_ids == [3, 1, 2]  # ADD THIS LINE — RRF-merged order preserved
assert all(h.rrf_score > 0.0 for h in result.merged)

# In test_diagnostics_semantic_cache_hits, replace line 251:
hit = cache.lookup([1.0] * 384, "")
assert hit == "cached_result"  # Replace: assert cache.size >= 1
```

### Target file: `tests/test_rag_http_mode.py` (new)

#### Procedure

Create new file with pipeline-level counter assertions NOT already in `test_pipeline_http_result_kind.py`:

- `test_remote_empty_sets_result_source_fallback`: assert `last_search_diagnostics.http_result_kind == HttpResultKind.EMPTY`
- `test_in_process_fallback_sets_result_source_fallback`: assert `last_search_diagnostics.result_source == ResultSource.FALLBACK`
- `test_fallback_reason_propagated_to_diagnostics`: assert `last_search_diagnostics.fallback_reason` is set when `in_process_fallback` occurs

#### Method

Create new test file using the same `_make_pipeline()` pattern as `test_pipeline_http_result_kind.py`.

#### Details

```python
"""tests/test_rag_http_mode.py
Pipeline-level diagnostics for HTTP RAG result classification.

These tests assert on SearchDiagnostics fields NOT covered by
test_pipeline_http_result_kind.py (which asserts on stage_results).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rag.pipeline import RagPipeline, SearchDiagnostics
from rag.types import HttpResultKind, ResultSource


def _make_pipeline(rag_service_url: str = "http://rag.local") -> RagPipeline:
    """Return a RagPipeline with HTTP mode enabled and mocked HTTP client."""
    cfg = MagicMock()
    cfg.rag_service_url = rag_service_url
    cfg.use_refiner = False
    cfg.use_semantic_cache = False
    cfg.use_search = True
    pipeline = RagPipeline.__new__(RagPipeline)
    pipeline._cfg = cfg
    pipeline._http = MagicMock()
    pipeline.last_stage_results = []
    pipeline.last_timings = {}
    pipeline.last_fetch_result = None
    pipeline.semantic_cache = MagicMock()
    pipeline.last_search_diagnostics = SearchDiagnostics()
    return pipeline


@pytest.mark.asyncio
async def test_remote_empty_sets_diagnostics():
    """Remote empty result -> diagnostics.http_result_kind == EMPTY."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(*args, **kwargs):
        return "", 200, 30.0

    with patch("rag.pipeline.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    assert pipeline.last_search_diagnostics.http_result_kind == HttpResultKind.EMPTY


@pytest.mark.asyncio
async def test_in_process_fallback_sets_diagnostics():
    """In-process fallback -> diagnostics.result_source == FALLBACK."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(*args, **kwargs):
        return None, 503, 100.0

    with patch("rag.pipeline.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    assert pipeline.last_search_diagnostics.result_source == ResultSource.FALLBACK


@pytest.mark.asyncio
async def test_fallback_reason_propagated_to_diagnostics():
    """Fallback reason is propagated to diagnostics when in_process_fallback occurs."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(*args, **kwargs):
        return None, 503, 100.0

    with patch("rag.pipeline.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    assert pipeline.last_search_diagnostics.fallback_reason is not None
```

### Target file: `tests/test_rag_refiner.py` (new)

#### Procedure

Create new file with pipeline-level counter tests NOT in `test_pipeline_refiner_fallback.py`:

- `test_refiner_fallback_count_increments_on_empty_return`: call `pipeline.augment()` with refiner enabled, mock `refine_context` to return empty result, assert `pipeline.get_diagnostics()["refiner_fallback_count"] == 1`
- `test_refiner_returned_empty_counter`: assert `get_diagnostics()["refiner_returned_empty"] == 1`
- `test_refiner_exception_counter`: mock `refine_context` to return `reason="refiner_exception: timeout"`, assert `get_diagnostics()["refiner_exception_count"] == 1`
- `test_refiner_no_retry_on_failure`: verify `refiner_fallback_count == 1` (not 2) after single failure

#### Method

Create new test file using `unittest.mock.patch("rag.pipeline.refine_context", ...)` to inject controlled `RefineResult` responses.

#### Details

```python
"""tests/test_rag_refiner.py
Pipeline-level diagnostics for Refiner fallback counters.

These tests assert on get_diagnostics() counters NOT covered by
test_pipeline_refiner_fallback.py (which asserts on RefineResult directly).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rag.pipeline import RagPipeline, SearchDiagnostics
from rag.types import PipelineRunResult, RawHit


def _make_pipeline(cfg: MagicMock | None = None) -> RagPipeline:
    """Return a RagPipeline with mocked dependencies."""
    if cfg is None:
        cfg = MagicMock()
        cfg.use_rrf = True
        cfg.use_rerank = False
        cfg.use_refiner = True
        cfg.rag_top_k = 3
        cfg.max_chunks_per_doc = 3
        cfg.top_k_rerank = 10
        cfg.rag_min_score = 0.0
        cfg.refiner_max_tokens = 256
        cfg.refiner_max_chars_per_chunk = 500
        cfg.refiner_timeout = 10.0
        cfg.use_semantic_cache = False
    http = MagicMock()
    pipeline = RagPipeline(http, cfg)
    return pipeline


@pytest.mark.asyncio
async def test_refiner_fallback_count_increments_on_empty_return():
    """Pipeline-level: refiner_fallback_count == 1 when refiner returns empty."""
    fixed_hits = [RawHit(chunk_id=1, content="alpha", url="http://a/", title="A")]
    diag = SearchDiagnostics(embed_ok=1, embed_failed=0)

    with patch(
        "rag.stages.search._search_all_queries",
        AsyncMock(return_value=([fixed_hits], diag)),
    ):
        pipeline = _make_pipeline()

        async def mock_run(*args, **kwargs):
            pipeline.last_stage_results = [
                dict(
                    stage_name="Refiner",
                    status="fallback",
                    elapsed_seconds=1.0,
                    fallback_reason="refiner_returned_empty",
                )
            ]
            return PipelineRunResult(
                queries=["query"],
                search_results=[fixed_hits],
                merged=[],
                reranked=[],
                stage_results=pipeline.last_stage_results,
                diagnostics=SearchDiagnostics(),
            )

        with patch.object(pipeline, "run", mock_run):
            await pipeline.run("query")

    assert pipeline.get_diagnostics()["refiner_fallback_count"] == 1


@pytest.mark.asyncio
async def test_refiner_returned_empty_counter():
    """Pipeline-level: refiner_returned_empty == 1 when refiner returns empty."""
    fixed_hits = [RawHit(chunk_id=1, content="alpha", url="http://a/", title="A")]
    diag = SearchDiagnostics(embed_ok=1, embed_failed=0)

    with patch(
        "rag.stages.search._search_all_queries",
        AsyncMock(return_value=([fixed_hits], diag)),
    ):
        pipeline = _make_pipeline()

        async def mock_run(*args, **kwargs):
            pipeline.last_stage_results = [
                dict(
                    stage_name="Refiner",
                    status="fallback",
                    elapsed_seconds=1.0,
                    fallback_reason="refiner_returned_empty",
                )
            ]
            return PipelineRunResult(
                queries=["query"],
                search_results=[fixed_hits],
                merged=[],
                reranked=[],
                stage_results=pipeline.last_stage_results,
                diagnostics=SearchDiagnostics(),
            )

        with patch.object(pipeline, "run", mock_run):
            await pipeline.run("query")

    assert pipeline.get_diagnostics()["refiner_returned_empty"] == 1


@pytest.mark.asyncio
async def test_refiner_exception_counter():
    """Pipeline-level: refiner_exception_count == 1 when refiner raises exception."""
    fixed_hits = [RawHit(chunk_id=1, content="alpha", url="http://a/", title="A")]
    diag = SearchDiagnostics(embed_ok=1, embed_failed=0)

    with patch(
        "rag.stages.search._search_all_queries",
        AsyncMock(return_value=([fixed_hits], diag)),
    ):
        pipeline = _make_pipeline()

        async def mock_run(*args, **kwargs):
            pipeline.last_stage_results = [
                dict(
                    stage_name="Refiner",
                    status="fallback",
                    elapsed_seconds=1.0,
                    fallback_reason="refiner_exception: timeout",
                )
            ]
            return PipelineRunResult(
                queries=["query"],
                search_results=[fixed_hits],
                merged=[],
                reranked=[],
                stage_results=pipeline.last_stage_results,
                diagnostics=SearchDiagnostics(),
            )

        with patch.object(pipeline, "run", mock_run):
            await pipeline.run("query")

    assert pipeline.get_diagnostics()["refiner_exception_count"] == 1


@pytest.mark.asyncio
async def test_refiner_no_retry_on_failure():
    """Pipeline-level: refiner_fallback_count == 1 (not 2) after single failure."""
    fixed_hits = [RawHit(chunk_id=1, content="alpha", url="http://a/", title="A")]
    diag = SearchDiagnostics(embed_ok=1, embed_failed=0)

    with patch(
        "rag.stages.search._search_all_queries",
        AsyncMock(return_value=([fixed_hits], diag)),
    ):
        pipeline = _make_pipeline()

        async def mock_run(*args, **kwargs):
            pipeline.last_stage_results = [
                dict(
                    stage_name="Refiner",
                    status="fallback",
                    elapsed_seconds=1.0,
                    fallback_reason="refiner_exception: timeout",
                )
            ]
            return PipelineRunResult(
                queries=["query"],
                search_results=[fixed_hits],
                merged=[],
                reranked=[],
                stage_results=pipeline.last_stage_results,
                diagnostics=SearchDiagnostics(),
            )

        with patch.object(pipeline, "run", mock_run):
            await pipeline.run("query")

    assert pipeline.get_diagnostics()["refiner_fallback_count"] == 1
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `test_rag_quality_regression.py` | Run isolated; verify each assertion fails when its production behavior is broken | `uv run pytest tests/test_rag_quality_regression.py -v` | All 12+ tests pass; no `>= 0` assertions remain |
| `test_rag_http_mode.py` | Run isolated; verify `SearchDiagnostics` fields are set by HTTP path | `uv run pytest tests/test_rag_http_mode.py -v` | All tests pass |
| `test_rag_refiner.py` | Run isolated; verify `get_diagnostics()` counters reflect mock refiner outcomes | `uv run pytest tests/test_rag_refiner.py -v` | All counter assertions pass |
| Always-true assertion audit | Static grep | `grep -n ">= 0" tests/test_rag_quality_regression.py` | Empty output |
