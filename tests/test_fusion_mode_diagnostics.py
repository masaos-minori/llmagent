"""tests/test_fusion_mode_diagnostics.py
Verifies fusion_mode in get_diagnostics() and FusionStage logger.info.
"""

from __future__ import annotations

import logging

import pytest
from rag.stage import PipelineContext
from rag.stages.fusion import FusionStage


def _make_pipeline(use_rrf: bool):
    """Return a minimal RagPipeline with mocked config."""
    from unittest.mock import MagicMock

    from rag.pipeline import RagPipeline
    from rag.models_result import SearchDiagnostics

    pipeline = RagPipeline.__new__(RagPipeline)
    pipeline._cfg = MagicMock()
    pipeline._cfg.use_rrf = use_rrf
    pipeline.last_stage_results = []
    pipeline.last_timings = {}
    pipeline.last_fetch_result = None
    pipeline.last_search_diagnostics = SearchDiagnostics()
    return pipeline


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
