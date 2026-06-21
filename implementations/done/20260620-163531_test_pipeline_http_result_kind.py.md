# Implementation: test_pipeline_http_result_kind.py

## Goal
Create `tests/test_pipeline_http_result_kind.py` to verify that `augment()` and
`get_diagnostics()` correctly classify HTTP RAG results into `remote_nonempty`,
`remote_empty`, and `in_process_fallback`, and that `fallback_reason="http_remote_empty"`
is set on the `HttpAugment` stage result when the remote returns `""`.

## Scope
- New file: `tests/test_pipeline_http_result_kind.py`
- Tests for:
  1. Non-empty remote result → `http_result_kind="remote_nonempty"`, `fallback_reason=None`
  2. Empty remote result (`""`) → `http_result_kind="remote_empty"`, `fallback_reason="http_remote_empty"`
  3. `None` remote result (error) → `http_result_kind="in_process_fallback"`
  4. No `rag_service_url` configured → `http_result_kind=None`

## Assumptions
- `RagPipeline` can be constructed with a minimal config that sets `rag_service_url`
- `call_rag_service()` can be mocked at the module level or via monkeypatch on the pipeline instance
- `_augment_http()` is the internal method that calls `call_rag_service()`; mock it to return
  the desired result directly and set `http_fallback_reasons`
- `last_stage_results` is directly inspectable after `augment()` returns

## Implementation

### Target file
`tests/test_pipeline_http_result_kind.py`

### Procedure
Write a pytest test file with 4 test cases.

### Method
New test file. Mock `RagPipeline._augment_http()` via `unittest.mock.AsyncMock` or
monkeypatch the `call_rag_service` function.

### Details

```python
"""tests/test_pipeline_http_result_kind.py
Verifies HTTP RAG result classification in augment() and get_diagnostics().
"""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag.pipeline import RagPipeline


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
    return pipeline


@pytest.mark.asyncio
async def test_remote_nonempty(monkeypatch) -> None:
    """Non-empty remote result → http_result_kind='remote_nonempty'."""
    pipeline = _make_pipeline()

    async def mock_augment_http(query, history_context, set_fallback_reason):
        return "context text"

    monkeypatch.setattr(pipeline, "_augment_http", mock_augment_http)
    await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == "remote_nonempty"
    http_sr = next(r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment")
    assert http_sr["status"] == "success"
    assert http_sr["fallback_reason"] is None


@pytest.mark.asyncio
async def test_remote_empty(monkeypatch) -> None:
    """Empty remote result ('') → http_result_kind='remote_empty', fallback_reason='http_remote_empty'."""
    pipeline = _make_pipeline()

    async def mock_augment_http(query, history_context, set_fallback_reason):
        return ""

    monkeypatch.setattr(pipeline, "_augment_http", mock_augment_http)
    await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == "remote_empty"
    http_sr = next(r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment")
    assert http_sr["status"] == "success"
    assert http_sr["fallback_reason"] == "http_remote_empty"


@pytest.mark.asyncio
async def test_in_process_fallback(monkeypatch) -> None:
    """None remote result → http_result_kind='in_process_fallback'."""
    pipeline = _make_pipeline()

    async def mock_augment_http(query, history_context, set_fallback_reason):
        set_fallback_reason("connection error")
        return None

    monkeypatch.setattr(pipeline, "_augment_http", mock_augment_http)
    # Also mock the in-process pipeline steps to avoid real execution
    monkeypatch.setattr(pipeline, "_run_stages", AsyncMock(return_value=""))
    await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == "in_process_fallback"
    http_sr = next(r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment")
    assert http_sr["status"] == "fallback"


@pytest.mark.asyncio
async def test_no_http_mode(monkeypatch) -> None:
    """No rag_service_url → http_result_kind=None."""
    pipeline = _make_pipeline(rag_service_url="")
    # No _augment_http called; mock in-process stages
    monkeypatch.setattr(pipeline, "_run_stages", AsyncMock(return_value=""))
    await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] is None
```

**Note:** The exact method signatures for `_augment_http()` and `_run_stages()` must be
confirmed against the actual `pipeline.py` before writing the final implementation.
Adjust monkeypatch targets as needed.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| All 4 tests pass | `uv run pytest tests/test_pipeline_http_result_kind.py -v` | 4 passed |
| Lint | `uv run ruff check tests/test_pipeline_http_result_kind.py` | 0 errors |
| Type check | `uv run mypy tests/test_pipeline_http_result_kind.py` | no errors |
| Full suite | `uv run pytest -q` | no new failures |
