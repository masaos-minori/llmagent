"""tests/test_web_search_provider.py

Unit tests for `search_duckduckgo()` covering the timeout/error-classification/
result-validation paths added for web-search-mcp's provider execution semantics.
No real network calls — `DDGS` is monkeypatched per test.
"""

from __future__ import annotations

import time
from collections.abc import AsyncIterator, Sequence
from typing import Any

import httpx
import pytest
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
    BrowserHttpStatusError,
    BrowserUnsupportedContentError,
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

    @pytest.mark.parametrize(
        "url",
        [
            "https://EXAMPLE.com/",
            "https://Example.COM/page",
            "https://example.com./",
            "https://example.com:8443/",
        ],
    )
    def test_url_host_is_matched_on_its_normalized_form(self, url: str) -> None:
        assert _check_domain(url, {"example.com"}) == "example.com"

    @pytest.mark.parametrize("entry", ["Example.COM", "example.com.", "EXAMPLE.com."])
    def test_a_raw_allowlist_member_is_matched_on_its_normalized_form(
        self, entry: str
    ) -> None:
        assert _check_domain("https://example.com/", {entry}) == "example.com"

    def test_idna_u_label_and_a_label_match_each_other(self) -> None:
        assert _check_domain("https://例え.jp/", {"xn--r8jz45g.jp"}) == "xn--r8jz45g.jp"
        assert _check_domain("https://xn--r8jz45g.jp/", {"例え.jp"}) == "xn--r8jz45g.jp"

    def test_a_different_host_never_matches_after_normalization(self) -> None:
        with pytest.raises(BrowserAuthorizationError):
            _check_domain("https://example.com.evil.example/", {"example.com"})

    def test_an_invalid_url_host_is_a_validation_error(self) -> None:
        with pytest.raises(BrowserValidationError):
            _check_domain("https://exa_mple.com/", {"example.com"})

    def test_an_invalid_allowlist_member_never_matches(self) -> None:
        with pytest.raises(BrowserAuthorizationError):
            _check_domain("https://example.com/", {"https://example.com", "bad host"})

    def test_ipv6_loopback_literal_is_still_an_authorization_error(self) -> None:
        with pytest.raises(BrowserAuthorizationError):
            _check_domain("http://[::1]/", {"example.com"})


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

_PUBLIC = "93.184.216.34"
_HTML = {"content-type": "text/html; charset=utf-8"}


class _AsyncStream(httpx.AsyncByteStream):
    def __init__(self, source: AsyncIterator[bytes]) -> None:
        self._source = source

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self._source:
            yield chunk


def _response(
    status: int, body: bytes = b"", headers: dict[str, str] | None = None
) -> httpx.Response:
    async def _one() -> AsyncIterator[bytes]:
        if body:
            yield body

    return httpx.Response(status, stream=_AsyncStream(_one()), headers=headers)


def _resolver(*answers: str):
    async def _resolve(host: str, port: int) -> Sequence[str]:
        return list(answers) or [_PUBLIC]

    return _resolve


