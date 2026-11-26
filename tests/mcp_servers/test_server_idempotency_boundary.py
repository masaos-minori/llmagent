"""tests/mcp_servers/test_server_idempotency_boundary.py

Characterization tests for the REQ-004 idempotency-key boundary middleware that
``attach_auth_middleware`` registers in ``scripts/mcp_servers/server.py``.

The boundary rejects a keyless side-effecting ``POST /v1/call_tool`` before
dispatch. The canonical side-effect set (``ALL_SIDE_EFFECTING_TOOLS`` from
``shared.tool_constants``) is non-empty. Most tests inject a controlled set via
``monkeypatch`` to exercise the mechanism, ``TestRealSideEffectingSetRejected``
sweeps the real, unpatched set, and one test locks the empty-set fast path.
``TestBoundaryRegisteredOnEveryApp`` repeats the rejection and auth-first checks
against every real production app to prove per-app registration.
"""

from __future__ import annotations

import importlib
from typing import Any, cast

import pytest
from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.testclient import TestClient
from mcp_servers import server as server_module

from tests.mcp_servers._auth_headers import MCP_TEST_AUTH_HEADERS

_SIDE_EFFECTING = {"shell_run", "delete_document"}
_READ_ONLY = {"read_config"}


def _build_app(token: str = "test-token") -> FastAPI:
    """Minimal FastAPI app with a /v1/call_tool route plus the shared middleware."""
    app = FastAPI()

    @app.post("/v1/call_tool")
    async def _call_tool(req: dict[str, Any]) -> dict[str, Any]:
        return {"name": req.get("name"), "ok": True}

    @app.get("/health")
    async def _health() -> dict[str, Any]:
        return {"status": "ok"}

    server_module.attach_auth_middleware(app, token)
    return app


def _client(app: FastAPI, *, authorized: bool = True) -> TestClient:
    headers = MCP_TEST_AUTH_HEADERS if authorized else {}
    return TestClient(app, headers=headers)


