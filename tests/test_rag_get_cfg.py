"""tests/test_rag_get_cfg.py
Coverage for config loading and LLM error paths in rag.pipeline and rag.llm.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from shared.config_loader import ConfigLoader


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
        from rag.llm import RagExpansionError, RagLLM

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        mock_client.post.return_value = mock_response

        llm = RagLLM(mock_client, "http://llm/v1/chat", cfg={"use_mqe": True})
        with pytest.raises(RagExpansionError, match="MQE expansion failed"):
            await llm.expand_queries("test query")

    @pytest.mark.asyncio
    async def test_expand_queries_raises_on_malformed_json(self) -> None:
        from rag.llm import RagExpansionError, RagLLM

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
            cfg={"use_mqe": True, "mqe_prompt_template": "{query}", "mqe_n_queries": 3},
        )
        with pytest.raises(RagExpansionError):
            await llm.expand_queries("test query")

    @pytest.mark.asyncio
    async def test_cross_encoder_rerank_raises_ragrerankerror_on_http_failure(
        self,
    ) -> None:
        from rag.llm import RagLLM, RagRerankError
        from rag.types import MergedHit

        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=MagicMock()
        )
        mock_client.post.return_value = mock_response

        llm = RagLLM(mock_client, "http://llm/v1/chat")
        candidates = [MergedHit(chunk_id=1, content="text", url="u")]
        with pytest.raises(RagRerankError, match="rerank LLM call failed"):
            await llm.cross_encoder_rerank("query", candidates, top_k=1)


class TestAgentConfigGetCfg:
    def test_load_config_error_path(self) -> None:
        """load_config() raises ConfigLoadError when ConfigLoader raises."""
        import pytest
        from agent.config import ConfigLoadError, load_config

        with patch.object(ConfigLoader, "load_all", side_effect=OSError("no file")):
            with pytest.raises(ConfigLoadError, match="Config load failed"):
                load_config()


class TestDeleteModelsGetCfg:
    def test_get_cfg_error_path(self) -> None:
        """FileDeleteConfig.load() raises ValueError when ConfigLoader raises."""
        from mcp.file.delete_models import FileDeleteConfig

        with patch.object(ConfigLoader, "load", side_effect=ValueError("not found")):
            with pytest.raises(ValueError, match="not found"):
                FileDeleteConfig.load()
