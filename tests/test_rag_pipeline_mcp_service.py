"""tests/test_rag_pipeline_mcp_service.py
Unit tests for RagPipelineMCPService and build_rag_cfg_adapter.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from mcp.rag_pipeline.models import (
    RagDebugResponse,
    RagPipelineConfig,
    RagRunRequest,
    RagRunResponse,
    RagSearchRequest,
    RagSearchResponse,
    build_rag_cfg_adapter,
)
from mcp.rag_pipeline.service import RagPipelineMCPService
from rag.models import TwoStageFetchResult

# ── build_rag_cfg_adapter ─────────────────────────────────────────────────────


class TestBuildRagCfgAdapter:
    def test_defaults_when_cfg_empty(self) -> None:
        cfg = RagPipelineConfig()
        ns = build_rag_cfg_adapter(cfg)
        assert ns.use_mqe is True
        assert ns.use_rrf is True
        assert ns.use_rerank is True
        assert ns.use_refiner is False
        assert ns.use_search is True
        assert ns.rag_service_url == ""
        assert ns.top_k_search == 5
        assert ns.top_k_rerank == 10
        assert ns.rag_top_k == 5
        assert ns.rag_min_score == 0.0
        assert ns.max_chunks_per_doc == 3
        assert ns.semantic_cache_max_size == 128
        assert ns.semantic_cache_threshold == 0.92
        assert ns.refiner_max_tokens == 512
        assert ns.refiner_max_chars_per_chunk == 800
        assert ns.refiner_timeout == 30.0

    def test_overrides_from_cfg(self) -> None:
        cfg = RagPipelineConfig(
            use_mqe=False,
            use_rrf=False,
            use_rerank=False,
            use_refiner=True,
            top_k_search=10,
            top_k_rerank=20,
            rag_top_k=3,
            rag_min_score=5.0,
            max_chunks_per_doc=1,
            semantic_cache_max_size=64,
            semantic_cache_threshold=0.85,
            refiner_max_tokens=256,
            refiner_max_chars_per_chunk=400,
            refiner_timeout=15.0,
        )
        ns = build_rag_cfg_adapter(cfg)
        assert ns.use_mqe is False
        assert ns.use_rrf is False
        assert ns.use_rerank is False
        assert ns.use_refiner is True
        assert ns.top_k_search == 10
        assert ns.top_k_rerank == 20
        assert ns.rag_top_k == 3
        assert ns.rag_min_score == 5.0
        assert ns.max_chunks_per_doc == 1
        assert ns.semantic_cache_max_size == 64
        assert ns.semantic_cache_threshold == 0.85
        assert ns.refiner_max_tokens == 256
        assert ns.refiner_max_chars_per_chunk == 400
        assert ns.refiner_timeout == 15.0

    def test_rag_service_url_always_empty(self) -> None:
        # rag_service_url must always be "" to prevent HTTP loop in MCP process
        cfg = RagPipelineConfig()
        ns = build_rag_cfg_adapter(cfg)
        assert ns.rag_service_url == ""

    def test_use_search_always_true(self) -> None:
        cfg = RagPipelineConfig()
        ns = build_rag_cfg_adapter(cfg)
        assert ns.use_search is True


# ── RagPipelineMCPService helpers ────────────────────────────────────────────


def _make_service_with_pipeline(pipeline_mock: Any) -> RagPipelineMCPService:
    svc = RagPipelineMCPService.__new__(RagPipelineMCPService)
    svc._http = MagicMock()
    svc._pipeline = pipeline_mock
    return svc


# ── run_pipeline ──────────────────────────────────────────────────────────────


class TestRunPipeline:
    @pytest.mark.asyncio
    async def test_normal_with_hits(self) -> None:
        hit = {
            "chunk_id": "c1",
            "score": 8.0,
            "content": "hello",
            "title": "T",
            "url": "U",
        }
        pipeline = MagicMock()
        pipeline.augment = AsyncMock(return_value="[Source: T | U]\nhello")
        pipeline.last_fetch_result = TwoStageFetchResult(
            hits=[hit], min_score_applied=0.0, max_chunks_per_doc=0
        )

        svc = _make_service_with_pipeline(pipeline)
        req = RagRunRequest(query="test query")
        result = await svc.run_pipeline(req)

        assert isinstance(result, RagRunResponse)
        assert result.query == "test query"
        assert result.augmented_text == "[Source: T | U]\nhello"
        assert result.selected_hits == [dict(hit)]
        pipeline.augment.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_empty_augmented_text(self) -> None:
        pipeline = MagicMock()
        pipeline.augment = AsyncMock(return_value="")
        pipeline.last_fetch_result = None

        svc = _make_service_with_pipeline(pipeline)
        req = RagRunRequest(query="nothing matches")
        result = await svc.run_pipeline(req)

        assert result.augmented_text == ""
        assert result.selected_hits == []

    @pytest.mark.asyncio
    async def test_history_context_joined(self) -> None:
        pipeline = MagicMock()
        pipeline.augment = AsyncMock(return_value="ctx")
        pipeline.last_fetch_result = None

        svc = _make_service_with_pipeline(pipeline)
        req = RagRunRequest(query="q", history_context=["utt1", "utt2"])
        await svc.run_pipeline(req)

        _call_kwargs = pipeline.augment.call_args.kwargs
        assert _call_kwargs["history_context"] == "utt1\nutt2"

    @pytest.mark.asyncio
    async def test_debug_fn_passed_when_debug_true(self) -> None:
        pipeline = MagicMock()
        pipeline.augment = AsyncMock(return_value="ctx")
        pipeline.last_fetch_result = None

        svc = _make_service_with_pipeline(pipeline)
        req = RagRunRequest(query="q", debug=True)
        await svc.run_pipeline(req)

        _call_kwargs = pipeline.augment.call_args.kwargs
        assert _call_kwargs.get("debug_fn") is not None

    @pytest.mark.asyncio
    async def test_debug_fn_invoked_when_debug_true(self) -> None:
        """debug_fn closure body executes when augment calls it."""

        async def fake_augment_calls_debug(
            query: str, *, debug_fn: Any = None, history_context: str = ""
        ) -> str:
            if debug_fn:
                debug_fn(["q1"], [], [{"chunk_id": 1}], [{"chunk_id": 2}])
            return "txt"

        pipeline = MagicMock()
        pipeline.augment = fake_augment_calls_debug
        pipeline.last_fetch_result = TwoStageFetchResult(
            hits=[{"chunk_id": 2}], min_score_applied=0.0, max_chunks_per_doc=0
        )

        svc = _make_service_with_pipeline(pipeline)
        req = RagRunRequest(query="q", debug=True)
        result = await svc.run_pipeline(req)
        assert result.augmented_text == "txt"

    @pytest.mark.asyncio
    async def test_debug_fn_none_when_debug_false(self) -> None:
        pipeline = MagicMock()
        pipeline.augment = AsyncMock(return_value="ctx")
        pipeline.last_fetch_result = None

        svc = _make_service_with_pipeline(pipeline)
        req = RagRunRequest(query="q", debug=False)
        await svc.run_pipeline(req)

        _call_kwargs = pipeline.augment.call_args.kwargs
        assert _call_kwargs.get("debug_fn") is None


# ── run_debug_pipeline ────────────────────────────────────────────────────────


class TestRunDebugPipeline:
    @pytest.mark.asyncio
    async def test_captures_intermediate_results(self) -> None:
        hit_merged = {
            "chunk_id": "m1",
            "score": 5.0,
            "content": "m",
            "title": "T",
            "url": "U",
        }
        hit_reranked = {
            "chunk_id": "r1",
            "score": 9.0,
            "content": "r",
            "title": "T",
            "url": "U",
        }

        async def fake_augment(
            query: str,
            *,
            debug_fn: Any = None,
            history_context: str = "",
        ) -> str:
            if debug_fn is not None:
                debug_fn(["q1", "q2"], [], [hit_merged], [hit_reranked])
            return "result"

        pipeline = MagicMock()
        pipeline.augment = fake_augment
        pipeline.last_fetch_result = TwoStageFetchResult(
            hits=[hit_reranked], min_score_applied=0.0, max_chunks_per_doc=0
        )
        pipeline.last_timings = {"mqe": 0.1, "search": 0.2}

        svc = _make_service_with_pipeline(pipeline)
        req = RagRunRequest(query="debug query")
        result = await svc.run_debug_pipeline(req)

        assert isinstance(result, RagDebugResponse)
        assert result.queries == ["q1", "q2"]
        assert result.merged_hits == [dict(hit_merged)]
        assert result.reranked_hits == [dict(hit_reranked)]
        assert result.elapsed == {"mqe": 0.1, "search": 0.2}
        assert result.augmented_text == "result"


# ── run_search ────────────────────────────────────────────────────────────────


class TestRunSearch:
    @pytest.mark.asyncio
    async def test_returns_context_and_hits(self) -> None:
        hit = {
            "chunk_id": "c1",
            "score": 7.0,
            "content": "txt",
            "title": "T",
            "url": "U",
        }
        pipeline = MagicMock()
        pipeline.augment = AsyncMock(return_value="ctx_text")
        pipeline.last_fetch_result = TwoStageFetchResult(
            hits=[hit], min_score_applied=0.0, max_chunks_per_doc=0
        )

        svc = _make_service_with_pipeline(pipeline)
        req = RagSearchRequest(query="q", history_context="prev utt")
        result = await svc.run_search(req)

        assert isinstance(result, RagSearchResponse)
        assert result.context == "ctx_text"
        assert result.selected_hits == [dict(hit)]

    @pytest.mark.asyncio
    async def test_empty_history_context(self) -> None:
        pipeline = MagicMock()
        pipeline.augment = AsyncMock(return_value="")
        pipeline.last_fetch_result = None

        svc = _make_service_with_pipeline(pipeline)
        req = RagSearchRequest(query="q", history_context="")
        result = await svc.run_search(req)

        assert result.context == ""


# ── pipeline_or_raise ─────────────────────────────────────────────────────────


class TestPipelineOrRaise:
    @pytest.mark.asyncio
    async def test_raises_when_not_started(self) -> None:
        svc = RagPipelineMCPService()
        req = RagRunRequest(query="q")
        with pytest.raises(RuntimeError, match="not started"):
            await svc.run_pipeline(req)


# ── MCP tool formatters ───────────────────────────────────────────────────────


class TestFmtRunPipeline:
    @pytest.mark.asyncio
    async def test_returns_augmented_text(self) -> None:
        pipeline = MagicMock()
        pipeline.augment = AsyncMock(return_value="RAG context block")
        pipeline.last_fetch_result = TwoStageFetchResult(
            hits=[{"chunk_id": "c1"}], min_score_applied=0.0, max_chunks_per_doc=0
        )

        svc = _make_service_with_pipeline(pipeline)
        result = await svc.fmt_run_pipeline({"query": "q"})
        assert result == "RAG context block"

    @pytest.mark.asyncio
    async def test_returns_fallback_when_empty(self) -> None:
        pipeline = MagicMock()
        pipeline.augment = AsyncMock(return_value="")
        pipeline.last_fetch_result = None

        svc = _make_service_with_pipeline(pipeline)
        result = await svc.fmt_run_pipeline({"query": "q"})
        assert "No relevant documents" in result


class TestFmtDebugPipeline:
    @pytest.mark.asyncio
    async def test_returns_json_summary(self) -> None:
        async def fake_augment(
            query: str, *, debug_fn: Any = None, history_context: str = ""
        ) -> str:
            if debug_fn:
                debug_fn(["q1"], [], [], [])
            return "augmented"

        pipeline = MagicMock()
        pipeline.augment = fake_augment
        pipeline.last_fetch_result = None
        pipeline.last_timings = {}

        svc = _make_service_with_pipeline(pipeline)
        result = await svc.fmt_debug_pipeline({"query": "q"})

        import orjson

        parsed = orjson.loads(result)
        assert parsed["query"] == "q"
        assert "queries" in parsed
        assert "elapsed" in parsed
        assert "augmented_text" in parsed


# ── start() lifecycle ─────────────────────────────────────────────────────────


class TestServiceStart:
    @pytest.mark.asyncio
    async def test_start_creates_pipeline_and_http_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """start() builds httpx.AsyncClient and RagPipeline from config."""

        import mcp.rag_pipeline.models as models_module

        fake_cfg = models_module.RagPipelineConfig(
            use_mqe=True,
            use_rrf=True,
            use_rerank=True,
            top_k_search=5,
            top_k_rerank=10,
        )
        monkeypatch.setattr(models_module.RagPipelineConfig, "load", lambda: fake_cfg)

        svc = RagPipelineMCPService()
        await svc.start()
        assert svc._pipeline is not None
        assert svc._http is not None
        await svc.stop()

    @pytest.mark.asyncio
    async def test_stop_closes_http_client(self) -> None:
        """stop() closes the http client when it was set."""
        svc = RagPipelineMCPService.__new__(RagPipelineMCPService)
        mock_http = AsyncMock()
        svc._http = mock_http
        svc._pipeline = None
        await svc.stop()
        mock_http.aclose.assert_awaited_once()


# ── Document management ───────────────────────────────────────────────────────


class TestFmtListDocuments:
    async def test_returns_rows(self, monkeypatch: Any) -> None:
        service = RagPipelineMCPService()
        monkeypatch.setattr(
            service,
            "list_documents",
            lambda lang=None, limit=20: [
                {"url": "file:///a.md", "lang": "en", "chunk_count": 3}
            ],
        )
        result = await service.fmt_list_documents({"limit": 5})
        assert "file:///a.md" in result
        assert "3 chunks" in result

    async def test_returns_no_documents_when_empty(self, monkeypatch: Any) -> None:
        service = RagPipelineMCPService()
        monkeypatch.setattr(service, "list_documents", lambda lang=None, limit=20: [])
        result = await service.fmt_list_documents({})
        assert "No documents" in result

    async def test_passes_lang_filter(self, monkeypatch: Any) -> None:
        called_with: dict[str, Any] = {}

        def _list(lang: str | None = None, limit: int = 20) -> list[dict]:
            called_with["lang"] = lang
            called_with["limit"] = limit
            return []

        service = RagPipelineMCPService()
        monkeypatch.setattr(service, "list_documents", _list)
        await service.fmt_list_documents({"lang": "ja", "limit": 10})
        assert called_with["lang"] == "ja"
        assert called_with["limit"] == 10


class TestFmtDeleteDocument:
    async def test_found_returns_deleted(self, monkeypatch: Any) -> None:
        service = RagPipelineMCPService()
        monkeypatch.setattr(service, "delete_document", lambda url: True)
        result = await service.fmt_delete_document({"url": "file:///a.md"})
        assert "Deleted" in result

    async def test_not_found_returns_not_found(self, monkeypatch: Any) -> None:
        service = RagPipelineMCPService()
        monkeypatch.setattr(service, "delete_document", lambda url: False)
        result = await service.fmt_delete_document({"url": "file:///a.md"})
        assert "Not found" in result

    async def test_missing_url_returns_error(self) -> None:
        service = RagPipelineMCPService()
        result = await service.fmt_delete_document({})
        assert "Error" in result or "required" in result.lower()
