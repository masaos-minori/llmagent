"""tests/test_web_search_health.py

Unit tests for mcp_servers/web_search/health.py: pure in-memory provider
health-state tracking (no FastAPI/HTTP involvement), plus a small
HTTP-boundary check that `/health` folds `health.health_details()` in and
flips to 503 once `is_degraded()` is true.
"""

from __future__ import annotations

import ast
import time
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from mcp_servers.server import attach_auth_middleware
from mcp_servers.web_search import health, web_search_server


@pytest.fixture(autouse=True)
def _reset_health() -> Iterator[None]:
    """Reset both before AND after each test.

    health.py's ProviderHealth singletons are process-global, shared across
    every test file in the pytest session — a test that flips is_degraded()/
    is_browser_degraded() to True and only resets on entry (not on exit)
    leaks that degraded state into whatever test runs next (e.g.
    tests/test_mcp_server_health_status.py's "always healthy" assertion),
    which is order-dependent and can fail under pytest-randomly.
    """
    health.reset()
    health.reset_browser()
    yield
    health.reset()
    health.reset_browser()


class TestProviderHealth:
    def test_initial_state_not_degraded(self) -> None:
        assert health.is_degraded() is False
        assert health.health_details()["consecutive_failures"] == 0

    def test_provider_health_defaults(self) -> None:
        ph = health.ProviderHealth()
        assert ph.provider == "duckduckgo"
        assert ph.last_success_at is None
        assert ph.last_failure_at is None
        assert ph.last_error_type == ""
        assert ph.consecutive_failures == 0

    def test_record_success_sets_timestamp(self) -> None:
        before = time.time()
        health.record_success()
        after = time.time()

        last_success_at = health.health_details()["last_success_at"]
        assert isinstance(last_success_at, float)
        assert before <= last_success_at <= after

    def test_single_failure_not_yet_degraded(self) -> None:
        health.record_failure("timeout")

        assert health.is_degraded() is False
        assert health.health_details()["last_error_type"] == "timeout"

    def test_repeated_failures_flip_degraded(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD - 1):
            health.record_failure("network_error")
        assert health.is_degraded() is False

        health.record_failure("network_error")
        assert health.is_degraded() is True

    def test_success_after_failures_resets_degraded(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD):
            health.record_failure("provider_error")
        assert health.is_degraded() is True

        health.record_success()

        assert health.is_degraded() is False
        assert health.health_details()["consecutive_failures"] == 0

    def test_health_details_shape(self) -> None:
        details = health.health_details()

        assert set(details) == {
            "provider",
            "last_success_at",
            "last_failure_at",
            "last_error_type",
            "consecutive_failures",
            "degraded",
        }
        assert details["provider"] == "duckduckgo"
        assert isinstance(details["consecutive_failures"], int)
        assert isinstance(details["degraded"], bool)


