"""tests/mcp_servers/shell/test_shell_server_endpoints.py

Characterization tests for scripts/mcp_servers/shell/shell_server.py's FastAPI wiring:
  - POST /shell_run (success path, and the two registered exception handlers)
  - GET  /v1/tools
  - POST /v1/call_tool (success and unknown-tool paths)
  - ShellMCPServer.dispatch()

These tests lock the current, observed behavior of the thin FastAPI wiring layer before
refactoring. They monkeypatch the module-level `_service` singleton so no real subprocess
or filesystem access occurs. Business logic (ShellService, ShellRunRequest/-Response,
sandboxing) is already covered by tests/mcp_servers/shell/test_shell_mcp_service.py; this
file exists solely to close the coverage gap on shell_server.py's own route/dispatch code.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from mcp_servers.shell import server as shell_server
from mcp_servers.shell.shell_models import (
    ShellAuthorizationError,
    ShellRunResponse,
    ShellValidationError,
)


class _FakeService:
    """Minimal stand-in for ShellService, exposing only what shell_server.py touches."""

    sandbox_backend = "none"

    def __init__(self) -> None:
        self.run_command = AsyncMock()
        self._dispatch_table: dict[str, Any] = {}

    def get_dispatch_table(self) -> dict[str, Any]:
        return self._dispatch_table


@pytest.fixture
def fake_service(monkeypatch: pytest.MonkeyPatch) -> _FakeService:
    svc = _FakeService()
    monkeypatch.setattr(shell_server, "_service", svc)
    return svc


@pytest.fixture
def client() -> TestClient:
    return TestClient(shell_server.app)


class TestShellRunEndpoint:
    def test_success_returns_run_result(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        fake_service.run_command.return_value = ShellRunResponse(
            stdout="hello\n",
            stderr="",
            exit_code=0,
            timed_out=False,
            truncated=False,
            elapsed_sec=0.01,
        )
        resp = client.post("/shell_run", json={"command": "echo hello"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["stdout"] == "hello\n"
        assert body["exit_code"] == 0
        fake_service.run_command.assert_awaited_once()

    def test_authorization_error_maps_to_403(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        fake_service.run_command.side_effect = ShellAuthorizationError(
            "cmd not allowed"
        )
        resp = client.post("/shell_run", json={"command": "rm -rf /"})
        assert resp.status_code == 403
        assert resp.json()["detail"] == "cmd not allowed"

    def test_validation_error_maps_to_422(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        fake_service.run_command.side_effect = ShellValidationError("bad cwd")
        resp = client.post("/shell_run", json={"command": "ls", "cwd": "/nope"})
        assert resp.status_code == 422
        assert resp.json()["detail"] == "bad cwd"


class TestToolsListEndpoint:
    def test_lists_shell_run_with_server_key(self, client: TestClient) -> None:
        resp = client.get("/v1/tools")
        assert resp.status_code == 200
        body = resp.json()
        assert "schema_version" in body
        names = {t["name"]: t for t in body["tools"]}
        assert "shell_run" in names
        assert names["shell_run"]["server_key"] == "shell"


class TestCallToolEndpoint:
    def test_dispatches_known_tool_and_audit_logs(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="ok: 0")
        fake_service._dispatch_table["shell_run"] = handler
        resp = client.post(
            "/v1/call_tool",
            json={"name": "shell_run", "args": {"command": "echo hi"}},
            headers={"x-session-id": "sess-1", "x-request-id": "req-1"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"result": "ok: 0", "is_error": False}
        handler.assert_awaited_once_with({"command": "echo hi"})

    def test_unknown_tool_returns_error_result(
        self, client: TestClient, fake_service: _FakeService
    ) -> None:
        resp = client.post("/v1/call_tool", json={"name": "not_a_tool", "args": {}})
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_error"] is True
        assert "Unknown tool" in body["result"]


class TestShellMCPServerDispatch:
    @pytest.mark.asyncio
    async def test_dispatch_routes_through_service_table(
        self, fake_service: _FakeService
    ) -> None:
        handler = AsyncMock(return_value="dispatched")
        fake_service._dispatch_table["shell_run"] = handler
        server = shell_server.ShellMCPServer()
        result = await server.dispatch("shell_run", {"command": "true"})
        assert result.output == "dispatched"
        assert result.is_error is False
