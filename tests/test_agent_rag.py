"""tests/test_agent_rag.py
Unit tests for RagPipeline.augment() — HTTP mode selected_hits storage.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from rag.pipeline import RagPipeline


def _make_cfg(**kwargs: object) -> SimpleNamespace:
    """Build a minimal cfg SimpleNamespace for RagPipeline."""
    defaults = {
        "use_search": True,
        "rag_service_url": "http://127.0.0.1:8010",
        "use_mqe": True,
        "use_rrf": True,
        "use_rerank": True,
        "use_refiner": False,
        "use_semantic_cache": False,
        "top_k_search": 5,
        "top_k_rerank": 10,
        "rag_top_k": 5,
        "rag_min_score": 0.0,
        "max_chunks_per_doc": 2,
        "semantic_cache_max_size": 128,
        "semantic_cache_threshold": 0.92,
        "rrf_k": 60,
        "mqe_n_queries": 3,
        "refiner_max_tokens": 512,
        "refiner_max_chars_per_chunk": 300,
        "refiner_timeout": 30.0,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── HTTP mode: selected_hits storage ─────────────────────────────────────────


class TestAugmentHttpMode:
    @pytest.mark.asyncio
    async def test_stores_selected_hits_in_last_reranked(self) -> None:
        hits = [
            {
                "chunk_id": "c1",
                "score": 9.0,
                "content": "ctx1",
                "title": "T1",
                "url": "U1",
            },
            {
                "chunk_id": "c2",
                "score": 7.5,
                "content": "ctx2",
                "title": "T2",
                "url": "U2",
            },
        ]
        resp_body = {"context": "RAG context", "selected_hits": hits}

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = resp_body

        http = AsyncMock(spec=httpx.AsyncClient)
        http.post = AsyncMock(return_value=mock_resp)

        cfg = _make_cfg()
        pipeline = RagPipeline(http, cfg)

        result = await pipeline.augment("test query")

        assert result == "RAG context"
        assert pipeline.last_reranked == hits

    @pytest.mark.asyncio
    async def test_does_not_overwrite_last_reranked_when_hits_empty(self) -> None:
        resp_body = {"context": "some context", "selected_hits": []}

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = resp_body

        http = AsyncMock(spec=httpx.AsyncClient)
        http.post = AsyncMock(return_value=mock_resp)

        cfg = _make_cfg()
        pipeline = RagPipeline(http, cfg)
        # Pre-populate last_reranked to confirm it is NOT overwritten
        initial_hit = {
            "chunk_id": "prev",
            "score": 5.0,
            "content": "p",
            "title": "T",
            "url": "U",
        }
        pipeline.last_reranked = [initial_hit]  # type: ignore[list-item]

        await pipeline.augment("test query")

        # When selected_hits is empty, last_reranked must remain unchanged
        assert pipeline.last_reranked == [initial_hit]

    @pytest.mark.asyncio
    async def test_returns_context_string(self) -> None:
        resp_body = {"context": "Expected context text", "selected_hits": []}

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = resp_body

        http = AsyncMock(spec=httpx.AsyncClient)
        http.post = AsyncMock(return_value=mock_resp)

        cfg = _make_cfg()
        pipeline = RagPipeline(http, cfg)
        result = await pipeline.augment("q")

        assert result == "Expected context text"

    @pytest.mark.asyncio
    async def test_missing_selected_hits_key_does_not_raise(self) -> None:
        resp_body = {"context": "ctx"}  # selected_hits key absent

        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = resp_body

        http = AsyncMock(spec=httpx.AsyncClient)
        http.post = AsyncMock(return_value=mock_resp)

        cfg = _make_cfg()
        pipeline = RagPipeline(http, cfg)
        result = await pipeline.augment("q")

        assert result == "ctx"
        assert pipeline.last_reranked == []

    @pytest.mark.asyncio
    async def test_fallback_to_inprocess_on_http_error(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.post = AsyncMock(side_effect=httpx.ConnectError("refused"))

        cfg = _make_cfg()
        pipeline = RagPipeline(http, cfg)

        # In-process path tries to open DB; mock SQLiteHelper to return empty result
        with patch("rag.pipeline.SQLiteHelper") as mock_sqlite:
            mock_db = MagicMock()
            mock_db.__enter__ = MagicMock(return_value=mock_db)
            mock_db.__exit__ = MagicMock(return_value=False)
            mock_sqlite.return_value.open.return_value = mock_db
            pipeline.run = AsyncMock(return_value=([], [], [], []))  # type: ignore[method-assign]

            result = await pipeline.augment("q")

        # Falls back gracefully; result should be empty string (no reranked hits)
        assert result == ""
