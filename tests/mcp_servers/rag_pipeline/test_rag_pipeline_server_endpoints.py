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

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from mcp_servers.rag_pipeline import rag_pipeline_health_probe as probe
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


_PROBE_TARGET = (
    "mcp_servers.rag_pipeline.rag_pipeline_health_probe.probe_embed_reachable"
)


def _stub_probe(monkeypatch: pytest.MonkeyPatch, state: str) -> AsyncMock:
    """Replace the embed probe with a call-recording stub returning `state`."""
    stub = AsyncMock(return_value=state)
    monkeypatch.setattr(_PROBE_TARGET, stub)
    return stub


def _stub_config(monkeypatch: pytest.MonkeyPatch, cfg: dict[str, Any]) -> None:
    """Make ConfigLoader().load(...) return `cfg` for the health check."""

    class _Loader:
        def load(self, _name: str) -> dict[str, Any]:
            return cfg

    monkeypatch.setattr("shared.config_loader.ConfigLoader", lambda: _Loader())


class _CountingCaller:
    """Embed transport stub that records each GET and answers with `status_code`."""

    def __init__(self, status_code: int = 200) -> None:
        self.calls = 0
        self._status_code = status_code

    async def get(self, _url: str, timeout: float) -> Any:
        self.calls += 1
        return type("_Resp", (), {"status_code": self._status_code})()


class _HangingCaller:
    """Embed transport stub that never answers."""

    async def get(self, _url: str, timeout: float) -> Any:
        await asyncio.Event().wait()


@pytest.fixture
def client(fake_service: _FakeService) -> TestClient:
    # fake_service dependency ensures _service is patched before lifespan runs.
    return TestClient(
        server.app, headers={"Authorization": f"Bearer {server._cfg.auth_token}"}
    )


class TestInboundAuth:
    def test_server_has_a_non_empty_token_in_tests(self) -> None:
        assert server._cfg.auth_token

    def test_missing_authorization_header_is_rejected(
        self, fake_service: _FakeService
    ) -> None:
        resp = TestClient(server.app).get("/v1/tools")
        assert resp.status_code == 401
        assert resp.json() == {"error": "Unauthorized"}

    def test_wrong_token_is_rejected_before_dispatch(
        self, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="ok result")
        fake_service._dispatch_table["rag_run_pipeline"] = handler
        resp = TestClient(server.app).post(
            "/v1/call_tool",
            json={"name": "rag_run_pipeline", "args": {}},
            headers={"Authorization": "Bearer wrong-token"},
        )
        assert resp.status_code == 401
        handler.assert_not_awaited()

    def test_x_rag_token_header_is_not_accepted(
        self, fake_service: _FakeService
    ) -> None:
        resp = TestClient(server.app).get(
            "/v1/tools", headers={"X-RAG-Token": server._cfg.auth_token}
        )
        assert resp.status_code == 401

    def test_correct_token_is_accepted(self, client: TestClient) -> None:
        assert client.get("/v1/tools").status_code == 200


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