class TestHealthEndpointWiring:
    def test_health_endpoint_reports_healthy_provider_details(self) -> None:
        client = TestClient(web_search_server.app)

        resp = client.get("/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["dependencies"] == {}
        assert data["details"]["provider"]["consecutive_failures"] == 0
        assert data["details"]["provider"]["degraded"] is False
        assert "metrics" in data["details"]

    def test_health_endpoint_degrades_after_repeated_failures(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD):
            health.record_failure("network_error")
        client = TestClient(web_search_server.app)

        resp = client.get("/health")

        assert resp.status_code == 503
        data = resp.json()
        assert "web_search_provider" in data["dependencies"]
        assert data["details"]["provider"]["degraded"] is True


class TestBrowserProviderHealth:
    """browser_fetch's health tracking is an independent singleton (UNK-03) —
    a browser_fetch failure streak must not flip search_web's own
    is_degraded(), and vice versa."""

    def test_initial_state_not_degraded(self) -> None:
        assert health.is_browser_degraded() is False
        assert health.browser_health_details()["consecutive_failures"] == 0

    def test_browser_provider_health_provider_name(self) -> None:
        assert health.browser_health_details()["provider"] == "browser_fetch"

    def test_record_browser_success_sets_timestamp(self) -> None:
        before = time.time()
        health.record_browser_success()
        after = time.time()

        last_success_at = health.browser_health_details()["last_success_at"]
        assert isinstance(last_success_at, float)
        assert before <= last_success_at <= after

    def test_repeated_browser_failures_flip_browser_degraded(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD - 1):
            health.record_browser_failure("fetch_error")
        assert health.is_browser_degraded() is False

        health.record_browser_failure("fetch_error")
        assert health.is_browser_degraded() is True

    def test_browser_failures_do_not_affect_search_web_degraded(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD):
            health.record_browser_failure("fetch_error")

        assert health.is_browser_degraded() is True
        assert health.is_degraded() is False

    def test_search_web_failures_do_not_affect_browser_degraded(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD):
            health.record_failure("network_error")

        assert health.is_degraded() is True
        assert health.is_browser_degraded() is False

    def test_browser_health_details_shape(self) -> None:
        details = health.browser_health_details()

        assert set(details) == {
            "provider",
            "last_success_at",
            "last_failure_at",
            "last_error_type",
            "consecutive_failures",
            "degraded",
        }


class TestBrowserHealthEndpointWiring:
    def test_health_endpoint_reports_browser_provider_details(self) -> None:
        client = TestClient(web_search_server.app)

        resp = client.get("/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["details"]["browser_provider"]["consecutive_failures"] == 0
        assert data["details"]["browser_provider"]["degraded"] is False
        assert "browser_metrics" in data["details"]

    def test_health_endpoint_degrades_after_repeated_browser_failures(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD):
            health.record_browser_failure("fetch_error")
        client = TestClient(web_search_server.app)

        resp = client.get("/health")

        assert resp.status_code == 503
        data = resp.json()
        assert "browser_fetch_provider" in data["dependencies"]
        assert data["details"]["browser_provider"]["degraded"] is True
        # search_web's own dependency key must not be present.
        assert "web_search_provider" not in data["dependencies"]


_SERVERS_DIR = Path(__file__).resolve().parents[3] / "scripts" / "mcp_servers"
_LOOPBACK = ("127.0.0.1", 50000)
_REMOTE = ("203.0.113.9", 50000)


def _guarded_app(*, exempt_health_on_loopback: bool) -> FastAPI:
    """Minimal app behind the real middleware: a health route and a protected route."""
    app = FastAPI()
    # Pass the keyword only when enabling it, so the default cases use the call
    # shape of every other server.
    extra = {"exempt_health_on_loopback": True} if exempt_health_on_loopback else {}
    attach_auth_middleware(app, "browser-secret", **extra)

    @app.get("/health")
    async def _health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/v1/protected")
    async def _protected() -> dict[str, str]:
        return {"data": "secret"}

    return app


class TestLoopbackHealthExemption:
    """REQ-002: only the exact health path, only from a loopback client."""

    @pytest.mark.parametrize("client_addr", [_LOOPBACK, ("::1", 50000)])
    def test_loopback_health_is_admitted_without_token(
        self, client_addr: tuple[str, int]
    ) -> None:
        client = TestClient(
            _guarded_app(exempt_health_on_loopback=True), client=client_addr
        )
        assert client.get("/health").status_code == 200

    def test_loopback_health_is_admitted_with_the_main_token(self) -> None:
        client = TestClient(
            _guarded_app(exempt_health_on_loopback=True), client=_LOOPBACK
        )
        resp = client.get("/health", headers={"Authorization": "Bearer main-secret"})
        assert resp.status_code == 200

    def test_non_loopback_health_without_token_is_rejected(self) -> None:
        client = TestClient(
            _guarded_app(exempt_health_on_loopback=True), client=_REMOTE
        )
        assert client.get("/health").status_code == 401

    def test_non_loopback_health_with_wrong_token_is_rejected(self) -> None:
        client = TestClient(
            _guarded_app(exempt_health_on_loopback=True), client=_REMOTE
        )
        resp = client.get("/health", headers={"Authorization": "Bearer main-secret"})
        assert resp.status_code == 401

    def test_non_loopback_health_with_correct_token_is_admitted(self) -> None:
        client = TestClient(
            _guarded_app(exempt_health_on_loopback=True), client=_REMOTE
        )
        resp = client.get("/health", headers={"Authorization": "Bearer browser-secret"})
        assert resp.status_code == 200

    def test_default_keeps_loopback_health_strict(self) -> None:
        client = TestClient(
            _guarded_app(exempt_health_on_loopback=False), client=_LOOPBACK
        )
        assert client.get("/health").status_code == 401

    def test_protected_route_requires_token_even_on_loopback(self) -> None:
        client = TestClient(
            _guarded_app(exempt_health_on_loopback=True), client=_LOOPBACK
        )
        assert client.get("/v1/protected").status_code == 401
        ok = client.get(
            "/v1/protected", headers={"Authorization": "Bearer browser-secret"}
        )
        assert ok.status_code == 200

    @pytest.mark.parametrize("path", ["/health/", "/healthz", "/health/extra"])
    def test_other_paths_are_not_exempt(self, path: str) -> None:
        client = TestClient(
            _guarded_app(exempt_health_on_loopback=True), client=_LOOPBACK
        )
        assert client.get(path).status_code == 401

    def test_unparsable_client_address_is_not_loopback(self) -> None:
        # The default test client host is the string "testclient", not an IP address.
        client = TestClient(_guarded_app(exempt_health_on_loopback=True))
        assert client.get("/health").status_code == 401


def _auth_middleware_calls(server_file: str) -> list[ast.Call]:
    tree = ast.parse((_SERVERS_DIR / server_file).read_text(encoding="utf-8"))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "attach_auth_middleware"
    ]


class TestHealthExemptionOptIn:
    """REQ-003 / REQ-004: only web-search opts in; the other servers keep strict /health."""

    def test_web_search_server_opts_in(self) -> None:
        (call,) = _auth_middleware_calls("web_search/web_search_server.py")
        flags = {kw.arg: kw.value for kw in call.keywords}
        value = flags.get("exempt_health_on_loopback")
        assert isinstance(value, ast.Constant) and value.value is True

    @pytest.mark.parametrize(
        "server_file",
        [
            "git/git_server.py",
            "rag_pipeline/rag_pipeline_server.py",
            "cicd/cicd_server.py",
            "mdq/mdq_server.py",
        ],
    )
    def test_other_servers_do_not_opt_in(self, server_file: str) -> None:
        calls = _auth_middleware_calls(server_file)
        assert calls, f"no attach_auth_middleware call found in {server_file}"
        for call in calls:
            assert "exempt_health_on_loopback" not in {kw.arg for kw in call.keywords}
