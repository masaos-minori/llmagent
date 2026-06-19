"""tests/test_stage_observability.py
Tests for RagPipeline stage-level observability (last_stage_results).
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rag.pipeline import RagPipeline
from rag.stage import StageResult  # noqa: F401 — imported to verify public symbol


def _make_cfg(**overrides: object) -> SimpleNamespace:
    defaults: dict[str, object] = dict(
        use_mqe=False,
        use_rrf=True,
        use_rerank=False,
        use_refiner=False,
        use_search=True,
        rag_service_url="",
        rag_auth_token="",
        rrf_k=60,
        use_semantic_cache=False,
        top_k_search=5,
        top_k_rerank=10,
        rag_top_k=3,
        rag_min_score=0.0,
        max_chunks_per_doc=3,
        semantic_cache_max_size=10,
        semantic_cache_threshold=0.9,
        refiner_max_tokens=512,
        refiner_max_chars_per_chunk=800,
        refiner_timeout=30.0,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def _make_pipeline(cfg: SimpleNamespace) -> RagPipeline:
    http = AsyncMock()
    with patch("rag.pipeline._ModuleConfig.get", return_value={}):
        return RagPipeline(http, cfg)


class TestStageObservability:
    @pytest.mark.asyncio
    async def test_mqe_disabled_produces_fallback_status(self) -> None:
        """MqeStage records fallback when use_mqe=False."""
        cfg = _make_cfg(use_mqe=False)
        pipeline = _make_pipeline(cfg)
        db = MagicMock()
        await pipeline.run("test query", db)
        statuses = {r["stage_name"]: r["status"] for r in pipeline.last_stage_results}
        reasons = {
            r["stage_name"]: r["fallback_reason"] for r in pipeline.last_stage_results
        }
        assert statuses["MqeStage"] == "fallback"
        assert reasons["MqeStage"] == "use_mqe=False"

    @pytest.mark.asyncio
    async def test_empty_search_produces_fallback_status(self) -> None:
        """SearchStage records fallback when no chunks are found (empty DB)."""
        cfg = _make_cfg(use_mqe=True)
        pipeline = _make_pipeline(cfg)
        pipeline._llm = MagicMock()
        pipeline._llm.expand_queries = AsyncMock(return_value=["test query"])
        db = MagicMock()
        await pipeline.run("test query", db)
        statuses = {r["stage_name"]: r["status"] for r in pipeline.last_stage_results}
        reasons = {
            r["stage_name"]: r["fallback_reason"] for r in pipeline.last_stage_results
        }
        assert statuses["SearchStage"] == "fallback"
        assert reasons["SearchStage"] == "no search results"

    @pytest.mark.asyncio
    async def test_rerank_disabled_produces_fallback_status(self) -> None:
        """RerankStage records fallback when use_rerank=False."""
        cfg = _make_cfg(use_rerank=False)
        pipeline = _make_pipeline(cfg)
        db = MagicMock()
        await pipeline.run("test query", db)
        statuses = {r["stage_name"]: r["status"] for r in pipeline.last_stage_results}
        reasons = {
            r["stage_name"]: r["fallback_reason"] for r in pipeline.last_stage_results
        }
        assert statuses["RerankStage"] == "fallback"
        assert reasons["RerankStage"] == "use_rerank=False"

    @pytest.mark.asyncio
    async def test_all_stages_recorded_with_elapsed(self) -> None:
        """Every pre-augment stage and AugmentStage appear in last_stage_results with non-negative elapsed."""
        cfg = _make_cfg(use_mqe=False, use_rrf=True, use_rerank=False)
        pipeline = _make_pipeline(cfg)
        db = MagicMock()
        await pipeline.run("test query", db)
        names = [r["stage_name"] for r in pipeline.last_stage_results]
        assert "MqeStage" in names
        assert "SearchStage" in names
        assert "FusionStage" in names
        assert "RerankStage" in names
        assert "AugmentStage" in names
        for r in pipeline.last_stage_results:
            assert r["elapsed_seconds"] >= 0.0
