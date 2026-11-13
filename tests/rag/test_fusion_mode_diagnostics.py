"""tests/test_fusion_mode_diagnostics.py
Verifies fusion_mode in get_diagnostics() and FusionStage logger.info.
"""

from __future__ import annotations

import logging

import pytest
from rag.stage import PipelineContext
from rag.stages.fusion import FusionStage


def _make_pipeline(use_rrf: bool):
    """Return a RagPipeline built through __init__ with a stub config."""
    from types import SimpleNamespace
    from unittest.mock import MagicMock

    from rag.pipeline import RagPipeline

    cfg = SimpleNamespace(
        use_search=True,
        use_refiner=False,
        use_mqe=False,
        use_rerank=False,
        use_rrf=use_rrf,
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


def test_fusion_mode_rrf():
    """use_rrf=True -> get_diagnostics()['fusion_mode'] == 'rrf'."""
    pipeline = _make_pipeline(use_rrf=True)
    diag = pipeline.get_diagnostics()
    assert diag["fusion_mode"] == "rrf"


def test_fusion_mode_dedup_only():
    """use_rrf=False -> get_diagnostics()['fusion_mode'] == 'dedup_only'."""
    pipeline = _make_pipeline(use_rrf=False)
    diag = pipeline.get_diagnostics()
    assert diag["fusion_mode"] == "dedup_only"


@pytest.mark.asyncio
async def test_fusion_stage_logs_info_on_dedup(caplog):
    """FusionStage.run() with use_rrf=False logs INFO about dedup mode."""
    stage = FusionStage(use_rrf=False)
    ctx = PipelineContext(query="test", search_results=[[]])
    with caplog.at_level(logging.INFO, logger="rag.stages.fusion"):
        await stage.run(ctx)
    assert any("dedup-only mode" in r.message for r in caplog.records)
