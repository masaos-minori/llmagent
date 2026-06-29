"""tests/test_rag_refiner.py
Pipeline-level diagnostics for Refiner fallback counters and augment() fallback behavior.

These tests assert on get_diagnostics() counters NOT covered by
test_pipeline_refiner_fallback.py (which asserts on RefineResult directly).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from rag.models_result import SearchDiagnostics
from rag.pipeline import RagPipeline
from rag.pipeline_refiner import RefineResult, refine_context
from rag.types import PipelineRunResult, RawHit


def _make_pipeline() -> RagPipeline:
    """Return a RagPipeline with mocked dependencies (bypasses __init__)."""
    pipeline = RagPipeline.__new__(RagPipeline)
    pipeline._cfg = MagicMock()
    pipeline._cfg.use_rrf = True
    pipeline.last_stage_results = []
    pipeline.last_timings = {}
    pipeline.last_fetch_result = None
    pipeline.semantic_cache = MagicMock()
    pipeline.last_search_diagnostics = SearchDiagnostics()
    return pipeline


@pytest.mark.asyncio
async def test_refiner_fallback_count_increments_on_empty_return() -> None:
    """Pipeline-level: refiner_fallback_count == 1 when refiner returns empty."""
    pipeline = _make_pipeline()

    async def mock_run(*args, **kwargs):
        pipeline.last_stage_results = [
            {
                "stage_name": "Refiner",
                "status": "fallback",
                "elapsed_seconds": 1.0,
                "fallback_reason": "refiner_returned_empty",
            }
        ]
        return PipelineRunResult(
            queries=["query"],
            search_results=[],
            merged=[],
            reranked=[],
            stage_results=pipeline.last_stage_results,
            diagnostics=SearchDiagnostics(),
        )

    with patch.object(pipeline, "run", mock_run):
        await pipeline.run("query", MagicMock())

    assert pipeline.get_diagnostics()["refiner_fallback_count"] == 1


@pytest.mark.asyncio
async def test_refiner_returned_empty_counter() -> None:
    """Pipeline-level: refiner_returned_empty == 1 when refiner returns empty."""
    pipeline = _make_pipeline()

    async def mock_run(*args, **kwargs):
        pipeline.last_stage_results = [
            {
                "stage_name": "Refiner",
                "status": "fallback",
                "elapsed_seconds": 1.0,
                "fallback_reason": "refiner_returned_empty",
            }
        ]
        return PipelineRunResult(
            queries=["query"],
            search_results=[],
            merged=[],
            reranked=[],
            stage_results=pipeline.last_stage_results,
            diagnostics=SearchDiagnostics(),
        )

    with patch.object(pipeline, "run", mock_run):
        await pipeline.run("query", MagicMock())

    assert pipeline.get_diagnostics()["refiner_returned_empty"] == 1


@pytest.mark.asyncio
async def test_refiner_exception_counter() -> None:
    """Pipeline-level: refiner_exception_count == 1 when refiner raises exception."""
    pipeline = _make_pipeline()

    async def mock_run(*args, **kwargs):
        pipeline.last_stage_results = [
            {
                "stage_name": "Refiner",
                "status": "fallback",
                "elapsed_seconds": 1.0,
                "fallback_reason": "refiner_exception: timeout",
            }
        ]
        return PipelineRunResult(
            queries=["query"],
            search_results=[],
            merged=[],
            reranked=[],
            stage_results=pipeline.last_stage_results,
            diagnostics=SearchDiagnostics(),
        )

    with patch.object(pipeline, "run", mock_run):
        await pipeline.run("query", MagicMock())

    assert pipeline.get_diagnostics()["refiner_exception_count"] == 1


@pytest.mark.asyncio
async def test_refiner_no_retry_on_failure() -> None:
    """Pipeline-level: refiner_fallback_count == 1 (not 2) after single failure."""
    pipeline = _make_pipeline()

    async def mock_run(*args, **kwargs):
        pipeline.last_stage_results = [
            {
                "stage_name": "Refiner",
                "status": "fallback",
                "elapsed_seconds": 1.0,
                "fallback_reason": "refiner_exception: timeout",
            }
        ]
        return PipelineRunResult(
            queries=["query"],
            search_results=[],
            merged=[],
            reranked=[],
            stage_results=pipeline.last_stage_results,
            diagnostics=SearchDiagnostics(),
        )

    with patch.object(pipeline, "run", mock_run):
        await pipeline.run("query", MagicMock())

    assert pipeline.get_diagnostics()["refiner_fallback_count"] == 1


# ── refine_context() unit tests (function-level) ─────────────────────────────


def _make_llm(return_value: str | None = None, side_effect=None) -> MagicMock:
    llm = MagicMock()
    if side_effect is not None:
        llm.refine_context = AsyncMock(side_effect=side_effect)
    else:
        llm.refine_context = AsyncMock(return_value=return_value)
    return llm


def _noop_status(msg: str) -> None:
    pass


@pytest.mark.asyncio
async def test_refine_context_empty_string_is_fallback() -> None:
    """refine_context() with empty LLM output -> text is None, reason == 'refiner_returned_empty'."""
    llm = _make_llm(return_value="")
    result = await refine_context(llm, _noop_status, [], "query")
    assert result.text is None
    assert result.reason == "refiner_returned_empty"


@pytest.mark.asyncio
async def test_refine_context_exception_is_fallback() -> None:
    """refine_context() with HTTPStatusError -> text is None, reason starts with 'refiner_exception:'."""
    response = MagicMock()
    response.status_code = 500
    err = httpx.HTTPStatusError("server error", request=MagicMock(), response=response)
    llm = _make_llm(side_effect=err)
    result = await refine_context(llm, _noop_status, [], "query")
    assert result.text is None
    assert result.reason is not None
    assert result.reason.startswith("refiner_exception:")


@pytest.mark.asyncio
async def test_refine_context_no_retry() -> None:
    """refine_context() calls llm.refine_context exactly once on exception (no retry)."""
    response = MagicMock()
    response.status_code = 500
    err = httpx.HTTPStatusError("server error", request=MagicMock(), response=response)
    llm = _make_llm(side_effect=err)
    await refine_context(llm, _noop_status, [], "query")
    assert llm.refine_context.call_count == 1


# ── augment() integration tests ───────────────────────────────────────────────


def _make_refiner_pipeline() -> RagPipeline:
    """Return a RagPipeline with use_refiner=True and mocked dependencies."""
    pipeline = RagPipeline.__new__(RagPipeline)
    cfg = MagicMock()
    cfg.use_search = True
    cfg.rag_service_url = ""
    cfg.use_semantic_cache = False
    cfg.use_refiner = True
    cfg.rrf_k = 60
    cfg.use_rrf = True
    cfg.refiner_max_tokens = 256
    cfg.refiner_max_chars_per_chunk = 500
    cfg.refiner_timeout = 10.0
    pipeline._cfg = cfg
    pipeline._http = MagicMock()
    pipeline._llm = MagicMock()
    pipeline._on_status = lambda _: None
    pipeline._on_clear = lambda: None
    pipeline.last_stage_results = []
    pipeline.last_timings = {}
    pipeline.last_fetch_result = None
    pipeline.semantic_cache = MagicMock()
    pipeline.last_search_diagnostics = SearchDiagnostics()
    return pipeline


@pytest.mark.asyncio
async def test_augment_refiner_empty_falls_back_to_raw_chunks(monkeypatch) -> None:
    """augment() with refiner returning empty -> falls back to raw chunk format."""
    pipeline = _make_refiner_pipeline()
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)
    fixed_hit = RawHit(chunk_id=1, content="alpha", url="http://a/", title="A")

    monkeypatch.setattr(
        pipeline,
        "run",
        AsyncMock(
            return_value=PipelineRunResult(
                queries=["query"],
                search_results=[[fixed_hit]],
                merged=[],
                reranked=[fixed_hit],
                stage_results=[],
                diagnostics=SearchDiagnostics(),
            )
        ),
    )
    with (
        patch(
            "rag.pipeline.refine_context",
            AsyncMock(
                return_value=RefineResult(text=None, reason="refiner_returned_empty")
            ),
        ),
        patch(
            "rag.pipeline.SQLiteHelper",
            return_value=MagicMock(open=MagicMock(return_value=mock_db)),
        ),
    ):
        result = await pipeline.augment("query")

    assert "[RAG_CONTEXT_START]" in result


@pytest.mark.asyncio
async def test_augment_refiner_exception_falls_back_to_raw_chunks(monkeypatch) -> None:
    """augment() with refiner exception fallback -> falls back to raw chunk format."""
    pipeline = _make_refiner_pipeline()
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)
    fixed_hit = RawHit(chunk_id=1, content="alpha", url="http://a/", title="A")

    monkeypatch.setattr(
        pipeline,
        "run",
        AsyncMock(
            return_value=PipelineRunResult(
                queries=["query"],
                search_results=[[fixed_hit]],
                merged=[],
                reranked=[fixed_hit],
                stage_results=[],
                diagnostics=SearchDiagnostics(),
            )
        ),
    )
    with (
        patch(
            "rag.pipeline.refine_context",
            AsyncMock(
                return_value=RefineResult(
                    text=None, reason="refiner_exception: network error"
                )
            ),
        ),
        patch(
            "rag.pipeline.SQLiteHelper",
            return_value=MagicMock(open=MagicMock(return_value=mock_db)),
        ),
    ):
        result = await pipeline.augment("query")

    assert "[RAG_CONTEXT_START]" in result


@pytest.mark.asyncio
async def test_augment_refiner_exception_diagnostic_not_silent(monkeypatch) -> None:
    """After augment() with refiner exception, diagnostics show fallback and exception count."""
    pipeline = _make_refiner_pipeline()
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)
    fixed_hit = RawHit(chunk_id=1, content="alpha", url="http://a/", title="A")

    monkeypatch.setattr(
        pipeline,
        "run",
        AsyncMock(
            return_value=PipelineRunResult(
                queries=["query"],
                search_results=[[fixed_hit]],
                merged=[],
                reranked=[fixed_hit],
                stage_results=[],
                diagnostics=SearchDiagnostics(),
            )
        ),
    )
    with (
        patch(
            "rag.pipeline.refine_context",
            AsyncMock(
                return_value=RefineResult(
                    text=None, reason="refiner_exception: timeout"
                )
            ),
        ),
        patch(
            "rag.pipeline.SQLiteHelper",
            return_value=MagicMock(open=MagicMock(return_value=mock_db)),
        ),
    ):
        await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["refiner_fallback_count"] >= 1
    assert diag["refiner_exception_count"] >= 1


@pytest.mark.asyncio
async def test_augment_refiner_empty_diagnostic_visible(monkeypatch) -> None:
    """After augment() with refiner returning empty, diagnostics show refiner_returned_empty."""
    pipeline = _make_refiner_pipeline()
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)
    fixed_hit = RawHit(chunk_id=1, content="alpha", url="http://a/", title="A")

    monkeypatch.setattr(
        pipeline,
        "run",
        AsyncMock(
            return_value=PipelineRunResult(
                queries=["query"],
                search_results=[[fixed_hit]],
                merged=[],
                reranked=[fixed_hit],
                stage_results=[],
                diagnostics=SearchDiagnostics(),
            )
        ),
    )
    with (
        patch(
            "rag.pipeline.refine_context",
            AsyncMock(
                return_value=RefineResult(text=None, reason="refiner_returned_empty")
            ),
        ),
        patch(
            "rag.pipeline.SQLiteHelper",
            return_value=MagicMock(open=MagicMock(return_value=mock_db)),
        ),
    ):
        await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["refiner_returned_empty"] >= 1