class _Net:
    """Injected transport and resolver; records every request that is sent."""

    def __init__(self, handler, *answers: str) -> None:
        self.requests: list[httpx.Request] = []
        self._handler = handler
        self.resolver = _resolver(*answers)

    @property
    def transport(self) -> httpx.MockTransport:
        async def _call(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return await self._handler(request)

        return httpx.MockTransport(_call)


def _html(body: str = "<html><body><p>Hello</p></body></html>"):
    async def _handler(request: httpx.Request) -> httpx.Response:
        return _response(200, body.encode(), _HTML)

    return _handler


async def _fetch(
    url: str,
    net: _Net,
    *,
    allowed: list[str] | None = None,
    max_response_kb: int = 256,
    caller_kb: int | None = None,
):
    cfg = _make_browser_config(
        allowed_domains=allowed or ["example.com"], max_response_kb=max_response_kb
    )
    req = BrowserFetchRequest(url=url, max_response_kb=caller_kb)
    return await fetch_browser(req, cfg, resolver=net.resolver, transport=net.transport)


class TestFetchBrowser:
    @pytest.mark.asyncio
    async def test_fetch_returns_extracted_text(self) -> None:
        resp = await _fetch("https://example.com/page", _Net(_html()))
        assert "Hello" in resp.text
        assert resp.status_code == 200
        assert resp.truncated is False
        assert resp.download_truncated is False
        assert resp.content_type == "text/html"

    @pytest.mark.asyncio
    async def test_fetch_disallowed_domain_raises_before_network_call(self) -> None:
        net = _Net(_html())
        with pytest.raises(BrowserAuthorizationError):
            await _fetch("https://evil.example/", net)
        assert net.requests == []

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("status", "category"),
        [
            (403, "client_error"),
            (404, "client_error"),
            (429, "rate_limited"),
            (500, "server_error"),
            (503, "server_error"),
        ],
    )
    async def test_fetch_non_2xx_raises_and_returns_no_body(
        self, status: int, category: str
    ) -> None:
        async def _handler(request: httpx.Request) -> httpx.Response:
            return _response(status, b"<html><body>Not Found</body></html>", _HTML)

        with pytest.raises(BrowserHttpStatusError) as excinfo:
            await _fetch("https://example.com/missing", _Net(_handler))
        assert excinfo.value.status_code == status
        assert excinfo.value.category == category
        assert "Not Found" not in str(excinfo.value)

    @pytest.mark.asyncio
    async def test_fetch_redirect_without_location_is_a_status_error(self) -> None:
        async def _handler(request: httpx.Request) -> httpx.Response:
            return _response(301)

        with pytest.raises(BrowserHttpStatusError) as excinfo:
            await _fetch("https://example.com/", _Net(_handler))
        assert excinfo.value.category == "redirect"

    @pytest.mark.asyncio
    async def test_fetch_timeout_propagates_raw_httpx_exception(self) -> None:
        async def _handler(request: httpx.Request) -> httpx.Response:
            raise httpx.TimeoutException("timed out")

        with pytest.raises(httpx.TimeoutException):
            await _fetch("https://example.com/slow", _Net(_handler))

    @pytest.mark.asyncio
    async def test_fetch_clamps_caller_max_response_kb_to_server_max(self) -> None:
        resp = await _fetch(
            "https://example.com/big",
            _Net(_html(f"<html><body><p>{'A' * 4096}</p></body></html>")),
            max_response_kb=1,
            caller_kb=999,
        )
        assert resp.truncated is True
        assert resp.download_truncated is False
        assert len(resp.text.encode("utf-8")) <= 1024

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "answers",
        [
            ("127.0.0.1",),
            ("10.0.0.5",),
            ("169.254.169.254",),
            ("::ffff:10.0.0.5",),
            (_PUBLIC, "10.0.0.5"),
        ],
    )
    async def test_fetch_rejects_a_prohibited_resolved_address(
        self, answers: tuple[str, ...]
    ) -> None:
        net = _Net(_html(), *answers)
        with pytest.raises(BrowserAuthorizationError):
            await _fetch("https://example.com/", net)
        assert net.requests == []

    @pytest.mark.asyncio
    async def test_fetch_resolution_failure_is_a_network_error(self) -> None:
        net = _Net(_html())

        async def _fail(host: str, port: int) -> Sequence[str]:
            raise OSError("no such host")

        net.resolver = _fail
        with pytest.raises(WebSearchNetworkError):
            await _fetch("https://example.com/", net)

    @pytest.mark.asyncio
    async def test_fetch_follows_a_redirect_inside_the_allowlist(self) -> None:
        async def _handler(request: httpx.Request) -> httpx.Response:
            if request.headers["host"] == "example.com":
                return _response(302, headers={"location": "https://docs.example.com/"})
            return _response(200, b"<html><body>docs</body></html>", _HTML)

        resp = await _fetch(
            "https://example.com/",
            _Net(_handler),
            allowed=["example.com", "docs.example.com"],
        )
        assert "docs" in resp.text

    @pytest.mark.asyncio
    async def test_fetch_rejects_a_redirect_outside_the_allowlist(self) -> None:
        async def _handler(request: httpx.Request) -> httpx.Response:
            return _response(302, headers={"location": "https://evil.example/"})

        with pytest.raises(BrowserAuthorizationError):
            await _fetch("https://example.com/", _Net(_handler))

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "media", ["application/pdf", "image/png", "application/zip"]
    )
    async def test_fetch_rejects_binary_types_before_the_parser(
        self, media: str, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _fail(html: str) -> str:
            raise AssertionError("the parser must not run")

        monkeypatch.setattr(
            "mcp_servers.web_search.search_provider._extract_text", _fail
        )

        async def _handler(request: httpx.Request) -> httpx.Response:
            return _response(200, b"%PDF-1.4", {"content-type": media})

        with pytest.raises(BrowserUnsupportedContentError) as excinfo:
            await _fetch("https://example.com/", _Net(_handler))
        assert excinfo.value.content_type == media

    @pytest.mark.asyncio
    async def test_fetch_rejects_a_missing_content_type(self) -> None:
        async def _handler(request: httpx.Request) -> httpx.Response:
            return _response(200, b"data")

        with pytest.raises(BrowserUnsupportedContentError):
            await _fetch("https://example.com/", _Net(_handler))

    @pytest.mark.asyncio
    async def test_fetch_returns_text_plain_without_the_html_parser(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        def _fail(html: str) -> str:
            raise AssertionError("the parser must not run for text/plain")

        monkeypatch.setattr(
            "mcp_servers.web_search.search_provider._extract_text", _fail
        )

        async def _handler(request: httpx.Request) -> httpx.Response:
            return _response(200, b"  plain text  ", {"content-type": "text/plain"})

        resp = await _fetch("https://example.com/", _Net(_handler))
        assert resp.text == "plain text"
        assert resp.content_type == "text/plain"

    @pytest.mark.asyncio
    async def test_download_truncation_is_reported_separately_from_text_truncation(
        self,
    ) -> None:
        big = b"<html><body><p>" + b"x" * (3 * 1024 * 1024) + b"</p></body></html>"

        async def _handler(request: httpx.Request) -> httpx.Response:
            return _response(200, big, _HTML)

        resp = await _fetch("https://example.com/", _Net(_handler))
        assert resp.download_truncated is True
        assert resp.truncated is True
