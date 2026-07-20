"""tests/test_web_search_audit.py

HTTP-boundary test: confirms `web_search_server.py::call_tool()` emits
exactly one classified audit record for every outcome — success, zero-result,
validation error, unknown tool, and provider timeout — including the paths
that used to bypass `_audit_log(...)` entirely because they raised before
reaching it. `search_duckduckgo` is monkeypatched at the point `service.py`
looks it up (no real network I/O).
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mcp_servers.web_search import health, metrics, service, web_search_server
from mcp_servers.web_search.web_search_models import (
    BrowserFetchResponse,
    SearchResult,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchTimeoutError,
    WebSearchUpstreamError,
)


@pytest.fixture(autouse=True)
def _reset_state() -> Iterator[None]:
    """Reset both before AND after each test — see
    test_web_search_health.py's `_reset_health` fixture for the rationale."""
    health.reset()
    metrics.reset()
    health.reset_browser()
    metrics.reset_browser()
    yield
    health.reset()
    metrics.reset()
    health.reset_browser()
    metrics.reset_browser()


class _RecordingAudit:
    """Stub replacing `_audit_log` that records each call's kwargs."""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def __call__(self, server_logger: Any, **kwargs: Any) -> None:
        self.calls.append(kwargs)


@pytest.fixture
def audit_stub(monkeypatch: pytest.MonkeyPatch) -> _RecordingAudit:
    stub = _RecordingAudit()
    monkeypatch.setattr(web_search_server, "_audit_log", stub)
    return stub


@pytest.fixture
def client() -> TestClient:
    return TestClient(web_search_server.app)


class TestAuditAlwaysFires:
    def test_audit_emitted_on_success(
        self,
        monkeypatch: pytest.MonkeyPatch,
        audit_stub: _RecordingAudit,
        client: TestClient,
    ) -> None:
        async def _fake(*args: object, **kwargs: object) -> list[SearchResult]:
            return [SearchResult(title="t", url="u", body="b", provider="duckduckgo")]

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _fake)

        resp = client.post(
            "/v1/call_tool", json={"name": "search_web", "args": {"query": "python"}}
        )

        assert resp.status_code == 200
        assert len(audit_stub.calls) == 1
        assert audit_stub.calls[0]["outcome"] == "ok"
        assert audit_stub.calls[0]["error_type"] == ""

    def test_audit_emitted_on_zero_result(
        self,
        monkeypatch: pytest.MonkeyPatch,
        audit_stub: _RecordingAudit,
        client: TestClient,
    ) -> None:
        async def _fake(*args: object, **kwargs: object) -> list[SearchResult]:
            return []

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _fake)

        resp = client.post(
            "/v1/call_tool", json={"name": "search_web", "args": {"query": "python"}}
        )

        # formatters.py no longer raises on empty results (prior cluster) — a
        # zero-result search is a normal, successful dispatch, not an error.
        assert resp.status_code == 200
        assert len(audit_stub.calls) == 1
        assert audit_stub.calls[0]["outcome"] == "ok"
        assert audit_stub.calls[0]["error_type"] == ""

    def test_audit_emitted_on_validation_error(
        self, audit_stub: _RecordingAudit, client: TestClient
    ) -> None:
        resp = client.post(
            "/v1/call_tool", json={"name": "search_web", "args": {"query": ""}}
        )

        assert resp.status_code == 200
        assert len(audit_stub.calls) == 1
        assert audit_stub.calls[0]["outcome"] == "error"
        assert audit_stub.calls[0]["error_type"] == "validation_error"

    def test_audit_emitted_on_unknown_tool(
        self, audit_stub: _RecordingAudit, client: TestClient
    ) -> None:
        resp = client.post(
            "/v1/call_tool", json={"name": "not_a_real_tool", "args": {}}
        )

        assert resp.status_code == 200
        assert len(audit_stub.calls) == 1
        assert audit_stub.calls[0]["outcome"] == "error"
        assert audit_stub.calls[0]["error_type"] == "unknown_tool"

    def test_audit_emitted_on_timeout(
        self,
        monkeypatch: pytest.MonkeyPatch,
        audit_stub: _RecordingAudit,
        client: TestClient,
    ) -> None:
        async def _raise(*args: object, **kwargs: object) -> list[SearchResult]:
            raise WebSearchTimeoutError("DuckDuckGo search timed out after 10.0s")

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _raise)

        resp = client.post(
            "/v1/call_tool", json={"name": "search_web", "args": {"query": "python"}}
        )

        assert resp.status_code == 502
        assert len(audit_stub.calls) == 1
        assert audit_stub.calls[0]["outcome"] == "error"
        assert audit_stub.calls[0]["error_type"] == "timeout"

    def test_audit_emitted_on_unexpected_error(
        self,
        monkeypatch: pytest.MonkeyPatch,
        audit_stub: _RecordingAudit,
        client: TestClient,
    ) -> None:
        async def _raise(*args: object, **kwargs: object) -> list[SearchResult]:
            raise RuntimeError("boom")

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _raise)

        with pytest.raises(RuntimeError):
            client.post(
                "/v1/call_tool",
                json={"name": "search_web", "args": {"query": "python"}},
            )

        assert len(audit_stub.calls) == 1
        assert audit_stub.calls[0]["outcome"] == "error"
        assert audit_stub.calls[0]["error_type"] == "unexpected_error"