class TestCorpusIdentityExposure:
    """RAGCORPUS001 REQ-002: health + search responses carry the server identity.

    These tests lock the FastAPI wiring that attaches ``_identity_payload()`` to the
    health ``details`` and to both search responses. ``_identity_payload`` is replaced
    with a deterministic stub so the tests assert only the wiring (not the DB read);
    the read itself is covered by
    tests/mcp_servers/rag_pipeline/test_rag_pipeline_server_identity.py.
    """

    _SENTINEL = {
        "corpus_id": "sentinel-corpus",
        "index_generation": 7,
        "schema_version": "1",
        "embedding_model_id": "test-embed-v1",
        "normalization_version": "1",
        "chunking_policy_version": "1",
        "verified": True,
    }

    def _stub_identity(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(server, "_identity_payload", lambda: dict(self._SENTINEL))

    def test_health_carries_corpus_identity(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        self._stub_identity(monkeypatch)
        _stub_config(monkeypatch, {"embed_url": "http://embed.invalid:8081"})
        _stub_probe(monkeypatch, "reachable")
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["details"]["corpus_identity"] == self._SENTINEL

    def test_run_pipeline_carries_corpus_identity(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self._stub_identity(monkeypatch)
        fake_service.run_pipeline.return_value = RagRunResponse(
            query="hello",
            augmented_text="context block",
            selected_hits=[{"id": 1}],
        )
        resp = client.post("/rag_run_pipeline", json={"query": "hello"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["corpus_identity"] == self._SENTINEL
        # Pre-existing fields unchanged (AC-5).
        assert body["query"] == "hello"
        assert body["augmented_text"] == "context block"
        assert body["selected_hits"] == [{"id": 1}]

    def test_debug_pipeline_carries_corpus_identity_inherited(
        self,
        client: TestClient,
        fake_service: _FakeService,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        self._stub_identity(monkeypatch)
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
        assert body["corpus_identity"] == self._SENTINEL
        # Pre-existing debug fields unchanged (AC-5); RagDebugResponse inherits the field.
        assert body["queries"] == ["hello", "hello world"]
        assert body["merged_hits"] == [{"id": 1}]
        assert body["reranked_hits"] == [{"id": 1}]


class TestHealthEndpoint:
    def test_config_load_failure_reports_degraded(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Exercise the except-branch: ConfigLoader().load(...) itself raises."""

        class _BoomLoader:
            def load(self, _name: str) -> dict[str, Any]:
                raise RuntimeError("boom")

        monkeypatch.setattr("shared.config_loader.ConfigLoader", lambda: _BoomLoader())
        stub = _stub_probe(monkeypatch, "reachable")
        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["dependencies"] == {"config": "check failed"}
        stub.assert_not_called()

    def test_reachable_embed_url_reports_ok(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _stub_config(monkeypatch, {"embed_url": "http://embed.invalid:8081"})
        stub = _stub_probe(monkeypatch, "reachable")
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["dependencies"] == {}
        assert body["ready"] is True
        stub.assert_awaited_once_with("http://embed.invalid:8081")

    def test_unreachable_embed_url_reports_degraded_but_live(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _stub_config(monkeypatch, {"embed_url": "http://embed.invalid:8081"})
        _stub_probe(monkeypatch, "unreachable")
        resp = client.get("/health")
        assert resp.status_code == 503
        body = resp.json()
        assert body["status"] == "degraded"
        assert body["dependencies"] == {"embed_url": "unreachable"}
        assert body["ready"] is False
        assert body["liveness"] is True
        assert body["restart_recommended"] is False
        assert body["operator_action_required"] is True

    @pytest.mark.parametrize("cfg", [{}, {"embed_url": 123}, {"embed_url": ""}])
    def test_absent_or_non_string_embed_url_is_not_probed(
        self,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        cfg: dict[str, Any],
    ) -> None:
        _stub_config(monkeypatch, cfg)
        stub = _stub_probe(monkeypatch, "reachable")
        resp = client.get("/health")
        assert resp.status_code == 503
        assert resp.json()["dependencies"] == {"embed_url": "not configured"}
        stub.assert_not_called()

    def test_probe_fault_is_unreachable_not_config_failure(
        self, client: TestClient, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _stub_config(monkeypatch, {"embed_url": "http://embed.invalid:8081"})
        stub = _stub_probe(monkeypatch, "reachable")
        stub.side_effect = RuntimeError("boom")
        resp = client.get("/health")
        assert resp.status_code == 503
        assert resp.json()["dependencies"] == {"embed_url": "unreachable"}


class TestEmbedProbe:
    @pytest.fixture(autouse=True)
    def _fresh_cache(self) -> None:
        probe.reset_cache()

    def test_ok_answer_is_reachable(self) -> None:
        caller = _CountingCaller(200)
        state = asyncio.run(
            probe.probe_embed_reachable("http://embed.invalid:8081/", caller=caller)
        )
        assert state == "reachable"

    def test_non_200_answer_is_unreachable(self) -> None:
        caller = _CountingCaller(503)
        state = asyncio.run(
            probe.probe_embed_reachable("http://embed.invalid:8081", caller=caller)
        )
        assert state == "unreachable"

    def test_hanging_transport_resolves_within_the_timeout(self) -> None:
        started = time.monotonic()
        state = asyncio.run(
            probe.probe_embed_reachable(
                "http://embed.invalid:8081", caller=_HangingCaller(), timeout=0.05
            )
        )
        assert state == "unreachable"
        assert time.monotonic() - started < 1.0

    def test_repeated_calls_within_the_ttl_issue_one_request(self) -> None:
        caller = _CountingCaller(200)

        async def _poll() -> list[str]:
            return [
                await probe.probe_embed_reachable(
                    "http://embed.invalid:8081", caller=caller
                )
                for _ in range(3)
            ]

        assert asyncio.run(_poll()) == ["reachable"] * 3
        assert caller.calls == 1

    def test_reset_cache_forces_a_new_request(self) -> None:
        caller = _CountingCaller(200)
        asyncio.run(
            probe.probe_embed_reachable("http://embed.invalid:8081", caller=caller)
        )
        probe.reset_cache()
        asyncio.run(
            probe.probe_embed_reachable("http://embed.invalid:8081", caller=caller)
        )
        assert caller.calls == 2


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
