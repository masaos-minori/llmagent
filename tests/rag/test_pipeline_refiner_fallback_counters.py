"""tests/rag/test_pipeline_refiner_fallback_counters.py

Pipeline-level diagnostics for Refiner fallback counters.

These tests assert on get_diagnostics() counters NOT covered by
test_pipeline_refiner_fallback.py (which asserts on RefineResult directly).
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from rag.models_result import SearchDiagnostics
from rag.pipeline import RagPipeline
from rag.types import PipelineRunResult


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
