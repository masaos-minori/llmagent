"""tests/test_web_search_formatters.py

Formatter-layer tests for `fdisp_search_web()`: zero-result responses format
as "No search results found." with no exception raised, and normal-result
formatting is unchanged. `search_web()`'s own orchestration (validation,
provider call, health/metrics recording) moved to `service.py` and is covered
by `tests/test_web_search_service.py`; here `search_duckduckgo` is
monkeypatched at the point `service.py` looks it up — no dependency on
`search_provider.py`'s internals.
"""

from __future__ import annotations

import pytest
from mcp_servers.web_search.formatters import (
    dispatch_web_tool,
    fdisp_browser_fetch,
    fdisp_search_web,
)
from mcp_servers.web_search.web_search_models import BrowserFetchResponse, SearchResult


class TestSearchWebEmptyResults:
    async def test_fdisp_search_web_empty_message(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _fake(*args: object, **kwargs: object) -> list[SearchResult]:
            return []

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _fake)

        assert await fdisp_search_web({"query": "x"}) == "No search results found."


class TestFdispSearchWebNormalResults:
    async def test_formats_results_unchanged(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_results = [
            SearchResult(title="A", url="u1", body="b1", provider="duckduckgo"),
            SearchResult(title="B", url="u2", body="b2", provider="duckduckgo"),
        ]

        async def _fake(*args: object, **kwargs: object) -> list[SearchResult]:
            return fake_results

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _fake)

        out = await fdisp_search_web({"query": "x"})

        assert out.startswith("[Search: 2 results via duckduckgo]\n\n")
        assert "[1] A" in out
        assert "[2] B" in out


class TestFdispBrowserFetch:
    async def test_formats_success_result(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_result = BrowserFetchResponse(
            text="Hello world",
            truncated=False,
            url="https://example.com/",
            status_code=200,
            elapsed_sec=0.1,
        )

        async def _fake(args: dict[str, object]) -> BrowserFetchResponse:
            return mock_result

        monkeypatch.setattr("mcp_servers.web_search.service.fetch_browser", _fake)

        out = await fdisp_browser_fetch({"url": "https://example.com/"})

        assert "status_code=200" in out
        assert "Hello world" in out
        assert "[RESPONSE TRUNCATED]" not in out

    async def test_formats_truncated_result(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_result = BrowserFetchResponse(
            text="a" * 100,
            truncated=True,
            url="https://example.com/",
            status_code=200,
            elapsed_sec=0.2,
        )

        async def _fake(args: dict[str, object]) -> BrowserFetchResponse:
            return mock_result

        monkeypatch.setattr("mcp_servers.web_search.service.fetch_browser", _fake)

        out = await fdisp_browser_fetch({"url": "https://example.com/"})

        assert "[RESPONSE TRUNCATED]" in out


class TestDispatchWebToolBrowserFetch:
    async def test_dispatch_routes_browser_fetch(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        mock_result = BrowserFetchResponse(
            text="ok",
            truncated=False,
            url="https://example.com/",
            status_code=200,
            elapsed_sec=0.1,
        )

        async def _fake(args: dict[str, object]) -> BrowserFetchResponse:
            return mock_result

        monkeypatch.setattr("mcp_servers.web_search.service.fetch_browser", _fake)

        result = await dispatch_web_tool(
            "browser_fetch", {"url": "https://example.com/"}
        )

        assert result.outcome == "ok"
        assert "ok" in result.output
