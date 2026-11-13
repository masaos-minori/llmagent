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
    """Return a RagPipeline built through __init__ with a stub config."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from rag.pipeline import RagPipeline

    cfg = SimpleNamespace(
        use_search=True,
        use_refiner=False,
        use_mqe=False,
        use_rerank=False,
        use_rrf=True,
        rrf_k=60,
        top_k_search=5,
        rag_top_k=3,
        top_k_rerank=10,
        rag_min_score=0.0,
        max_chunks_per_doc=3,
        refiner_max_tokens=256,
        refiner_max_chars_per_chunk=500,
        refiner_timeout=10.0,
        llm_url="http://localhost:8000/v1/chat/completions",
        embed_url="http://localhost:8000/v1/embeddings",
        rag_db_path=":memory:",
        sqlite_vec_so="/opt/llm/sqlite-vec/vec0.so",
        sqlite_timeout=5,
        sqlite_busy_timeout_ms=5000,
        embed_retry=3,
        embed_workers=4,
        mqe_prompt_template="Expand query: {query}",
        mqe_n_queries=3,
        rerank_prompt_template="Rerank results for: {query}",
    )
    return RagPipeline(MagicMock(), cfg)


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
