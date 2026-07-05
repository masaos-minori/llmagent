"""tests/test_pipeline_http_result_kind.py
Verifies HTTP RAG result classification in augment() and get_diagnostics().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rag.models_result import HttpResultKind, ResultSource
from rag.pipeline import RagPipeline, SearchDiagnostics
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
    from rag.pipeline import SearchDiagnostics

    pipeline.last_search_diagnostics = SearchDiagnostics()
    pipeline._rag_db_path = ""
    pipeline._sqlite_vec_so = ""
    pipeline._sqlite_timeout = 30
    pipeline._sqlite_busy_timeout_ms = 30000
    return pipeline


@pytest.mark.asyncio
async def test_remote_nonempty(monkeypatch) -> None:
    """Non-empty remote result -> http_result_kind='remote_nonempty'."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(
        http,
        rag_url,
        query,
        history_context,
        *,
        auth_token="",
        set_fetch_result=None,
        set_fallback_reason=None,
    ):
        return "context text", 200, 50.0

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == "remote_nonempty"
    sd = pipeline.last_search_diagnostics
    assert sd.result_source == ResultSource.REMOTE
    assert sd.remote_status_code == 200
    assert sd.remote_latency_ms == 50.0
    assert sd.fallback_reason is None
    http_sr = next(
        r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment"
    )
    assert http_sr["status"] == "success"
    assert http_sr["fallback_reason"] is None


@pytest.mark.asyncio
async def test_remote_empty(monkeypatch) -> None:
    """Empty remote result ('') -> http_result_kind='remote_empty', fallback_reason=None."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(
        http,
        rag_url,
        query,
        history_context,
        *,
        auth_token="",
        set_fetch_result=None,
        set_fallback_reason=None,
    ):
        return "", 200, 30.0

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        with patch("rag.pipeline.SQLiteHelper.open") as mock_open:
            await pipeline.augment("query")

    # remote_empty must NOT trigger in-process pipeline
    mock_open.assert_not_called()

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == "remote_empty"
    sd = pipeline.last_search_diagnostics
    assert sd.result_source == ResultSource.REMOTE
    assert sd.http_result_kind == HttpResultKind.EMPTY
    assert sd.remote_status_code == 200
    assert sd.remote_latency_ms == 30.0
    assert sd.fallback_reason is None
    http_sr = next(
        r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment"
    )
    assert http_sr["status"] == "success"
    assert http_sr["fallback_reason"] is None


@pytest.mark.asyncio
async def test_in_process_fallback(monkeypatch) -> None:
    """None remote result -> http_result_kind='in_process_fallback'."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(
        http,
        rag_url,
        query,
        history_context,
        *,
        auth_token="",
        set_fetch_result=None,
        set_fallback_reason=None,
    ):
        if set_fallback_reason:
            set_fallback_reason("connection error")
        return None, 503, 100.0

    with patch("rag.http_augment.call_rag_service", mock_call_rag_service):
        with patch("rag.pipeline.SQLiteHelper.open"):
            # Also mock the in-process pipeline steps to avoid real execution
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
            await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == "in_process_fallback"
    sd = pipeline.last_search_diagnostics
    assert sd.result_source == ResultSource.FALLBACK
    assert sd.http_result_kind == HttpResultKind.ERROR
    assert sd.remote_status_code == 503
    assert sd.remote_latency_ms == 100.0
    http_sr = next(
        r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment"
    )
    assert http_sr["status"] == "fallback"
    assert http_sr.get("fallback_reason") is not None


@pytest.mark.asyncio
async def test_no_http_mode(monkeypatch) -> None:
    """No rag_service_url -> http_result_kind=None."""
    pipeline = _make_pipeline(rag_service_url="")
    # No HTTP call; mock in-process stages
    with patch("rag.pipeline.SQLiteHelper.open"):
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
        await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] is None
