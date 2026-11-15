"""tests/mcp_servers/test_server_idempotency_boundary.py

Characterization tests for the REQ-004 idempotency-key boundary middleware that
``attach_auth_middleware`` registers in ``scripts/mcp_servers/server.py``.

The boundary rejects a keyless side-effecting ``POST /v1/call_tool`` before
dispatch. The canonical side-effect set (``ALL_SIDE_EFFECTING_TOOLS`` from
``shared.tool_constants``, defined by ``sideeffect001``) is not present yet, so
each test injects a controlled set via ``monkeypatch`` to exercise the mechanism;
one test locks the inert (deferred) behavior until the canonical set lands.
"""

from __future__ import annotations

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
