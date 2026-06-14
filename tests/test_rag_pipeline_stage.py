"""tests/test_rag_pipeline_stage.py
Unit tests for RAG pipeline stages and observer functionality.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rag.stage import PipelineContext
from rag.stages.augment import AugmentStage
from rag.stages.fusion import FusionStage
from rag.stages.mqe import MqeStage
from rag.stages.rerank import RerankStage
from rag.stages.search import SearchStage


class TestPipelineContextFields:
    """Test PipelineContext field defaults."""

    def test_context_initializes_with_empty_lists(self) -> None:
        ctx = PipelineContext(query="test query")
        assert ctx.queries == []
        assert ctx.search_results == []
        assert ctx.merged == []
        assert ctx.reranked == []


# ---------------------------------------------------------------------------
# MqeStage
# ---------------------------------------------------------------------------


class TestMqeStage:
    @pytest.mark.asyncio
    async def test_mqe_disabled_returns_original_query(self) -> None:
        llm = MagicMock()
        stage = MqeStage({"use_mqe": False}, llm)
        ctx = PipelineContext(query="hello")
        await stage.run(ctx)
        assert ctx.queries == ["hello"]

    @pytest.mark.asyncio
    async def test_mqe_enabled_calls_llm_expand(self) -> None:
        llm = MagicMock()
        llm.expand_queries = AsyncMock(return_value=["hello", "hi there"])
        stage = MqeStage({"use_mqe": True}, llm)
        ctx = PipelineContext(query="hello")
        await stage.run(ctx)
        assert ctx.queries == ["hello", "hi there"]
        llm.expand_queries.assert_called_once_with("hello")

    @pytest.mark.asyncio
    async def test_mqe_raises_on_llm_error(self) -> None:
        """MqeStage propagates RagExpansionError instead of falling back."""
        llm = MagicMock()
        llm.expand_queries = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
        stage = MqeStage({"use_mqe": True}, llm)
        ctx = PipelineContext(query="hello")
        with pytest.raises(RuntimeError, match="LLM unavailable"):
            await stage.run(ctx)


# ---------------------------------------------------------------------------
# SearchStage
# ---------------------------------------------------------------------------


class TestSearchStage:
    @pytest.mark.asyncio
    async def test_search_none_db_returns_empty(self) -> None:
        stage = SearchStage({"top_k_search": 5})
        ctx = PipelineContext(query="q")
        ctx.queries = ["q"]
        await stage.run(ctx, db=None)
        assert ctx.search_results == []

    @pytest.mark.asyncio
    async def test_search_calls_repository(self) -> None:
        stage = SearchStage({"top_k_search": 5})
        ctx = PipelineContext(query="q")
        ctx.queries = ["q"]
        mock_db = MagicMock()

        from rag.types import RawHit

        with patch(
            "rag.stages.search._search_all_queries", new_callable=AsyncMock
        ) as mock_search:
            mock_search.return_value = [[RawHit(chunk_id=1, content="a", url="u")]]
            await stage.run(ctx, db=mock_db)

        assert len(ctx.search_results) == 1
        mock_search.assert_called_once()


# ---------------------------------------------------------------------------
# FusionStage
# ---------------------------------------------------------------------------


class TestFusionStage:
    @pytest.mark.asyncio
    async def test_fusion_empty_results_yields_empty_merged(self) -> None:
        stage = FusionStage({"rrf_k": 60})
        ctx = PipelineContext(query="q")
        ctx.search_results = []
        await stage.run(ctx)
        assert ctx.merged == []

    @pytest.mark.asyncio
    async def test_fusion_combines_multiple_result_lists(self) -> None:
        from rag.types import RawHit

        stage = FusionStage({"rrf_k": 60})
        ctx = PipelineContext(query="q")
        hit1 = RawHit(chunk_id=1, content="a", url="u1")
        hit2 = RawHit(chunk_id=2, content="b", url="u2")
        ctx.search_results = [[hit1], [hit2]]  # type: ignore[assignment]
        await stage.run(ctx)
        chunk_ids = {h.chunk_id for h in ctx.merged}
        assert {1, 2}.issubset(chunk_ids)


# ---------------------------------------------------------------------------
# RerankStage
# ---------------------------------------------------------------------------


class TestRerankStage:
    @pytest.mark.asyncio
    async def test_rerank_disabled_returns_top_k(self) -> None:
        llm = MagicMock()
        cfg = {
            "use_rerank": False,
            "rag_top_k": 2,
            "max_chunks_per_doc": 5,
            "top_k_rerank": 10,
            "rag_min_score": 0.0,
        }
        stage = RerankStage(cfg, llm)
        from rag.types import MergedHit

        hits = [MergedHit(chunk_id=i, content=f"c{i}", url="u") for i in range(5)]
        ctx = PipelineContext(query="q")
        ctx.merged = hits  # type: ignore[assignment]
        await stage.run(ctx)
        assert len(ctx.reranked) <= 2

    @pytest.mark.asyncio
    async def test_rerank_enabled_calls_cross_encoder(self) -> None:
        llm = MagicMock()
        from rag.types import MergedHit, RankedHit

        expected_merged = [MergedHit(chunk_id=1, content="a", url="u")]
        expected_ranked = [
            RankedHit(chunk_id=1, content="a", url="u", rerank_score=0.95)
        ]
        llm.cross_encoder_rerank = AsyncMock(return_value=expected_ranked)
        cfg = {
            "use_rerank": True,
            "rag_top_k": 2,
            "max_chunks_per_doc": 5,
            "top_k_rerank": 10,
            "rag_min_score": 0.0,
        }
        stage = RerankStage(cfg, llm)
        ctx = PipelineContext(query="q")
        ctx.merged = expected_merged  # type: ignore[assignment]
        await stage.run(ctx)
        llm.cross_encoder_rerank.assert_called_once()

    @pytest.mark.asyncio
    async def test_rerank_raises_on_error(self) -> None:
        """RerankStage propagates RagRerankError instead of falling back to RRF order."""
        from rag.llm import RagRerankError

        llm = MagicMock()
        llm.cross_encoder_rerank = AsyncMock(
            side_effect=RagRerankError("rerank failed")
        )
        cfg = {
            "use_rerank": True,
            "rag_top_k": 2,
            "max_chunks_per_doc": 5,
            "top_k_rerank": 10,
            "rag_min_score": 0.0,
        }
        stage = RerankStage(cfg, llm)
        from rag.types import MergedHit

        hits = [MergedHit(chunk_id=i, content=f"c{i}", url="u") for i in range(3)]
        ctx = PipelineContext(query="q")
        ctx.merged = hits  # type: ignore[assignment]
        with pytest.raises(RagRerankError, match="rerank failed"):
            await stage.run(ctx)


# ---------------------------------------------------------------------------
# AugmentStage
# ---------------------------------------------------------------------------


class TestAugmentStage:
    @pytest.mark.asyncio
    async def test_augment_empty_reranked_sets_result(self) -> None:
        stage = AugmentStage()
        ctx = PipelineContext(query="q")
        ctx.reranked = []
        await stage.run(ctx)
        # _format_chunks always wraps with block markers; empty hits → empty content
        assert isinstance(ctx.augment_result, str)

    @pytest.mark.asyncio
    async def test_augment_formats_hits_into_block(self) -> None:
        from rag.types import RankedHit

        stage = AugmentStage()
        ctx = PipelineContext(query="q")
        ctx.reranked = [
            RankedHit(chunk_id=1, content="text body", url="http://x.com", title="T")
        ]  # type: ignore[assignment]
        await stage.run(ctx)
        assert "text body" in ctx.augment_result
        assert "http://x.com" in ctx.augment_result


# ---------------------------------------------------------------------------
# RagPipeline.last_timings
# ---------------------------------------------------------------------------


def _make_rag_cfg() -> SimpleNamespace:
    return SimpleNamespace(
        use_mqe=False,
        use_rerank=False,
        use_rrf=True,
        use_search=True,
        use_refiner=False,
        rag_service_url="",
        top_k_search=5,
        top_k_rerank=10,
        rag_top_k=3,
        rag_min_score=0.0,
        max_chunks_per_doc=5,
        semantic_cache_max_size=0,
        semantic_cache_threshold=0.0,
        refiner_max_tokens=512,
        refiner_max_chars_per_chunk=800,
        refiner_timeout=30.0,
    )


class TestRagPipelineLastTimings:
    @pytest.mark.asyncio
    async def test_last_timings_populated_after_run(self) -> None:
        """run() must populate last_timings with one float entry per stage."""
        import httpx
        from rag.pipeline import RagPipeline

        http = MagicMock(spec=httpx.AsyncClient)
        pipeline = RagPipeline(http, _make_rag_cfg())
        mock_db = MagicMock()

        noop = AsyncMock()
        with (
            patch("rag.pipeline.MqeStage") as MockMqe,
            patch("rag.pipeline.SearchStage") as MockSearch,
            patch("rag.pipeline.FusionStage") as MockFusion,
            patch("rag.pipeline.RerankStage") as MockRerank,
            patch("rag.pipeline.AugmentStage") as MockAugment,
        ):
            for M in (MockMqe, MockSearch, MockFusion, MockRerank, MockAugment):
                inst = MagicMock()
                inst.__class__.__name__ = M._mock_name or "Stage"
                inst.run = noop
                M.return_value = inst

            await pipeline.run("test query", mock_db)

        assert len(pipeline.last_timings) == 5
        for elapsed in pipeline.last_timings.values():
            assert isinstance(elapsed, float)
            assert elapsed >= 0.0

    @pytest.mark.asyncio
    async def test_last_timings_reset_on_each_run(self) -> None:
        """last_timings from a previous run must not leak into the next run."""
        import httpx
        from rag.pipeline import RagPipeline

        http = MagicMock(spec=httpx.AsyncClient)
        pipeline = RagPipeline(http, _make_rag_cfg())
        pipeline.last_timings = {"stale_stage": 99.9}
        mock_db = MagicMock()

        noop = AsyncMock()
        with (
            patch("rag.pipeline.MqeStage") as MockMqe,
            patch("rag.pipeline.SearchStage") as MockSearch,
            patch("rag.pipeline.FusionStage") as MockFusion,
            patch("rag.pipeline.RerankStage") as MockRerank,
            patch("rag.pipeline.AugmentStage") as MockAugment,
        ):
            for M in (MockMqe, MockSearch, MockFusion, MockRerank, MockAugment):
                inst = MagicMock()
                inst.run = noop
                M.return_value = inst

            await pipeline.run("second query", mock_db)

        assert "stale_stage" not in pipeline.last_timings


class TestSemanticCacheDimensionGuard:
    """Test SemanticCache dimension validation added in fail-fast refactor."""

    def test_put_sets_dimension_on_first_entry(self) -> None:
        from rag.cache import SemanticCache

        cache = SemanticCache()
        cache.put([1.0, 2.0, 3.0], "", "ctx")
        assert cache._dim == 3

    def test_put_raises_on_dimension_mismatch(self) -> None:
        from rag.cache import SemanticCache

        cache = SemanticCache()
        cache.put([1.0, 2.0, 3.0], "", "ctx")
        with pytest.raises(ValueError, match="dimension mismatch"):
            cache.put([1.0, 2.0], "", "other")

    def test_lookup_raises_on_dimension_mismatch(self) -> None:
        from rag.cache import SemanticCache

        cache = SemanticCache()
        cache.put([1.0, 2.0, 3.0], "", "ctx")
        with pytest.raises(ValueError, match="dimension mismatch"):
            cache.lookup([1.0, 2.0])

    def test_lookup_empty_cache_returns_none(self) -> None:
        from rag.cache import SemanticCache

        cache = SemanticCache()
        assert cache.lookup([1.0, 2.0, 3.0]) is None
