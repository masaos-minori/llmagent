"""tests/test_rag_http_mode.py
Pipeline-level diagnostics for HTTP RAG result classification.

These tests assert on SearchDiagnostics fields NOT covered by
test_pipeline_http_result_kind.py (which asserts on stage_results).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rag.models_result import HttpResultKind, ResultSource, SearchDiagnostics
from rag.pipeline import RagPipeline
from rag.types import PipelineRunResult


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
async def test_remote_empty_sets_result_source_remote() -> None:
    """Remote empty result ('') -> last_search_diagnostics.http_result_kind == EMPTY."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(*args, **kwargs):
        return "", 200, 30.0

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    assert pipeline.last_search_diagnostics.http_result_kind == HttpResultKind.EMPTY
    sd = pipeline.last_search_diagnostics
    assert sd.result_source == ResultSource.REMOTE
    assert sd.remote_status_code == 200
    assert sd.remote_latency_ms == 30.0
    assert sd.fallback_reason is None


@pytest.mark.asyncio
async def test_remote_empty_does_not_trigger_in_process(monkeypatch) -> None:
    """remote_empty (status 200, empty result) must NOT fall back to in-process pipeline."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(*args, **kwargs):
        return "", 200, 5.0

    run_mock = AsyncMock()
    monkeypatch.setattr(pipeline, "run", run_mock)

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        result = await pipeline.augment("test query")

    assert result == ""
    run_mock.assert_not_called()


@pytest.mark.asyncio
async def test_in_process_fallback_sets_result_source_fallback(monkeypatch) -> None:
    """In-process fallback -> last_search_diagnostics.result_source == FALLBACK."""
    pipeline = _make_pipeline()
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    async def mock_call_rag_service(*args, **kwargs):
        return None, 503, 100.0

    monkeypatch.setattr(
        pipeline,
        "run",
        AsyncMock(
            return_value=PipelineRunResult(
                queries=["query"],
                search_results=[],
                merged=[],
                reranked=[],
                stage_results=[],
                diagnostics=SearchDiagnostics(),
            )
        ),
    )
    with (
        patch("rag.http_augment.call_rag_service", mock_call_rag_service),
        patch(
            "rag.pipeline.SQLiteHelper",
            return_value=MagicMock(open=MagicMock(return_value=mock_db)),
        ),
    ):
        await pipeline.augment("query")

    assert pipeline.last_search_diagnostics.result_source == ResultSource.FALLBACK
    sd = pipeline.last_search_diagnostics
    assert sd.http_result_kind == HttpResultKind.ERROR
    assert sd.remote_status_code == 503
    assert sd.remote_latency_ms == 100.0
    assert any(
        r.get("fallback_reason") is not None for r in pipeline.last_stage_results
    )


@pytest.mark.asyncio
async def test_fallback_reason_propagated_to_diagnostics(monkeypatch) -> None:
    """Fallback reason is propagated to diagnostics when in_process_fallback occurs."""
    pipeline = _make_pipeline()
    mock_db = MagicMock()
    mock_db.__enter__ = MagicMock(return_value=mock_db)
    mock_db.__exit__ = MagicMock(return_value=False)

    async def mock_call_rag_service(*args, **kwargs):
        if kwargs.get("set_fallback_reason"):
            kwargs["set_fallback_reason"]("connection refused")
        return None, 503, 100.0

    monkeypatch.setattr(
        pipeline,
        "run",
        AsyncMock(
            return_value=PipelineRunResult(
                queries=["query"],
                search_results=[],
                merged=[],
                reranked=[],
                stage_results=[],
                diagnostics=SearchDiagnostics(),
            )
        ),
    )
    with (
        patch("rag.http_augment.call_rag_service", mock_call_rag_service),
        patch(
            "rag.pipeline.SQLiteHelper",
            return_value=MagicMock(open=MagicMock(return_value=mock_db)),
        ),
    ):
        await pipeline.augment("query")

    assert any(
        r.get("fallback_reason") is not None for r in pipeline.last_stage_results
    )
