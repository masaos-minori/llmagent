"""tests/mcp_servers/rag_pipeline/test_rag_pipeline_lifespan.py — Startup, failure cleanup and shutdown of the RAG pipeline service."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import mcp_servers.rag_pipeline.rag_pipeline_models as models_module
import mcp_servers.rag_pipeline.rag_pipeline_server as server_module
import pytest
from mcp_servers.rag_pipeline.rag_pipeline_service import RagPipelineMCPService


def _cfg() -> models_module.RagPipelineConfig:
    return models_module.RagPipelineConfig(
        use_mqe=True,
        use_rrf=True,
        use_rerank=True,
        top_k_search=5,
        top_k_rerank=10,
        llm_url="http://llm.local",
        embed_url="http://embed.local",
    )


class _Boom(Exception):
    """Raised in place of a pipeline construction failure."""


class TestFailedStart:
    @pytest.mark.asyncio
    async def test_client_is_closed_and_error_propagates(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        created: list[httpx.AsyncClient] = []
        real_client = httpx.AsyncClient

        def _tracking_client(*args: Any, **kwargs: Any) -> httpx.AsyncClient:
            client = real_client(*args, **kwargs)
            created.append(client)
            return client

        monkeypatch.setattr(httpx, "AsyncClient", _tracking_client)
        svc = RagPipelineMCPService()
        with (
            patch(
                "rag.pipeline.RagPipeline", side_effect=_Boom("pipeline init failed")
            ),
            pytest.raises(_Boom),
        ):
            await svc.start(_cfg())
        assert created
        assert all(client.is_closed for client in created)
        assert svc._http is None


class TestInjectedConfig:
    @pytest.mark.asyncio
    async def test_start_with_a_config_does_not_reload_it(self) -> None:
        svc = RagPipelineMCPService()
        with patch.object(
            models_module.RagPipelineConfig,
            "load",
            side_effect=AssertionError("config was reloaded"),
        ):
            await svc.start(_cfg())
        assert svc._pipeline is not None
        assert svc._http is not None
        await svc.stop()

    @pytest.mark.asyncio
    async def test_start_without_a_config_still_loads_one(self) -> None:
        svc = RagPipelineMCPService()
        with patch.object(
            models_module.RagPipelineConfig, "load", return_value=_cfg()
        ) as load:
            await svc.start()
        load.assert_called_once_with()
        await svc.stop()


class TestStop:
    @pytest.mark.asyncio
    async def test_stop_twice_is_safe(self) -> None:
        svc = RagPipelineMCPService()
        await svc.start(_cfg())
        await svc.stop()
        await svc.stop()
        assert svc._http is None

    @pytest.mark.asyncio
    async def test_stop_after_a_failed_start_is_safe(self) -> None:
        svc = RagPipelineMCPService()
        with (
            patch("rag.pipeline.RagPipeline", side_effect=_Boom("fail")),
            pytest.raises(_Boom),
        ):
            await svc.start(_cfg())
        await svc.stop()

    @pytest.mark.asyncio
    async def test_stop_on_a_bare_instance_closes_only_the_client(self) -> None:
        svc = RagPipelineMCPService.__new__(RagPipelineMCPService)
        http = AsyncMock()
        svc._http = http
        await svc.stop()
        http.aclose.assert_awaited_once()


class TestLifespan:
    @pytest.mark.asyncio
    async def test_start_gets_the_module_config_and_stop_runs_after_an_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        service = MagicMock()
        service.start = AsyncMock()
        service.stop = AsyncMock()
        monkeypatch.setattr(server_module, "_service", service)
        with pytest.raises(_Boom):
            async with server_module._lifespan(server_module.app):
                raise _Boom("while serving")
        service.start.assert_awaited_once_with(server_module._cfg)
        service.stop.assert_awaited_once()
