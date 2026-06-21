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
    """Non-empty remote result -> http_result_kind='remote_nonempty'."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(
        http, rag_url, query, history_context, *, auth_token="", set_fetch_result=None, set_fallback_reason=None
    ):
        return "context text"

    with patch("rag.pipeline.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == "remote_nonempty"
    http_sr = next(
        r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment"
    )
    assert http_sr["status"] == "success"
    assert http_sr["fallback_reason"] is None


@pytest.mark.asyncio
async def test_remote_empty(monkeypatch) -> None:
    """Empty remote result ('') -> http_result_kind='remote_empty', fallback_reason='http_remote_empty'."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(
        http, rag_url, query, history_context, *, auth_token="", set_fetch_result=None, set_fallback_reason=None
    ):
        return ""

    with patch("rag.pipeline.call_rag_service", mock_call_rag_service):
        await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == "remote_empty"
    http_sr = next(
        r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment"
    )
    assert http_sr["status"] == "success"
    assert http_sr["fallback_reason"] == "http_remote_empty"


@pytest.mark.asyncio
async def test_in_process_fallback(monkeypatch) -> None:
    """None remote result -> http_result_kind='in_process_fallback'."""
    pipeline = _make_pipeline()

    async def mock_call_rag_service(
        http, rag_url, query, history_context, *, auth_token="", set_fetch_result=None, set_fallback_reason=None
    ):
        if set_fallback_reason:
            set_fallback_reason("connection error")
        return None

    with patch("rag.pipeline.call_rag_service", mock_call_rag_service):
        # Also mock the in-process pipeline steps to avoid real execution
        monkeypatch.setattr(pipeline, "run", AsyncMock(return_value=("query", [], [], [])))
        await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] == "in_process_fallback"
    http_sr = next(
        r for r in pipeline.last_stage_results if r["stage_name"] == "HttpAugment"
    )
    assert http_sr["status"] == "fallback"


@pytest.mark.asyncio
async def test_no_http_mode(monkeypatch) -> None:
    """No rag_service_url -> http_result_kind=None."""
    pipeline = _make_pipeline(rag_service_url="")
    # No HTTP call; mock in-process stages
    monkeypatch.setattr(pipeline, "run", AsyncMock(return_value=("query", [], [], [])))
    await pipeline.augment("query")

    diag = pipeline.get_diagnostics()
    assert diag["http_result_kind"] is None