class TestAuditBrowserFetch:
    """browser_fetch shares call_tool()'s audit-logging code path with
    search_web, but its target/detail is built from `url`, not `query`."""

    def test_audit_emitted_on_success_with_url_preview(
        self,
        monkeypatch: pytest.MonkeyPatch,
        audit_stub: _RecordingAudit,
        client: TestClient,
    ) -> None:
        mock_result = BrowserFetchResponse(
            text="ok",
            truncated=False,
            url="https://example.com/page",
            status_code=200,
            elapsed_sec=0.1,
        )

        async def _fake(args: dict[str, Any]) -> BrowserFetchResponse:
            return mock_result

        monkeypatch.setattr(service, "fetch_browser", _fake)

        resp = client.post(
            "/v1/call_tool",
            json={"name": "browser_fetch", "args": {"url": "https://example.com/page"}},
        )

        assert resp.status_code == 200
        assert len(audit_stub.calls) == 1
        call = audit_stub.calls[0]
        assert call["outcome"] == "ok"
        assert call["error_type"] == ""
        assert call["server_key"] == "web_search"
        assert call["target"] == "https://example.com/page"
        assert "url_preview=" in call["detail"]
        # search_web's query-specific detail fields must not leak in.
        assert "query_hash=" not in call["detail"]

    def test_audit_emitted_on_authorization_error(
        self, audit_stub: _RecordingAudit, client: TestClient
    ) -> None:
        resp = client.post(
            "/v1/call_tool",
            json={
                "name": "browser_fetch",
                "args": {"url": "https://not-allowed.example/"},
            },
        )

        assert resp.status_code == 403
        assert len(audit_stub.calls) == 1
        assert audit_stub.calls[0]["outcome"] == "error"
        assert audit_stub.calls[0]["error_type"] == "authorization_error"
        assert audit_stub.calls[0]["target"] == "https://not-allowed.example/"

    def test_audit_emitted_on_validation_error(
        self, audit_stub: _RecordingAudit, client: TestClient
    ) -> None:
        # BrowserValidationError is a ValueError subclass, so dispatch_tool()
        # converts it into an is_error=True DispatchResult (200 response)
        # before it can reach the BrowserValidationError exception_handler —
        # same as search_web's own ValueError validation path.
        resp = client.post(
            "/v1/call_tool",
            json={"name": "browser_fetch", "args": {"url": "ftp://example.com/"}},
        )

        assert resp.status_code == 200
        assert len(audit_stub.calls) == 1
        assert audit_stub.calls[0]["outcome"] == "error"
        assert audit_stub.calls[0]["error_type"] == "validation_error"


class TestClassifyDispatchError:
    """Direct unit tests for the module-level classification helpers."""

    def test_validation_error_prefix(self) -> None:
        assert (
            web_search_server._classify_dispatch_error("Validation error: bad input")
            == "validation_error"
        )

    def test_unknown_tool_prefix(self) -> None:
        assert (
            web_search_server._classify_dispatch_error("Unknown tool: not_real")
            == "unknown_tool"
        )

    def test_invalid_tool_name(self) -> None:
        assert (
            web_search_server._classify_dispatch_error(
                "Tool name must be a non-empty string"
            )
            == "invalid_tool_name"
        )

    def test_unrecognized_output_falls_back_to_dispatch_error(self) -> None:
        assert (
            web_search_server._classify_dispatch_error("something else entirely")
            == "dispatch_error"
        )


class TestClassifyUpstreamError:
    """Direct unit tests for upstream exception classification."""

    def test_timeout_error(self) -> None:
        exc = WebSearchTimeoutError("timed out")
        assert web_search_server._classify_upstream_error(exc) == "timeout"

    def test_network_error(self) -> None:
        exc = WebSearchNetworkError("network down")
        assert web_search_server._classify_upstream_error(exc) == "network_error"

    def test_parse_error(self) -> None:
        exc = WebSearchParseError("bad shape")
        assert web_search_server._classify_upstream_error(exc) == "parse_error"

    def test_generic_upstream_error_falls_back_to_provider_error(self) -> None:
        exc = WebSearchUpstreamError("some other provider failure")
        assert web_search_server._classify_upstream_error(exc) == "provider_error"
