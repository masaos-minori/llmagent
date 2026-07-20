"""tests/test_web_search_server.py

HTTP-boundary test: confirms `web_search_server.py`'s
`@app.exception_handler(WebSearchUpstreamError)` catches every new exception
subclass raised deep in the dispatch chain and returns a 502 Bad Gateway.
`search_duckduckgo` is monkeypatched at the point `service.py` looks it up
(no real network I/O).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from mcp_servers.web_search import service, web_search_server
from mcp_servers.web_search.web_search_models import (
    BrowserFetchResponse,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchProviderError,
    WebSearchTimeoutError,
)


class TestCallToolErrorClassification:
    @pytest.mark.parametrize(
        "exc_cls",
        [
            WebSearchTimeoutError,
            WebSearchNetworkError,
            WebSearchProviderError,
            WebSearchParseError,
        ],
    )
    def test_exception_subclass_returns_502(
        self, monkeypatch: pytest.MonkeyPatch, exc_cls: type[Exception]
    ) -> None:
        async def _raise(*args: object, **kwargs: object) -> None:
            raise exc_cls("boom")

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _raise)
        client = TestClient(web_search_server.app)

        resp = client.post(
            "/v1/call_tool", json={"name": "search_web", "args": {"query": "q"}}
        )

        assert resp.status_code == 502
        assert resp.json() == {"error": "boom"}


class TestBrowserFetchErrorClassification:
    def test_disallowed_domain_returns_403(self) -> None:
        client = TestClient(web_search_server.app)

        resp = client.post(
            "/v1/call_tool",
            json={
                "name": "browser_fetch",
                "args": {"url": "https://not-allowed.example/"},
            },
        )

        assert resp.status_code == 403

    def test_bad_scheme_returns_200_with_is_error(self) -> None:
        # BrowserValidationError is a ValueError subclass, so
        # mcp_servers.dispatch.dispatch_tool() catches it before it can reach
        # the @app.exception_handler(BrowserValidationError) 422 handler —
        # exactly like search_web's own ValueError (validation) path, which
        # also surfaces as a 200 response with is_error=True rather than an
        # HTTP error status. This mirrors the pre-merge standalone
        # browser-mcp server's behavior (it used the same shared dispatch_tool()).
        client = TestClient(web_search_server.app)

        resp = client.post(
            "/v1/call_tool",
            json={"name": "browser_fetch", "args": {"url": "ftp://example.com/"}},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["is_error"] is True
        assert "Validation error" in body["result"]


class TestBrowserFetchToolsEndpoint:
    def test_tools_endpoint_lists_both_tools_under_web_search_server_key(self) -> None:
        client = TestClient(web_search_server.app)

        resp = client.get("/v1/tools")

        assert resp.status_code == 200
        tools = {t["name"]: t for t in resp.json()["tools"]}
        assert "search_web" in tools
        assert "browser_fetch" in tools
        assert tools["search_web"]["server_key"] == "web_search"
        assert tools["browser_fetch"]["server_key"] == "web_search"


class TestBrowserFetchDispatchSuccess:
    def test_success_returns_200(self, monkeypatch: pytest.MonkeyPatch) -> None:
        mock_result = BrowserFetchResponse(
            text="ok",
            truncated=False,
            url="https://example.com/page",
            status_code=200,
            elapsed_sec=0.1,
        )

        async def _fake(args: dict[str, object]) -> BrowserFetchResponse:
            return mock_result

        monkeypatch.setattr(service, "fetch_browser", _fake)
        client = TestClient(web_search_server.app)

        resp = client.post(
            "/v1/call_tool",
            json={"name": "browser_fetch", "args": {"url": "https://example.com/page"}},
        )

        assert resp.status_code == 200
