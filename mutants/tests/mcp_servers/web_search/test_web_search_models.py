"""
tests/test_web_search_models.py
Unit tests for mcp/web_search/models.py.
"""

from __future__ import annotations

import importlib

import pytest
from mcp_servers.web_search.web_search_models import (
    DEFAULT_MAX_RESULTS,
    HARD_MAX_RESULTS_LIMIT,
    HARD_SEARCH_TIMEOUT_SEC_LIMIT,
    MAX_RESULTS_LIMIT,
    BrowserAuthorizationError,
    BrowserConfig,
    BrowserFetchRequest,
    BrowserFetchResponse,
    BrowserValidationError,
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

    def test_from_dict_default_max_results_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="default_max_results"):
            WebSearchConfig.from_dict({"default_max_results": 0})

    def test_from_dict_max_results_limit_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="max_results_limit"):
            WebSearchConfig.from_dict({"max_results_limit": 0})

    def test_from_dict_default_exceeds_limit_raises(self) -> None:
        with pytest.raises(ValueError, match="must not exceed"):
            WebSearchConfig.from_dict(
                {"default_max_results": 20, "max_results_limit": 10}
            )

    def test_from_dict_limit_exceeds_hard_max_raises(self) -> None:
        with pytest.raises(ValueError, match="HARD_MAX_RESULTS_LIMIT"):
            WebSearchConfig.from_dict({"max_results_limit": HARD_MAX_RESULTS_LIMIT + 1})

    def test_from_dict_search_timeout_sec_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="search_timeout_sec"):
            WebSearchConfig.from_dict({"search_timeout_sec": 0})

    def test_from_dict_search_timeout_sec_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="search_timeout_sec"):
            WebSearchConfig.from_dict({"search_timeout_sec": -1.0})

    def test_from_dict_search_timeout_sec_exceeds_hard_limit_raises(self) -> None:
        with pytest.raises(ValueError, match="search_timeout_sec"):
            WebSearchConfig.from_dict(
                {"search_timeout_sec": HARD_SEARCH_TIMEOUT_SEC_LIMIT + 1}
            )

    def test_from_dict_search_timeout_sec_default(self) -> None:
        cfg = WebSearchConfig.from_dict({})
        assert cfg.search_timeout_sec == 10.0

    def test_from_dict_search_timeout_sec_at_hard_limit_ok(self) -> None:
        cfg = WebSearchConfig.from_dict(
            {"search_timeout_sec": HARD_SEARCH_TIMEOUT_SEC_LIMIT}
        )
        assert cfg.search_timeout_sec == HARD_SEARCH_TIMEOUT_SEC_LIMIT


class TestWebSearchUpstreamError:
    def test_is_runtime_error(self) -> None:
        err = WebSearchUpstreamError("all providers failed")
        assert isinstance(err, RuntimeError)
        assert "all providers failed" in str(err)


class TestBrowserExceptions:
    def test_browser_authorization_error_is_runtime_error(self) -> None:
        err = BrowserAuthorizationError("domain not allowed")
        assert isinstance(err, RuntimeError)
        assert "domain not allowed" in str(err)

    def test_browser_validation_error_is_value_error(self) -> None:
        err = BrowserValidationError("bad url")
        assert isinstance(err, ValueError)
        assert "bad url" in str(err)

    def test_browser_errors_are_not_web_search_upstream_error(self) -> None:
        """Per the plan's Design section, the two error hierarchies coexist
        independently — a BrowserAuthorizationError must not also be a
        WebSearchUpstreamError."""
        assert not isinstance(BrowserAuthorizationError("x"), WebSearchUpstreamError)
        assert not isinstance(BrowserValidationError("x"), WebSearchUpstreamError)


class TestWebSearchConfigBrowserFields:
    def test_defaults(self) -> None:
        cfg = WebSearchConfig()
        assert cfg.browser_allowed_domains == []
        assert cfg.browser_max_response_kb == 256
        assert cfg.browser_timeout_sec == 15
        assert cfg.browser_auth_token == ""

    def test_from_dict_defaults(self) -> None:
        cfg = WebSearchConfig.from_dict({})
        assert cfg.browser_allowed_domains == []
        assert cfg.browser_max_response_kb == 256
        assert cfg.browser_timeout_sec == 15
        assert cfg.browser_auth_token == ""

    def test_from_dict_custom(self) -> None:
        cfg = WebSearchConfig.from_dict(
            {
                "browser_allowed_domains": ["example.com"],
                "browser_max_response_kb": 512,
                "browser_timeout_sec": 30,
                "browser_auth_token": "secret",
            }
        )
        assert cfg.browser_allowed_domains == ["example.com"]
        assert cfg.browser_max_response_kb == 512
        assert cfg.browser_timeout_sec == 30
        assert cfg.browser_auth_token == "secret"

    def test_from_dict_none_values_use_defaults(self) -> None:
        """Uses `or` for defaults so a present-but-null TOML key does not
        raise (int(None)) or stringify to "None" (str(None))."""
        cfg = WebSearchConfig.from_dict(
            {
                "browser_allowed_domains": None,
                "browser_max_response_kb": None,
                "browser_timeout_sec": None,
                "browser_auth_token": None,
            }
        )
        assert cfg.browser_allowed_domains == []
        assert cfg.browser_max_response_kb == 256
        assert cfg.browser_timeout_sec == 15
        assert cfg.browser_auth_token == ""


class TestBrowserConfig:
    def test_from_web_search_config_projects_fields(self) -> None:
        cfg = WebSearchConfig.from_dict(
            {
                "browser_allowed_domains": ["example.com", "docs.python.org"],
                "browser_max_response_kb": 128,
                "browser_timeout_sec": 5,
                "browser_auth_token": "tok",
            }
        )
        browser_cfg = BrowserConfig.from_web_search_config(cfg)
        assert browser_cfg.allowed_domains == ["example.com", "docs.python.org"]
        assert browser_cfg.max_response_kb == 128
        assert browser_cfg.timeout_sec == 5
        assert browser_cfg.auth_token == "tok"


class TestBrowserFetchRequest:
    def test_valid_request_defaults(self) -> None:
        req = BrowserFetchRequest(url="https://example.com/")
        assert req.url == "https://example.com/"
        assert req.max_response_kb is None

    def test_max_response_kb_override(self) -> None:
        req = BrowserFetchRequest(url="https://example.com/", max_response_kb=100)
        assert req.max_response_kb == 100

    def test_max_response_kb_below_min_raises(self) -> None:
        with pytest.raises(ValidationError):
            BrowserFetchRequest(url="https://example.com/", max_response_kb=0)

    def test_max_response_kb_above_max_raises(self) -> None:
        with pytest.raises(ValidationError):
            BrowserFetchRequest(url="https://example.com/", max_response_kb=65537)


class TestBrowserFetchResponse:
    def test_fields(self) -> None:
        resp = BrowserFetchResponse(
            text="hello",
            truncated=False,
            url="https://example.com/",
            status_code=200,
            elapsed_sec=0.5,
        )
        assert resp.text == "hello"
        assert resp.truncated is False
        assert resp.url == "https://example.com/"
        assert resp.status_code == 200
        assert resp.elapsed_sec == 0.5


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

    def test_query_whitespace_only_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="   ")

    def test_query_trims_leading_trailing_whitespace(self) -> None:
        req = SearchRequest(query="  hello  ")
        assert req.query == "hello"

    def test_query_nul_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="hello\x00world")

    def test_query_control_char_raises(self) -> None:
        with pytest.raises(ValidationError):
            SearchRequest(query="hello\nworld")


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
