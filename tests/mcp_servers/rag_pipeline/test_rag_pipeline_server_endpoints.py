"""tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_endpoints.py

Characterization tests for scripts/mcp_servers/rag_pipeline/rag_pipeline_server.py's
FastAPI wiring:
  - lifespan start/stop delegation to the shared service
  - RagPipelineServiceError exception handler (503)
  - POST /rag_run_pipeline
  - POST /rag_debug_pipeline
  - GET  /v1/tools
  - POST /v1/call_tool (known and unknown tool)
  - RagPipelineMCPServer.dispatch()

These tests lock the current, observed behavior of the thin FastAPI wiring layer before
refactoring. They monkeypatch the module-level `_service` singleton so no real pipeline,
HTTP client, or filesystem access occurs. Business logic (RagPipelineMCPService,
RagRunRequest/-Response, dispatch table contents) is already covered by
tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py; this file exists solely
to close the coverage gap on rag_pipeline_server.py's own route/dispatch/lifespan code.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from mcp_servers.rag_pipeline import rag_pipeline_server as server
from mcp_servers.rag_pipeline.rag_pipeline_models import (
    RagDebugResponse,
    RagPipelineConfig,
    RagPipelineServiceError,
    RagRunResponse,
)


class _FakeService:
    """Minimal stand-in for RagPipelineMCPService, exposing only what
    rag_pipeline_server.py touches."""

    def __init__(self) -> None:
        self.start = AsyncMock()
        self.stop = AsyncMock()
        self.run_pipeline = AsyncMock()
        self.run_debug_pipeline = AsyncMock()
        self._dispatch_table: dict[str, Any] = {}

    def get_dispatch_table(self) -> dict[str, Any]:
        return self._dispatch_table


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> _FakeService:
    svc = _FakeService()
    monkeypatch.setattr(server, "_service", svc)
    return svc


@pytest.fixture
def client(fake_service: _FakeService) -> TestClient:
    # fake_service dependency ensures _service is patched before lifespan runs.
    return TestClient(server.app)


class TestLifespan:
    def test_start_and_stop_delegate_to_service(
        self, fake_service: _FakeService
    ) -> None:
        with TestClient(server.app):
            fake_service.start.assert_awaited_once()
            fake_service.stop.assert_not_awaited()
        fake_service.stop.assert_awaited_once()


class TestRagServiceErrorHandler:
    def test_service_error_maps_to_503(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        fake_service.run_pipeline.side_effect = RagPipelineServiceError("not ready")
        resp = client.post("/rag_run_pipeline", json={"query": "hello"})
        assert resp.status_code == 503
        assert resp.json() == {"error": "not ready"}


class TestRagRunPipelineEndpoint:
    def test_success_returns_run_result(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        fake_service.run_pipeline.return_value = RagRunResponse(
            query="hello",
            augmented_text="context block",
            selected_hits=[{"id": 1}],
        )
        resp = client.post("/rag_run_pipeline", json={"query": "hello"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["query"] == "hello"
        assert body["augmented_text"] == "context block"
        assert body["selected_hits"] == [{"id": 1}]
        fake_service.run_pipeline.assert_awaited_once()


class TestRagDebugPipelineEndpoint:
    def test_success_returns_debug_result(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        fake_service.run_debug_pipeline.return_value = RagDebugResponse(
            query="hello",
            augmented_text="context block",
            selected_hits=[],
            queries=["hello", "hello world"],
            merged_hits=[{"id": 1}],
            reranked_hits=[{"id": 1}],
        )
        resp = client.post("/rag_debug_pipeline", json={"query": "hello"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["queries"] == ["hello", "hello world"]
        assert body["merged_hits"] == [{"id": 1}]
        assert body["reranked_hits"] == [{"id": 1}]
        fake_service.run_debug_pipeline.assert_awaited_once()


class TestHealthEndpoint:
    def test_config_load_failure_reports_degraded(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Exercise the except-branch: ConfigLoader().load(...) itself raises."""

        class _BoomLoader:
            def load(self, _name: str) -> dict[str, Any]:
                raise RuntimeError("boom")

        monkeypatch.setattr("shared.config_loader.ConfigLoader", lambda: _BoomLoader())
        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["dependencies"] == {"config": "check failed"}


class TestToolsListEndpoint:
    def test_lists_rag_run_pipeline_with_server_key(self, client: TestClient) -> None:
        resp = client.get("/v1/tools")
        assert resp.status_code == 200
        body = resp.json()
        assert "schema_version" in body
        names = {t["name"]: t for t in body["tools"]}
        assert "rag_run_pipeline" in names
        assert names["rag_run_pipeline"]["server_key"] == "rag_pipeline"

    def test_embed_url_unset_disables_pipeline_tools_only(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server, "_cfg", RagPipelineConfig(embed_url=""))
        resp = client.get("/v1/tools?include_disabled=true")
        assert resp.status_code == 200
        names = {t["name"]: t for t in resp.json()["tools"]}
        assert names["rag_run_pipeline"]["enabled"] is False
        assert (
            names["rag_run_pipeline"]["disabled_reason"]
            == "embed_url is not configured"
        )
        assert names["rag_debug_pipeline"]["enabled"] is False
        assert names["rag_list_documents"]["enabled"] is True
        assert names["rag_delete_document"]["enabled"] is True

    def test_include_disabled_false_omits_disabled_tool(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server, "_cfg", RagPipelineConfig(embed_url=""))
        resp = client.get("/v1/tools?include_disabled=false")
        names = {t["name"] for t in resp.json()["tools"]}
        assert "rag_run_pipeline" not in names
        assert "rag_list_documents" in names

    def test_disabled_code_filters_to_matching_tools(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server, "_cfg", RagPipelineConfig(embed_url=""))
        resp = client.get(
            "/v1/tools?include_disabled=true&disabled_code=embed_url+is+not+configured"
        )
        names = {t["name"] for t in resp.json()["tools"]}
        assert names == {"rag_run_pipeline", "rag_debug_pipeline"}


class TestCallToolDisabledGate:
    def test_disabled_tool_returns_error_without_dispatch(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        monkeypatch.setattr(server, "_cfg", RagPipelineConfig(embed_url=""))
        handler = AsyncMock(return_value="ok result")
        fake_service._dispatch_table["rag_run_pipeline"] = handler
        resp = client.post(
            "/v1/call_tool", json={"name": "rag_run_pipeline", "args": {}}
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_error"] is True
        assert "embed_url is not configured" in body["result"]
        handler.assert_not_awaited()


class TestCallToolEndpoint:
    def test_dispatches_known_tool(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="ok result")
        fake_service._dispatch_table["rag_run_pipeline"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={"name": "rag_run_pipeline", "args": {"query": "hi"}},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"result": "ok result", "is_error": False}
        handler.assert_awaited_once_with({"query": "hi"})

    def test_unknown_tool_returns_error_result(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        resp = client.post("/v1/call_tool", json={"name": "not_a_tool", "args": {}})
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_error"] is True
        assert "Unknown tool" in body["result"]


class TestRagPipelineMCPServerDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_routes_through_service_table(
        self, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="dispatched")
        fake_service._dispatch_table["rag_run_pipeline"] = handler
        instance = server.RagPipelineMCPServer()
        result = await instance.dispatch("rag_run_pipeline", {"query": "hi"})
        assert result.output == "dispatched"
        assert result.is_error is False
