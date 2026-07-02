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
    build_rag_cfg_adapter,
)
from mcp.rag_pipeline.service import RagPipelineMCPService, _hit_to_dict
from rag.models_data import TwoStageFetchResult
from rag.types import MergedHit, RankedHit, RawHit

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

    def test_adapter_satisfies_rag_config_protocol(self) -> None:
        """build_rag_cfg_adapter output must satisfy every field in RagConfig Protocol."""
        from shared.types import RagConfig

        cfg = RagPipelineConfig(
            use_mqe=False,
            use_rrf=False,
            rrf_k=30,
            use_rerank=False,
            use_refiner=True,
            top_k_search=10,
            top_k_rerank=20,
            rag_top_k=5,
            rag_min_score=1.5,
            max_chunks_per_doc=2,
            semantic_cache_max_size=64,
            semantic_cache_threshold=0.85,
            use_semantic_cache=True,
            refiner_max_tokens=256,
            refiner_max_chars_per_chunk=400,
            refiner_timeout=15.0,
            rag_auth_token="test-token",
        )
        adapter = build_rag_cfg_adapter(cfg)

        required_fields: list[str] = [
            "semantic_cache_max_size",
            "semantic_cache_threshold",
            "use_mqe",
            "top_k_search",
            "use_rerank",
            "rag_top_k",
            "max_chunks_per_doc",
            "top_k_rerank",
            "rag_min_score",
            "use_rrf",
            "rrf_k",
            "use_search",
            "rag_service_url",
            "rag_auth_token",
            "use_refiner",
            "refiner_max_tokens",
            "refiner_max_chars_per_chunk",
            "refiner_timeout",
            "use_semantic_cache",
        ]

        for field in required_fields:
            assert hasattr(adapter, field), f"Missing RagConfig field: {field}"

        # Verify the adapter structurally satisfies the Protocol at runtime
        assert isinstance(adapter, RagConfig)

        # Verify specific values from the config above
        assert adapter.use_mqe is False
        assert adapter.use_rrf is False
        assert adapter.rrf_k == 30
        assert adapter.use_rerank is False
        assert adapter.use_refiner is True
        assert adapter.top_k_search == 10
        assert adapter.top_k_rerank == 20
        assert adapter.rag_top_k == 5
        assert adapter.rag_min_score == 1.5
        assert adapter.max_chunks_per_doc == 2
        assert adapter.semantic_cache_max_size == 64
        assert adapter.semantic_cache_threshold == 0.85
        assert adapter.use_semantic_cache is True
        assert adapter.refiner_max_tokens == 256
        assert adapter.refiner_max_chars_per_chunk == 400
        assert adapter.refiner_timeout == 15.0
        assert adapter.rag_auth_token == "test-token"

        # MCP mode invariants
        assert adapter.use_search is True
        assert adapter.rag_service_url == ""


# ── _hit_to_dict helper ───────────────────────────────────────────────────────


class TestHitToDict:
    def test_dataclass_raw_hit(self) -> None:
        hit = RawHit(chunk_id=1, content="text", url="http://u", title="T")
        result = _hit_to_dict(hit)
        assert isinstance(result, dict)
        assert result["chunk_id"] == 1
        assert result["content"] == "text"
        assert result["url"] == "http://u"

    def test_dataclass_merged_hit(self) -> None:
        hit = MergedHit(chunk_id=2, content="m", rrf_score=5.0)
        result = _hit_to_dict(hit)
        assert result["chunk_id"] == 2
        assert result["rrf_score"] == 5.0

    def test_dataclass_ranked_hit(self) -> None:
        hit = RankedHit(chunk_id=3, content="r", rerank_score=9.0)
        result = _hit_to_dict(hit)
        assert result["chunk_id"] == 3
        assert result["rerank_score"] == 9.0

    def test_dict_hit_returns_same_dict(self) -> None:
        hit = {"chunk_id": 4, "content": "d"}
        result = _hit_to_dict(hit)
        assert result is hit

    def test_unsupported_type_raises(self) -> None:
        class NotADataclass:
            pass

        with pytest.raises(TypeError, match="Unsupported hit type"):
            _hit_to_dict(NotADataclass())


# ── RagPipelineMCPService helpers ────────────────────────────────────────────


def _make_service_with_pipeline(pipeline_mock: Any) -> RagPipelineMCPService:
    svc = RagPipelineMCPService.__new__(RagPipelineMCPService)
    svc._http = MagicMock()
    svc._pipeline = pipeline_mock
    return svc


# ── run_pipeline ──────────────────────────────────────────────────────────────


class TestRunPipeline:
    @pytest.mark.asyncio
    async def test_query_with_hits_returns_augmented_response(self) -> None:
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

    @pytest.mark.asyncio
    async def test_dataclass_hits_serialized_correctly(self) -> None:
        """run_pipeline must serialize dataclass hits without TypeError."""
        hit_raw = RawHit(chunk_id=1, content="raw", url="http://r", title="R")
        pipeline = MagicMock()
        pipeline.augment = AsyncMock(return_value="augmented")
        pipeline.last_fetch_result = TwoStageFetchResult(
            hits=[hit_raw], min_score_applied=0.0, max_chunks_per_doc=0
        )

        svc = _make_service_with_pipeline(pipeline)
        req = RagRunRequest(query="q")
        result = await svc.run_pipeline(req)

        assert isinstance(result.selected_hits[0], dict)
        assert result.selected_hits[0]["chunk_id"] == 1
        assert result.selected_hits[0]["content"] == "raw"


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

    @pytest.mark.asyncio
    async def test_dataclass_hits_serialized_in_debug_response(self) -> None:
        """run_debug_pipeline must serialize dataclass hits without TypeError."""
        hit_merged = MergedHit(chunk_id=10, content="merged", rrf_score=5.5)
        hit_reranked = RankedHit(chunk_id=11, content="reranked", rerank_score=9.2)

        async def fake_augment(
            query: str,
            *,
            debug_fn: Any = None,
            history_context: str = "",
        ) -> str:
            if debug_fn is not None:
                debug_fn(["q"], [], [hit_merged], [hit_reranked])
            return "result"

        pipeline = MagicMock()
        pipeline.augment = fake_augment
        pipeline.last_fetch_result = TwoStageFetchResult(
            hits=[hit_reranked], min_score_applied=0.0, max_chunks_per_doc=0
        )
        pipeline.last_timings = {"mqe": 0.1}

        svc = _make_service_with_pipeline(pipeline)
        req = RagRunRequest(query="debug query")
        result = await svc.run_debug_pipeline(req)

        assert isinstance(result.merged_hits[0], dict)
        assert result.merged_hits[0]["chunk_id"] == 10
        assert result.merged_hits[0]["rrf_score"] == 5.5
        assert isinstance(result.reranked_hits[0], dict)
        assert result.reranked_hits[0]["chunk_id"] == 11
        assert result.reranked_hits[0]["rerank_score"] == 9.2


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
    async def test_no_module_level_cfg_override(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """start() must not write to rag.pipeline._cfg."""

        import mcp.rag_pipeline.models as models_module
        import rag.pipeline as agent_rag

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
        assert not hasattr(agent_rag, "_cfg"), (
            "rag.pipeline._cfg must not be set by RagPipelineMCPService.start()"
        )

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
