"""tests/rag/test_rag_pipeline_no_cache_freshness.py

Regression tests proving committed document additions, updates, and deletions
are reflected in RagPipeline retrieval results without calling any cache-invalidation
method or restarting the pipeline/service (REQ-007).

Since SemanticCache was removed (procedure documents 01-07), every query must
execute the retrieval pipeline on each call — no stale caching can mask DB changes.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from rag.models_result import SearchDiagnostics
from rag.pipeline import RagPipeline
from shared.types import RawHit

# ── Helpers ──────────────────────────────────────────────────────────────────

_ADDITION_MARKER = "NEWLY_ADDED_DOCUMENT_CONTENT"
_UPDATE_OLD_MARKER = "ORIGINAL_CONTENT_MARKER"
_UPDATE_NEW_MARKER = "UPDATED_CONTENT_MARKER"
_DELETION_MARKER = "EXISTING_DOCUMENT_CONTENT"

ADD_DIAG = SearchDiagnostics(embed_ok=1, embed_failed=0)
DEL_DIAG = SearchDiagnostics(embed_ok=1, embed_failed=0)
UPDATE_DIAG = SearchDiagnostics(embed_ok=1, embed_failed=0)

ADD_HIT = RawHit(chunk_id=999, content=_ADDITION_MARKER, url="http://new/", title="New")
OLD_HIT = RawHit(
    chunk_id=1, content=_UPDATE_OLD_MARKER, url="http://example.com/", title="Example"
)
NEW_HIT = RawHit(
    chunk_id=1, content=_UPDATE_NEW_MARKER, url="http://example.com/", title="Example"
)
DEL_HIT = RawHit(
    chunk_id=1, content=_DELETION_MARKER, url="http://example.com/", title="Example"
)


def _make_no_cache_cfg() -> SimpleNamespace:
    """Build a RagConfig-compatible SimpleNamespace for pipeline construction."""
    return SimpleNamespace(
        use_mqe=False,
        top_k_search=5,
        use_rerank=False,
        rag_top_k=3,
        max_chunks_per_doc=3,
        top_k_rerank=10,
        rag_min_score=0.0,
        use_rrf=True,
        rrf_k=60,
        use_search=True,
        rag_service_url="",
        rag_auth_token="",
        use_refiner=False,
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
        rag_pipeline_service_url=None,
        mqe_prompt_template="Expand query: {query}",
        mqe_n_queries=3,
        rerank_prompt_template="Rerank results for: {query}",
    )


def _make_http() -> MagicMock:
    """Return a mock httpx.AsyncClient."""
    return MagicMock()


# ── Tests ──────────────────────────────────────────────────────────────────


class TestNoCacheFreshness:
    async def test_addition_visible_without_invalidation(self) -> None:
        """Document addition is visible on the next identical query without invalidation."""
        cfg = _make_no_cache_cfg()
        http = _make_http()
        with patch("rag.pipeline._ModuleConfig.get", return_value={}):
            pipeline = RagPipeline(http, cfg)

        assert hasattr(pipeline, "invalidate_cache") is False

        mock_db = MagicMock()
        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(side_effect=[([], DEL_DIAG), ([[ADD_HIT]], ADD_DIAG)]),
        ):
            result_before = await pipeline.run("same-query", db=mock_db)
            result_after = await pipeline.run("same-query", db=mock_db)

        before_contents = [h.content for h in result_before.merged]
        after_contents = [h.content for h in result_after.merged]
        assert _ADDITION_MARKER not in before_contents
        assert _ADDITION_MARKER in after_contents

    async def test_update_visible_without_invalidation(self) -> None:
        """Document update is visible on the next identical query without invalidation."""
        cfg = _make_no_cache_cfg()
        http = _make_http()
        with patch("rag.pipeline._ModuleConfig.get", return_value={}):
            pipeline = RagPipeline(http, cfg)

        assert hasattr(pipeline, "invalidate_cache") is False

        mock_db = MagicMock()
        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(
                side_effect=[([[OLD_HIT]], UPDATE_DIAG), ([[NEW_HIT]], UPDATE_DIAG)]
            ),
        ):
            result_before = await pipeline.run("same-query", db=mock_db)
            result_after = await pipeline.run("same-query", db=mock_db)

        before_contents = [h.content for h in result_before.merged]
        after_contents = [h.content for h in result_after.merged]
        assert _UPDATE_OLD_MARKER in before_contents
        assert _UPDATE_OLD_MARKER not in after_contents
        assert _UPDATE_NEW_MARKER in after_contents

    async def test_deletion_visible_without_invalidation(self) -> None:
        """Document deletion is visible on the next identical query without invalidation."""
        cfg = _make_no_cache_cfg()
        http = _make_http()
        with patch("rag.pipeline._ModuleConfig.get", return_value={}):
            pipeline = RagPipeline(http, cfg)

        assert hasattr(pipeline, "invalidate_cache") is False

        mock_db = MagicMock()
        with patch(
            "rag.stages.search._search_all_queries",
            AsyncMock(side_effect=[([[DEL_HIT]], DEL_DIAG), ([], DEL_DIAG)]),
        ):
            result_before = await pipeline.run("same-query", db=mock_db)
            result_after = await pipeline.run("same-query", db=mock_db)

        before_contents = [h.content for h in result_before.merged]
        after_contents = [h.content for h in result_after.merged]
        assert _DELETION_MARKER in before_contents
        assert len(after_contents) == 0
