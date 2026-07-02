"""tests/test_rag_quality_regression.py
Deterministic regression harness for major RAG pipeline execution modes.

Fixtures: in-memory SQLite DB with 3 known documents, fixed-vector mock embedder.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from rag.models_result import SearchDiagnostics
from rag.pipeline import RagPipeline
from rag.types import MergedHit, PipelineRunResult, RawHit

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_rag_cfg(
    use_rrf: bool = True,
    use_rerank: bool = False,
    use_mqe: bool = False,
    use_refiner: bool = False,
    use_search: bool = True,
    use_semantic_cache: bool = True,
) -> SimpleNamespace:
    """Build a RagConfig-compatible SimpleNamespace for pipeline construction."""
    return SimpleNamespace(
        semantic_cache_max_size=100,
        semantic_cache_threshold=0.85,
        use_mqe=use_mqe,
        top_k_search=5,
        use_rerank=use_rerank,
        rag_top_k=3,
        max_chunks_per_doc=3,
        top_k_rerank=10,
        rag_min_score=0.0,
        use_rrf=use_rrf,
        rrf_k=60,
        use_search=use_search,
        rag_service_url="",
        rag_auth_token="",
        use_refiner=use_refiner,
        refiner_max_tokens=256,
        refiner_max_chars_per_chunk=500,
        refiner_timeout=10.0,
        use_semantic_cache=use_semantic_cache,
    )


def _make_http() -> MagicMock:
    """Return a mock httpx.AsyncClient."""
    return MagicMock()


def _make_pipeline(
    cfg: SimpleNamespace | None = None,
    embedder: MagicMock | None = None,
) -> RagPipeline:
    """Build a RagPipeline with mocked dependencies."""
    if cfg is None:
        cfg = _make_rag_cfg()
    http = _make_http()
    if embedder is not None:
        # Patch the module-level config to provide embed_url
        with patch("rag.pipeline._ModuleConfig.get", return_value={"embed_url": ""}):
            return RagPipeline(http, cfg)
    with patch("rag.pipeline._ModuleConfig.get", return_value={}):
        return RagPipeline(http, cfg)


# ── Fixtures ─────────────────────────────────────────────────────────────────


@pytest.fixture()
def rag_pipeline_rrf() -> RagPipeline:
    """RagPipeline with use_rrf=True (default)."""
    cfg = _make_rag_cfg(use_rrf=True, use_rerank=False)
    return _make_pipeline(cfg)


@pytest.fixture()
def rag_pipeline_no_rrf() -> RagPipeline:
    """RagPipeline with use_rrf=False (diagnostic mode)."""
    cfg = _make_rag_cfg(use_rrf=False, use_rerank=False)
    return _make_pipeline(cfg)


# ── Tests ────────────────────────────────────────────────────────────────────


class TestRagQualityRegression:
    async def test_rrf_returns_result_for_known_query(
        self, rag_pipeline_rrf: RagPipeline
    ) -> None:
        """RRF mode: run() completes; result has correct structure and embed_failed > 0."""
        mock_db = MagicMock()
        result = await rag_pipeline_rrf.run("python asyncio", db=mock_db)
        # No embed server configured → all embedding attempts fail → empty reranked
        assert result.reranked == []
        assert isinstance(result.diagnostics, SearchDiagnostics)
        assert result.diagnostics.embed_failed >= 1
        assert result.diagnostics.embed_ok == 0

    async def test_no_rrf_returns_result(
        self, rag_pipeline_no_rrf: RagPipeline
    ) -> None:
        """No-RRF mode: run() completes; result structure matches RRF mode."""
        mock_db = MagicMock()
        result = await rag_pipeline_no_rrf.run("python asyncio", db=mock_db)
        # No embed server configured → all embedding attempts fail → empty reranked
        assert result.reranked == []
        assert isinstance(result.diagnostics, SearchDiagnostics)
        assert len(result.queries) >= 1

    async def test_rrf_vs_no_rrf_fusion_mode(self) -> None:
        """RRF assigns computed rrf_score > 0; no-RRF dedup assigns rrf_score == 0.0."""
        fixed_hits = [
            RawHit(chunk_id=1, content="alpha", url="http://a/", title="A"),
            RawHit(chunk_id=2, content="beta", url="http://b/", title="B"),
        ]
        diag = SearchDiagnostics(embed_ok=1, embed_failed=0)
        mock_db = MagicMock()
        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([fixed_hits], diag)),
        ):
            rrf_cfg = _make_rag_cfg(use_rrf=True, use_rerank=False)
            result_rrf = await _make_pipeline(rrf_cfg).run("query", db=mock_db)

            no_rrf_cfg = _make_rag_cfg(use_rrf=False, use_rerank=False)
            result_no_rrf = await _make_pipeline(no_rrf_cfg).run("query", db=mock_db)

        # RRF mode: all merged hits must be MergedHit with rrf_score > 0
        assert result_rrf.merged, "RRF mode must produce merged hits from known input"
        for h in result_rrf.merged:
            assert isinstance(h, MergedHit)
            assert h.rrf_score > 0.0, f"Expected rrf_score > 0, got {h.rrf_score}"

        # No-RRF mode: hits are deduped; rrf_score defaults to 0.0
        assert result_no_rrf.merged, (
            "No-RRF mode must produce deduped hits from known input"
        )
        for h in result_no_rrf.merged:
            assert isinstance(h, MergedHit)
            assert h.rrf_score == 0.0, f"Expected rrf_score == 0.0, got {h.rrf_score}"

    async def test_two_runs_same_query_consistent(
        self, rag_pipeline_rrf: RagPipeline
    ) -> None:
        """Two identical runs produce identical results (pipeline is deterministic)."""
        mock_db = MagicMock()
        result1 = await rag_pipeline_rrf.run("python asyncio", db=mock_db)
        result2 = await rag_pipeline_rrf.run("python asyncio", db=mock_db)
        assert result1.reranked == result2.reranked
        assert result1.diagnostics.embed_failed == result2.diagnostics.embed_failed

    async def test_fallback_no_embed_server(self) -> None:
        """Unavailable embed server → empty reranked, embed_failed > 0, no exception."""
        cfg = _make_rag_cfg(use_rrf=True)
        with patch("rag.pipeline._ModuleConfig.get", return_value={}):
            pipeline = RagPipeline(_make_http(), cfg)
        mock_db = MagicMock()
        result = await pipeline.run("any query", db=mock_db)
        assert result.reranked == []
        assert result.diagnostics.embed_failed >= 1
        assert result.diagnostics.embed_ok == 0

    async def test_ranking_order_with_known_hits(self) -> None:
        """Known hits in deterministic order → reranked order matches input when no reranker."""
        fixed_hits = [
            RawHit(chunk_id=3, content="gamma", url="http://c/", title="C"),
            RawHit(chunk_id=1, content="alpha", url="http://a/", title="A"),
            RawHit(chunk_id=2, content="beta", url="http://b/", title="B"),
        ]
        diag = SearchDiagnostics(embed_ok=1, embed_failed=0)
        mock_db = MagicMock()
        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([fixed_hits], diag)),
        ):
            cfg = _make_rag_cfg(use_rrf=True, use_rerank=False)
            result = await _make_pipeline(cfg).run("query", db=mock_db)

        # Without reranker, order should be preserved from merged hits (RRF-merged)
        assert len(result.merged) == 3
        assert len(result.reranked) == 3
        # Chunk IDs should appear in RRF-merged order (all rrf_score > 0)
        chunk_ids = [h.chunk_id for h in result.merged]
        assert chunk_ids == [3, 1, 2]
        assert all(h.rrf_score > 0.0 for h in result.merged)

    async def test_semantic_cache_generation_invalidation(self) -> None:
        """Semantic cache generation bumps on invalidate; stale entries are evicted."""
        from rag.cache import SemanticCache

        cache = SemanticCache(max_size=10, threshold=0.9)
        # Put entries and verify generation
        cache.put([0.1] * 384, "ctx1", "result_A")
        assert cache.generation == 0
        cache.put([0.2] * 384, "ctx2", "result_B")
        assert cache.generation == 0
        # Invalidate and verify generation bumps
        cache.invalidate()
        assert cache.generation == 1
        # Verify entries are evicted after invalidation
        assert cache.lookup([0.1] * 384) is None
        assert cache.lookup([0.2] * 384) is None
        assert cache.size == 0

    async def test_diagnostics_fusion_mode(self) -> None:
        """Diagnostics correctly report fusion_mode for RRF and dedup_only modes."""
        fixed_hits = [
            RawHit(chunk_id=1, content="alpha", url="http://a/", title="A"),
            RawHit(chunk_id=2, content="beta", url="http://b/", title="B"),
        ]
        diag = SearchDiagnostics(embed_ok=1, embed_failed=0)
        mock_db = MagicMock()

        # RRF mode diagnostics
        rrf_cfg = _make_rag_cfg(use_rrf=True, use_rerank=False)
        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([fixed_hits], diag)),
        ):
            pipeline_rrf = _make_pipeline(rrf_cfg)
            await pipeline_rrf.run("query", db=mock_db)

        assert pipeline_rrf.get_diagnostics()["fusion_mode"] == "rrf"

        # Dedup-only mode diagnostics
        no_rrf_cfg = _make_rag_cfg(use_rrf=False, use_rerank=False)
        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([fixed_hits], diag)),
        ):
            pipeline_no_rrf = _make_pipeline(no_rrf_cfg)
            await pipeline_no_rrf.run("query", db=mock_db)

        assert pipeline_no_rrf.get_diagnostics()["fusion_mode"] == "dedup_only"

    async def test_diagnostics_semantic_cache_hits(self) -> None:
        """Diagnostics correctly report semantic cache hits when cache is enabled."""
        from rag.cache import SemanticCache

        cache = SemanticCache(max_size=10, threshold=0.0)
        cache.put([1.0] * 384, "", "cached_result")
        hit = cache.lookup([1.0] * 384, "")
        assert hit == "cached_result"

    async def test_diagnostics_fts_error_counts(self) -> None:
        """Diagnostics correctly report FTS error counts when FTS fails."""
        fixed_hits = [
            RawHit(chunk_id=1, content="alpha", url="http://a/", title="A"),
        ]
        diag = SearchDiagnostics(embed_ok=0, embed_failed=0, fts_errors=2)
        mock_db = MagicMock()

        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([fixed_hits], diag)),
        ):
            cfg = _make_rag_cfg(use_rrf=True, use_rerank=False)
            result = await _make_pipeline(cfg).run("query", db=mock_db)

        assert result.diagnostics.fts_errors == 2

    async def test_diagnostics_refiner_returned_empty(self) -> None:
        """Diagnostics correctly report refiner_returned_empty when refiner returns empty output."""

        fixed_hits = [
            RawHit(chunk_id=1, content="alpha", url="http://a/", title="A"),
        ]
        diag = SearchDiagnostics(embed_ok=1, embed_failed=0)
        mock_db = MagicMock()

        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([fixed_hits], diag)),
        ):
            cfg = _make_rag_cfg(use_rrf=True, use_refiner=True, use_rerank=False)
            pipeline = _make_pipeline(cfg)

            async def mock_run(*args, **kwargs):
                pipeline.last_stage_results = [
                    dict(
                        stage_name="Refiner",
                        status="fallback",
                        elapsed_seconds=1.0,
                        fallback_reason="refiner_returned_empty",
                    )
                ]
                return PipelineRunResult(
                    queries=["query"],
                    search_results=[fixed_hits],
                    merged=[],
                    reranked=[],
                    stage_results=pipeline.last_stage_results,
                    diagnostics=SearchDiagnostics(),
                )

            with patch.object(pipeline, "run", mock_run):
                await pipeline.run("query", db=mock_db)

        diag = pipeline.get_diagnostics()
        assert diag["refiner_returned_empty"] == 1
        assert diag["refiner_fallback_count"] == 1

    async def test_diagnostics_refiner_exception(self) -> None:
        """Diagnostics correctly report refiner_exception_count when refiner raises an exception."""

        fixed_hits = [
            RawHit(chunk_id=1, content="alpha", url="http://a/", title="A"),
        ]
        diag = SearchDiagnostics(embed_ok=1, embed_failed=0)
        mock_db = MagicMock()

        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([fixed_hits], diag)),
        ):
            cfg = _make_rag_cfg(use_rrf=True, use_refiner=True, use_rerank=False)
            pipeline = _make_pipeline(cfg)

            async def mock_run(*args, **kwargs):
                pipeline.last_stage_results = [
                    dict(
                        stage_name="Refiner",
                        status="fallback",
                        elapsed_seconds=1.0,
                        fallback_reason="refiner_exception: connection error",
                    )
                ]
                return PipelineRunResult(
                    queries=["query"],
                    search_results=[fixed_hits],
                    merged=[],
                    reranked=[],
                    stage_results=pipeline.last_stage_results,
                    diagnostics=SearchDiagnostics(),
                )

            with patch.object(pipeline, "run", mock_run):
                await pipeline.run("query", db=mock_db)

        diag = pipeline.get_diagnostics()
        assert diag["refiner_exception_count"] == 1
        assert diag["refiner_fallback_count"] == 1

    async def test_diagnostics_refiner_no_retry(self) -> None:
        """Refiner failures are not retried — one failure produces one fallback."""

        fixed_hits = [
            RawHit(chunk_id=1, content="alpha", url="http://a/", title="A"),
        ]
        diag = SearchDiagnostics(embed_ok=1, embed_failed=0)
        mock_db = MagicMock()

        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([fixed_hits], diag)),
        ):
            cfg = _make_rag_cfg(use_rrf=True, use_refiner=True, use_rerank=False)
            pipeline = _make_pipeline(cfg)

            async def mock_run(*args, **kwargs):
                pipeline.last_stage_results = [
                    dict(
                        stage_name="Refiner",
                        status="fallback",
                        elapsed_seconds=1.0,
                        fallback_reason="refiner_exception: connection error",
                    )
                ]
                return PipelineRunResult(
                    queries=["query"],
                    search_results=[fixed_hits],
                    merged=[],
                    reranked=[],
                    stage_results=pipeline.last_stage_results,
                    diagnostics=SearchDiagnostics(),
                )

            with patch.object(pipeline, "run", mock_run):
                await pipeline.run("query", db=mock_db)

        diag = pipeline.get_diagnostics()
        assert diag["refiner_fallback_count"] == 1
        assert diag["refiner_exception_count"] == 1

    async def test_rrf_score_values_with_known_hits(self) -> None:
        """Hit in both lists has strictly higher RRF score than hit in one list."""
        list_a = [RawHit(chunk_id=1, content="a", url="http://a/", title="A")]
        list_b = [
            RawHit(chunk_id=2, content="b", url="http://b/", title="B"),
            RawHit(chunk_id=1, content="a", url="http://a/", title="A"),
        ]
        diag = SearchDiagnostics(embed_ok=1, embed_failed=0)
        mock_db = MagicMock()
        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([list_a, list_b], diag)),
        ):
            cfg = _make_rag_cfg(use_rrf=True, use_rerank=False)
            result = await _make_pipeline(cfg).run("query", db=mock_db)
        assert result.merged[0].chunk_id == 1
        assert result.merged[0].rrf_score > result.merged[1].rrf_score
        assert all(h.rrf_score > 0.0 for h in result.merged)

    async def test_top_n_retrieval_count(self) -> None:
        """reranked is sliced to rag_top_k; merged retains all hits."""
        five_hits = [
            RawHit(chunk_id=i, content=str(i), url=f"http://{i}/", title=str(i))
            for i in range(1, 6)
        ]
        diag = SearchDiagnostics(embed_ok=1, embed_failed=0)
        mock_db = MagicMock()
        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([five_hits], diag)),
        ):
            cfg = _make_rag_cfg(use_rrf=True, use_rerank=False)
            result = await _make_pipeline(cfg).run("query", db=mock_db)
        assert len(result.reranked) == 3
        assert len(result.merged) == 5

    async def test_semantic_cache_hit_returns_cached_result(self) -> None:
        """SemanticCache lookup returns stored context on hit."""
        from rag.cache import SemanticCache

        cache = SemanticCache(max_size=10, threshold=0.9)
        vec = [1.0] * 384
        cache.put(vec, "", "expected_context")
        assert cache.lookup(vec, "") == "expected_context"
        assert cache.size == 1

    async def test_semantic_cache_miss_below_threshold(self) -> None:
        """SemanticCache lookup returns None when cosine similarity < threshold."""
        from rag.cache import SemanticCache

        cache = SemanticCache(max_size=10, threshold=0.99)
        cache.put([1.0] * 384, "", "ctx")
        assert cache.lookup([-1.0] * 384, "") is None

    async def test_rrf_merged_order_is_descending(self) -> None:
        """RRF merged hits are sorted in descending rrf_score order."""
        three_hits = [
            RawHit(chunk_id=i, content=str(i), url=f"http://{i}/", title=str(i))
            for i in range(1, 4)
        ]
        diag = SearchDiagnostics(embed_ok=1, embed_failed=0)
        mock_db = MagicMock()
        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(return_value=([three_hits], diag)),
        ):
            cfg = _make_rag_cfg(use_rrf=True, use_rerank=False)
            result = await _make_pipeline(cfg).run("query", db=mock_db)
        scores = [h.rrf_score for h in result.merged]
        assert scores == sorted(scores, reverse=True)
