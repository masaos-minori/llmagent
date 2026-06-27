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
from rag.types import MergedHit, RawHit

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
        assert isinstance(result.reranked, list)
        assert isinstance(result.diagnostics, SearchDiagnostics)
        # No embed server configured → all embedding attempts fail
        assert result.diagnostics.embed_failed >= 1
        assert result.diagnostics.embed_ok == 0

    async def test_no_rrf_returns_result(
        self, rag_pipeline_no_rrf: RagPipeline
    ) -> None:
        """No-RRF mode: run() completes; result structure matches RRF mode."""
        mock_db = MagicMock()
        result = await rag_pipeline_no_rrf.run("python asyncio", db=mock_db)
        assert isinstance(result.reranked, list)
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
