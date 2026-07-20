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
from mcp_servers.web_search import web_search_server
from mcp_servers.web_search.web_search_models import (
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
