"""tests/test_rag_get_cfg.py
Coverage for config loading and LLM error paths in rag.pipeline and rag.llm.
"""

from __future__ import annotations

from dataclasses import replace as dc_replace
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from rag.models_config import RagConfigImpl
from shared.config_loader import ConfigLoader

_RAG_CFG_BASE = RagConfigImpl(
    semantic_cache_max_size=0,
    semantic_cache_threshold=0.0,
    use_semantic_cache=False,
    use_mqe=False,
    top_k_search=5,
    use_rerank=False,
    rag_top_k=3,
    max_chunks_per_doc=5,
    top_k_rerank=10,
    rag_min_score=0.0,
    use_rrf=True,
    rrf_k=60,
    use_search=True,
    rag_service_url="",
    rag_auth_token="",
    use_refiner=False,
    refiner_max_tokens=512,
    refiner_max_chars_per_chunk=800,
    refiner_timeout=30.0,
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
    llm_url="http://localhost:8000/v1/chat/completions",
    embed_url="http://localhost:8000/v1/embeddings",
)


def _make_rag_cfg(**overrides) -> RagConfigImpl:
    if overrides:
        return dc_replace(_RAG_CFG_BASE, **overrides)
    return _RAG_CFG_BASE


class TestRagPipelineGetCfg:
    def test_get_cfg_error_path(self, monkeypatch) -> None:
        """_ModuleConfig.get() returns {} when ConfigLoader raises."""
        import rag.pipeline as pipeline_mod

        monkeypatch.setattr(pipeline_mod._ModuleConfig, "_cache", None)
        with patch.object(ConfigLoader, "load_all", side_effect=ValueError("no file")):
            result = pipeline_mod._ModuleConfig.get()
        assert result == {}
        monkeypatch.setattr(pipeline_mod._ModuleConfig, "_cache", None)


class TestRagLlmExceptions:
    """Test new fail-fast exception types introduced in fail-fast refactor."""

    @pytest.mark.asyncio
    async def test_expand_queries_raises_ragerexpansionerror_on_http_failure(
        self,
    ) -> None:
        from rag.llm_client import RagLLM
        from rag.llm_prompts import RagExpansionError

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        mock_client.post.return_value = mock_response

        llm = RagLLM(mock_client, "http://llm/v1/chat", cfg=_make_rag_cfg(use_mqe=True))
        with pytest.raises(RagExpansionError, match="MQE expansion failed"):
            await llm.expand_queries("test query")

    @pytest.mark.asyncio
    async def test_expand_queries_raises_on_malformed_json(self) -> None:
        from rag.llm_client import RagLLM
        from rag.llm_prompts import RagExpansionError

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        import orjson

        mock_response.content = orjson.dumps(
            {"choices": [{"message": {"content": "not a json array"}}]}
        )
        mock_client.post.return_value = mock_response

        llm = RagLLM(
            mock_client,
            "http://llm/v1/chat",
            cfg=_make_rag_cfg(use_mqe=True, mqe_prompt_template="{query}"),
        )
        with pytest.raises(RagExpansionError):
            await llm.expand_queries("test query")

    @pytest.mark.asyncio
    async def test_cross_encoder_rerank_raises_ragrerankerror_on_http_failure(
        self,
    ) -> None:
        from rag.llm_client import RagLLM
        from rag.llm_prompts import RagRerankError
        from shared.types import MergedHit

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        mock_client.post.return_value = mock_response

        llm = RagLLM(mock_client, "http://llm/v1/chat", cfg=_make_rag_cfg())
        candidates = [MergedHit(chunk_id=1, content="text", url="u")]
        with pytest.raises(RagRerankError, match="rerank LLM call failed"):
            await llm.cross_encoder_rerank("query", candidates, top_k=1)


class TestAgentConfigGetCfg:
    def test_load_config_error_path(self) -> None:
        """load_config() raises ConfigLoadError when ConfigLoader raises."""
        import pytest
        from agent.config_builders import ConfigLoadError, load_config

        with patch.object(ConfigLoader, "load_all", side_effect=OSError("no file")):
            with pytest.raises(ConfigLoadError, match="Config load failed"):
                load_config()


class TestDeleteModelsGetCfg:
    def test_get_cfg_error_path(self) -> None:
        """FileDeleteConfig.load() raises ValueError when ConfigLoader raises."""
        from mcp_servers.file.delete_models import FileDeleteConfig

        with patch.object(ConfigLoader, "load", side_effect=ValueError("not found")):
            with pytest.raises(ValueError, match="not found"):
                FileDeleteConfig.load()


# ── Removal guards ────────────────────────────────────────────────────────────


def test_rag_llm_module_does_not_exist() -> None:
    """rag.llm re-export stub must be deleted; imports must use llm_client/llm_prompts."""
    import importlib

    with pytest.raises(ModuleNotFoundError):
        importlib.import_module("rag.llm")


def test_pipeline_stage_result_not_in_rag_types() -> None:
    """PipelineStageResult must be removed from rag.types (canonical: StageResult in rag.stage)."""
    import rag.types

    assert not hasattr(rag.types, "PipelineStageResult")
