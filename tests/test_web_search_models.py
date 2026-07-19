"""
tests/test_web_search_models.py
Unit tests for mcp/web_search/models.py.
"""

from __future__ import annotations

import importlib

import pytest
from mcp_servers.web_search.web_search_models import (
    DEFAULT_MAX_RESULTS,
    MAX_RESULTS_LIMIT,
    SearchRequest,
    SearchResponse,
    SearchResult,
    WebSearchConfig,
    WebSearchUpstreamError,
)
from pydantic import ValidationError


class TestWebSearchConfig:
    def test_defaults(self) -> None:
        cfg = WebSearchConfig()
        assert cfg.default_max_results == DEFAULT_MAX_RESULTS
        assert cfg.max_results_limit == MAX_RESULTS_LIMIT

    def test_from_dict_defaults(self) -> None:
        cfg = WebSearchConfig.from_dict({})
        assert cfg.default_max_results == DEFAULT_MAX_RESULTS

    def test_from_dict_custom(self) -> None:
        cfg = WebSearchConfig.from_dict(
            {
                "default_max_results": 10,
                "max_results_limit": 15,
            }
        )
        assert cfg.default_max_results == 10
        assert cfg.max_results_limit == 15

    def test_from_dict_type_coercion(self) -> None:
        cfg = WebSearchConfig.from_dict({"default_max_results": "7"})
        assert cfg.default_max_results == 7


class TestWebSearchUpstreamError:
    def test_is_runtime_error(self) -> None:
        err = WebSearchUpstreamError("all providers failed")
        assert isinstance(err, RuntimeError)
        assert "all providers failed" in str(err)


class TestSearchRequest:
    def test_valid_request(self) -> None:
        req = SearchRequest(query="python testing")
        assert req.query == "python testing"
        assert req.max_results == DEFAULT_MAX_RESULTS

    def test_custom_max_results(self) -> None:
        req = SearchRequest(query="pytest", max_results=10)
        assert req.max_results == 10

    def test_query_too_short_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="")

    def test_query_too_long_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="x" * 501)

    def test_max_results_below_min_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="test", max_results=0)

    def test_max_results_above_limit_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="test", max_results=MAX_RESULTS_LIMIT + 1)

    def test_max_results_at_limit_ok(self) -> None:
        req = SearchRequest(query="test", max_results=MAX_RESULTS_LIMIT)
        assert req.max_results == MAX_RESULTS_LIMIT


class TestSearchRequestBoundsWiredToConfig:
    """SearchRequest's Field bounds are sourced from WebSearchConfig.load() at
    module-import time (models.py's module-level _cfg), not hardcoded
    constants. WebSearchConfig.load() is redefined per module-reload, so the
    monkeypatch targets ConfigLoader.load() (what it delegates to) instead —
    that patch survives the reload of mcp_servers.web_search.models."""

    def test_bounds_reflect_monkeypatched_config(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import mcp_servers.web_search.web_search_models as models_mod
        from shared.config_loader import ConfigLoader

        monkeypatch.setattr(
            ConfigLoader,
            "load",
            lambda self, name: {"default_max_results": 7, "max_results_limit": 9},
        )
        try:
            reloaded = importlib.reload(models_mod)
            assert reloaded._cfg.default_max_results == 7
            assert reloaded._cfg.max_results_limit == 9

            req_default = reloaded.SearchRequest(query="test")
            assert req_default.max_results == 7

            req_at_limit = reloaded.SearchRequest(query="test", max_results=9)
            assert req_at_limit.max_results == 9

            with pytest.raises(ValidationError):
                reloaded.SearchRequest(query="test", max_results=10)
        finally:
            # Restore the real config-backed module state for subsequent tests.
            importlib.reload(models_mod)


class TestSearchResult:
    def test_fields(self) -> None:
        result = SearchResult(
            title="Python Docs",
            url="https://docs.python.org",
            body="Official Python documentation",
            provider="duckduckgo",
        )
        assert result.title == "Python Docs"
        assert result.url == "https://docs.python.org"
        assert result.body == "Official Python documentation"
        assert result.provider == "duckduckgo"


class TestSearchResponse:
    def test_fields(self) -> None:
        results = [
            SearchResult(title="r1", url="u1", body="b1", provider="ddg"),
        ]
        resp = SearchResponse(query="python", results=results, provider="duckduckgo")
        assert resp.query == "python"
        assert len(resp.results) == 1
        assert resp.provider == "duckduckgo"

    def test_empty_results(self) -> None:
        resp = SearchResponse(query="x", results=[], provider="brave")
        assert resp.results == []
