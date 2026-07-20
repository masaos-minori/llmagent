"""tests/test_web_search_provider.py

Unit tests for `search_duckduckgo()` covering the timeout/error-classification/
result-validation paths added for web-search-mcp's provider execution semantics.
No real network calls — `DDGS` is monkeypatched per test.
"""

from __future__ import annotations

import time
from typing import Any

import pytest
from mcp_servers.web_search.search_provider import search_duckduckgo
from mcp_servers.web_search.web_search_models import (
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchProviderError,
    WebSearchTimeoutError,
)


class _FakeDDGS:
    """Fake DDGS context manager whose .text() behavior is injected per test."""

    def __init__(self, text_fn: Any) -> None:
        self._text_fn = text_fn

    def __enter__(self) -> _FakeDDGS:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def text(self, query: str, max_results: int) -> list[dict[str, str]]:
        return self._text_fn(query, max_results)


def _install_fake_ddgs(monkeypatch: pytest.MonkeyPatch, text_fn: Any) -> None:
    monkeypatch.setattr(
        "mcp_servers.web_search.search_provider.DDGS",
        lambda: _FakeDDGS(text_fn),
    )


class TestSearchDuckDuckGo:
    async def test_one_result(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _install_fake_ddgs(
            monkeypatch,
            lambda q, max_results: [{"title": "t", "href": "u", "body": "b"}],
        )

        results = await search_duckduckgo("query", 5, 10.0)

        assert len(results) == 1
        assert results[0].title == "t"
        assert results[0].url == "u"
        assert results[0].body == "b"
        assert results[0].provider == "duckduckgo"

    async def test_empty_results_no_exception(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_fake_ddgs(monkeypatch, lambda q, max_results: [])

        results = await search_duckduckgo("query", 5, 10.0)

        assert results == []

    async def test_timeout_raises_timeout_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _slow(q: str, max_results: int) -> list[dict[str, str]]:
            time.sleep(0.2)
            return []

        _install_fake_ddgs(monkeypatch, _slow)

        with pytest.raises(WebSearchTimeoutError):
            await search_duckduckgo("query", 5, 0.01)

    async def test_runtime_error_raises_network_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _boom(q: str, max_results: int) -> list[dict[str, str]]:
            raise RuntimeError("boom")

        _install_fake_ddgs(monkeypatch, _boom)

        with pytest.raises(WebSearchNetworkError):
            await search_duckduckgo("query", 5, 10.0)

    async def test_os_error_raises_network_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _boom(q: str, max_results: int) -> list[dict[str, str]]:
            raise OSError("network unreachable")

        _install_fake_ddgs(monkeypatch, _boom)

        with pytest.raises(WebSearchNetworkError):
            await search_duckduckgo("query", 5, 10.0)

    async def test_generic_exception_raises_provider_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _boom(q: str, max_results: int) -> list[dict[str, str]]:
            raise ValueError("unexpected DDGS failure")

        _install_fake_ddgs(monkeypatch, _boom)

        with pytest.raises(WebSearchProviderError):
            await search_duckduckgo("query", 5, 10.0)

    async def test_malformed_item_raises_parse_error(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _install_fake_ddgs(
            monkeypatch,
            lambda q, max_results: [
                {"title": "ok", "href": "u", "body": "b"},
                "not-a-dict",
            ],
        )

        with pytest.raises(WebSearchParseError):
            await search_duckduckgo("query", 5, 10.0)
