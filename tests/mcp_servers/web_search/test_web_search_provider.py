"""tests/test_web_search_provider.py

Unit tests for `search_duckduckgo()` covering the timeout/error-classification/
result-validation paths added for web-search-mcp's provider execution semantics.
No real network calls — `DDGS` is monkeypatched per test.
"""

from __future__ import annotations

import time
from typing import Any

import httpx
import pytest
import respx
from mcp_servers.web_search.search_provider import (
    _check_domain,
    _extract_text,
    _truncate,
    fetch_browser,
    search_duckduckgo,
)
from mcp_servers.web_search.web_search_models import (
    BrowserAuthorizationError,
    BrowserConfig,
    BrowserFetchRequest,
    BrowserValidationError,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchProviderError,
    WebSearchTimeoutError,
)


def _make_browser_config(
    *,
    allowed_domains: list[str] | None = None,
    max_response_kb: int = 256,
    timeout_sec: int = 15,
) -> BrowserConfig:
    return BrowserConfig(
        allowed_domains=list(allowed_domains) if allowed_domains is not None else [],
        max_response_kb=max_response_kb,
        timeout_sec=timeout_sec,
        auth_token="",
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


# ── _check_domain (ported from browser-mcp's BrowserService._check_domain) ────


class TestCheckDomain:
    def test_allowed_domain_passes(self) -> None:
        result = _check_domain("https://example.com/page", {"example.com"})
        assert result == "example.com"

    def test_disallowed_domain_raises_403(self) -> None:
        with pytest.raises(BrowserAuthorizationError):
            _check_domain("https://evil.example/", {"example.com"})

    def test_empty_allowlist_denies_all(self) -> None:
        with pytest.raises(BrowserAuthorizationError):
            _check_domain("https://example.com/", set())

    def test_loopback_ip_rejected_even_if_allowlisted(self) -> None:
        # Simulated misconfiguration: 127.0.0.1 present in the allowlist itself.
        with pytest.raises(BrowserAuthorizationError):
            _check_domain("http://127.0.0.1/", {"127.0.0.1"})

    def test_link_local_metadata_ip_rejected(self) -> None:
        # 169.254.169.254 is the canonical AWS/GCP cloud-metadata SSRF target.
        with pytest.raises(BrowserAuthorizationError):
            _check_domain("http://169.254.169.254/", {"169.254.169.254"})

    def test_private_range_ip_rejected(self) -> None:
        with pytest.raises(BrowserAuthorizationError):
            _check_domain("http://10.0.0.1/", {"10.0.0.1"})

    def test_bad_scheme_raises_validation_error(self) -> None:
        with pytest.raises(BrowserValidationError):
            _check_domain("ftp://example.com/", {"example.com"})

    def test_missing_hostname_raises_validation_error(self) -> None:
        with pytest.raises(BrowserValidationError):
            _check_domain("http:///path", {"example.com"})


# ── _truncate (ported from browser-mcp's BrowserService._truncate) ────────────


class TestTruncate:
    def test_under_limit_returns_unmodified(self) -> None:
        text = "hello world"
        result, truncated = _truncate(text, max_kb=256)
        assert result == text
        assert truncated is False

    def test_over_limit_truncates_with_flag(self) -> None:
        text = "A" * 4096
        result, truncated = _truncate(text, max_kb=1)
        assert truncated is True
        assert len(result.encode("utf-8")) <= 1024


# ── _extract_text (ported from browser-mcp's BrowserService._extract_text) ────


class TestExtractText:
    def test_strips_script_and_style_tags(self) -> None:
        html = (
            "<html><head><style>body { color: red; }</style></head>"
            "<body><script>alert('evil')</script><p>Visible paragraph text</p></body>"
            "</html>"
        )
        result = _extract_text(html)
        assert "Visible paragraph text" in result
        assert "alert" not in result
        assert "color: red" not in result


# ── fetch_browser (ported from browser-mcp's BrowserService.fetch) ────────────


class TestFetchBrowser:
    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_returns_extracted_text(self) -> None:
        respx.get("https://example.com/page").mock(
            return_value=httpx.Response(
                200, html="<html><body><p>Hello</p></body></html>"
            )
        )
        cfg = _make_browser_config(allowed_domains=["example.com"])
        req = BrowserFetchRequest(url="https://example.com/page")
        resp = await fetch_browser(req, cfg)
        assert "Hello" in resp.text
        assert resp.status_code == 200
        assert resp.truncated is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_disallowed_domain_raises_before_network_call(self) -> None:
        route = respx.get("https://evil.example/").mock(
            return_value=httpx.Response(200, html="<html></html>")
        )
        cfg = _make_browser_config(allowed_domains=["example.com"])
        req = BrowserFetchRequest(url="https://evil.example/")
        with pytest.raises(BrowserAuthorizationError):
            await fetch_browser(req, cfg)
        assert route.called is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_non_2xx_response_passthrough(self) -> None:
        # No raise_for_status is performed at the provider layer; the status
        # code and whatever body text exists are passed through unmodified,
        # letting the caller/LLM decide how to interpret it.
        respx.get("https://example.com/missing").mock(
            return_value=httpx.Response(
                404, html="<html><body><p>Not Found</p></body></html>"
            )
        )
        cfg = _make_browser_config(allowed_domains=["example.com"])
        req = BrowserFetchRequest(url="https://example.com/missing")
        resp = await fetch_browser(req, cfg)
        assert resp.status_code == 404
        assert "Not Found" in resp.text

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_timeout_propagates_raw_httpx_exception(self) -> None:
        # fetch_browser() intentionally does not catch httpx errors — per the
        # search_provider.py implementation doc, httpx.HTTPError subclasses
        # propagate unhandled up to service.py, which classifies them as
        # "fetch_error" (see test_web_search_service.py).
        respx.get("https://example.com/slow").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        cfg = _make_browser_config(allowed_domains=["example.com"])
        req = BrowserFetchRequest(url="https://example.com/slow")
        with pytest.raises(httpx.TimeoutException):
            await fetch_browser(req, cfg)

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_clamps_caller_max_response_kb_to_server_max(self) -> None:
        respx.get("https://example.com/big").mock(
            return_value=httpx.Response(
                200, html=f"<html><body><p>{'A' * 4096}</p></body></html>"
            )
        )
        cfg = _make_browser_config(allowed_domains=["example.com"], max_response_kb=1)
        # Caller asks for far more than the server allows; result is clamped.
        req = BrowserFetchRequest(url="https://example.com/big", max_response_kb=999)
        resp = await fetch_browser(req, cfg)
        assert resp.truncated is True
        assert len(resp.text.encode("utf-8")) <= 1024