class TestKeylessSideEffectRejected:
    def test_keyless_side_effecting_call_is_rejected_422(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        client = _client(_build_app())
        response = client.post("/v1/call_tool", json={"name": "shell_run"})
        assert response.status_code == 422

    def test_rejection_message_names_the_requirement(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        client = _client(_build_app())
        response = client.post("/v1/call_tool", json={"name": "delete_document"})
        assert "X-Idempotency-Key" in response.json()["error"]

    @pytest.mark.parametrize("key", [" ", "  ", "\t", " \t "])
    def test_whitespace_only_key_counts_as_missing(
        self, monkeypatch: pytest.MonkeyPatch, key: str
    ) -> None:
        # A whitespace-only key carries no dedup identity: it is treated as missing.
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        client = _client(_build_app())
        response = client.post(
            "/v1/call_tool",
            json={"name": "shell_run"},
            headers={"X-Idempotency-Key": key},
        )
        assert response.status_code == 422


class TestRealSideEffectingSetRejected:
    """Every tool of the real, unpatched `ALL_SIDE_EFFECTING_TOOLS` needs a key."""

    @staticmethod
    def _real_set() -> frozenset[str]:
        return frozenset(server_module.ALL_SIDE_EFFECTING_TOOLS)

    def test_the_real_set_is_not_empty(self) -> None:
        assert self._real_set()

    @pytest.mark.parametrize("tool", sorted(server_module.ALL_SIDE_EFFECTING_TOOLS))
    def test_a_keyless_call_is_rejected_422(self, tool: str) -> None:
        client = _client(_build_app())
        response = client.post("/v1/call_tool", json={"name": tool})
        assert response.status_code == 422

    @pytest.mark.parametrize("tool", sorted(server_module.ALL_SIDE_EFFECTING_TOOLS))
    def test_a_whitespace_key_is_rejected_422(self, tool: str) -> None:
        client = _client(_build_app())
        response = client.post(
            "/v1/call_tool",
            json={"name": tool},
            headers={"X-Idempotency-Key": "  \t"},
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("tool", sorted(server_module.ALL_SIDE_EFFECTING_TOOLS))
    def test_a_keyed_call_passes_the_boundary(self, tool: str) -> None:
        """Control: with a key the same call is not stopped by the boundary."""
        client = _client(_build_app())
        response = client.post(
            "/v1/call_tool",
            json={"name": tool},
            headers={"X-Idempotency-Key": "k-control"},
        )
        assert response.status_code == 200

    def test_a_real_app_rejects_a_keyless_call_for_every_tool(self) -> None:
        import importlib

        module = importlib.import_module("mcp_servers.shell.shell_server")
        client = TestClient(module.app, headers=MCP_TEST_AUTH_HEADERS)
        statuses = {
            tool: client.post("/v1/call_tool", json={"name": tool}).status_code
            for tool in sorted(self._real_set())
        }
        assert set(statuses.values()) == {422}


class TestKeyedSideEffectDispatched:
    def test_keyed_side_effecting_call_passes_the_boundary(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        client = _client(_build_app())
        response = client.post(
            "/v1/call_tool",
            json={"name": "shell_run"},
            headers={"X-Idempotency-Key": "key-1"},
        )
        assert response.status_code == 200
        assert response.json()["name"] == "shell_run"


class TestKeylessReadonlyAllowed:
    def test_keyless_read_only_call_passes_the_boundary(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        client = _client(_build_app())
        response = client.post("/v1/call_tool", json={"name": "read_config"})
        assert response.status_code == 200
        assert response.json()["name"] == "read_config"

    def test_keyless_unknown_tool_passes_the_boundary(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        client = _client(_build_app())
        response = client.post("/v1/call_tool", json={"name": "unknown_tool"})
        assert response.status_code == 200


class TestAuthRunsBeforeBoundary:
    def test_unauthorized_request_gets_401_not_422(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        client = _client(_build_app(), authorized=False)
        response = client.post("/v1/call_tool", json={"name": "shell_run"})
        assert response.status_code == 401


class TestInertUntilCanonicalSet:
    def test_keyless_side_effecting_passes_when_set_absent(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # sideeffect001 not landed: ALL_SIDE_EFFECTING_TOOLS is None, so the
        # boundary is wired in but inert (the deferred REQ-004 behavior).
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", None)
        client = _client(_build_app())
        response = client.post("/v1/call_tool", json={"name": "shell_run"})
        assert response.status_code == 200


class _BodyRequest:
    """Minimal Request stand-in exposing only the ``body()`` coroutine under test."""

    def __init__(self, payload: bytes) -> None:
        self._payload = payload

    async def body(self) -> bytes:
        return self._payload


class _RaisingBodyRequest:
    """Request whose ``body()`` raises, exercising the boundary's never-500 guard."""

    async def body(self) -> bytes:
        raise RuntimeError("body unavailable")


class TestReadCallToolBodyDefensivePaths:
    """The boundary helper must never turn a malformed request into a 500."""

    async def test_body_exception_returns_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        result = await server_module._read_call_tool_body(
            cast(Request, _RaisingBodyRequest())
        )
        assert result == {}

    async def test_empty_body_returns_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        result = await server_module._read_call_tool_body(
            cast(Request, _BodyRequest(b""))
        )
        assert result == {}

    async def test_invalid_json_returns_empty(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        result = await server_module._read_call_tool_body(
            cast(Request, _BodyRequest(b"{not json"))
        )
        assert result == {}


class TestImportFallbackKeepsBoundaryInert:
    def test_missing_tool_constants_module_is_inert(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # If shared.tool_constants cannot be imported, the module import must not
        # fail: ALL_SIDE_EFFECTING_TOOLS resolves to None and the boundary stays
        # inert (the deferred REQ-004 behavior). Force the ImportError branch via a
        # meta_path blocker, then restore the normally-imported module.
        class _BlockingFinder:
            def find_spec(self, name, path=None, target=None):
                if name == "shared.tool_constants":
                    raise ImportError(name)
                return None

        import importlib as _real_importlib
        import sys

        # shared.tool_constants is cached in sys.modules from the initial import, so
        # import_module() returns the cache without consulting meta_path. Drop it so
        # the reload re-imports and the blocker forces the ImportError branch.
        sys.modules.pop("shared.tool_constants", None)
        blocker = _BlockingFinder()
        sys.meta_path.insert(0, blocker)
        try:
            _real_importlib.reload(server_module)
            assert server_module.ALL_SIDE_EFFECTING_TOOLS is None
        finally:
            sys.meta_path.remove(blocker)
            _real_importlib.reload(server_module)


class TestNonCallToolPathsUntouched:
    def test_health_path_bypasses_the_boundary(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        client = _client(_build_app())
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


# Every production MCP app. Keep in step with the apps in scripts/mcp_servers.
_APP_MODULES = (
    "mcp_servers.shell.shell_server",
    "mcp_servers.git.git_server",
    "mcp_servers.web_search.web_search_server",
    "mcp_servers.file.delete_server",
    "mcp_servers.file.write_server",
    "mcp_servers.file.read_server",
    "mcp_servers.github.github_server",
    "mcp_servers.cicd.cicd_server",
    "mcp_servers.rag_pipeline.rag_pipeline_server",
    "mcp_servers.mdq.mdq_server",
)


class TestBoundaryRegisteredOnEveryApp:
    """Per-app registration: each real app wires the boundary through
    attach_auth_middleware, not just the synthetic app above. The rejected tool
    name needs no registry entry — the boundary rejects on the injected set
    before dispatch, so the 422 is proof of registration alone."""

    @pytest.mark.parametrize("module_name", _APP_MODULES)
    def test_keyless_side_effecting_call_rejected_on_every_app(
        self, monkeypatch: pytest.MonkeyPatch, module_name: str
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        module = importlib.import_module(module_name)
        client = TestClient(module.app, headers=MCP_TEST_AUTH_HEADERS)
        response = client.post("/v1/call_tool", json={"name": "shell_run"})
        assert response.status_code == 422

    @pytest.mark.parametrize("module_name", _APP_MODULES)
    def test_unauthorized_request_gets_401_before_boundary_on_every_app(
        self, monkeypatch: pytest.MonkeyPatch, module_name: str
    ) -> None:
        monkeypatch.setattr(server_module, "ALL_SIDE_EFFECTING_TOOLS", _SIDE_EFFECTING)
        module = importlib.import_module(module_name)
        client = TestClient(module.app)
        response = client.post("/v1/call_tool", json={"name": "shell_run"})
        assert response.status_code == 401
