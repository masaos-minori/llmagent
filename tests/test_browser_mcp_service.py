"""
tests/test_browser_mcp_service.py
Unit tests for BrowserService guard methods and dispatch handler:
  - _check_domain: domain allowlist allow/deny, IP-literal/loopback rejection
  - _truncate: byte-based size truncation with flag
  - _extract_text: HTML -> visible text extraction
  - fetch: respx-mocked HTTP GET, error propagation
  - build_service: empty-allowlist warning
  - fmt_fetch: dispatch-handler plain-text formatting
"""

from __future__ import annotations

import logging

import httpx
import pytest
import respx
from mcp_servers.browser.browser_models import (
    BrowserAuthorizationError,
    BrowserConfig,
    BrowserFetchRequest,
    BrowserFetchResponse,
)
from mcp_servers.browser.browser_service import BrowserService, build_service

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_config(
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


def _make_service(
    *,
    allowed_domains: list[str] | None = None,
    max_response_kb: int = 256,
    timeout_sec: int = 15,
) -> BrowserService:
    """Create a minimal BrowserService for testing; no real network calls are made."""
    return BrowserService(
        _make_config(
            allowed_domains=allowed_domains,
            max_response_kb=max_response_kb,
            timeout_sec=timeout_sec,
        )
    )


# ── _check_domain ─────────────────────────────────────────────────────────────


class TestCheckDomain:
    def test_allowed_domain_passes(self) -> None:
        svc = _make_service(allowed_domains=["example.com"])
        result = svc._check_domain("https://example.com/page")
        assert result == "example.com"

    def test_disallowed_domain_raises_403(self) -> None:
        svc = _make_service(allowed_domains=["example.com"])
        with pytest.raises(BrowserAuthorizationError):
            svc._check_domain("https://evil.example/")

    def test_empty_allowlist_denies_all(self) -> None:
        svc = _make_service()  # default: allowed_domains=[]
        with pytest.raises(BrowserAuthorizationError):
            svc._check_domain("https://example.com/")

    def test_loopback_ip_rejected_even_if_allowlisted(self) -> None:
        # Simulated misconfiguration: 127.0.0.1 present in the allowlist itself.
        svc = _make_service(allowed_domains=["127.0.0.1"])
        with pytest.raises(BrowserAuthorizationError):
            svc._check_domain("http://127.0.0.1/")

    def test_link_local_metadata_ip_rejected(self) -> None:
        # 169.254.169.254 is the canonical AWS/GCP cloud-metadata SSRF target.
        svc = _make_service(allowed_domains=["169.254.169.254"])
        with pytest.raises(BrowserAuthorizationError):
            svc._check_domain("http://169.254.169.254/")

    def test_private_range_ip_rejected(self) -> None:
        svc = _make_service(allowed_domains=["10.0.0.1"])
        with pytest.raises(BrowserAuthorizationError):
            svc._check_domain("http://10.0.0.1/")


# ── _truncate ──────────────────────────────────────────────────────────────────


class TestTruncate:
    def test_under_limit_returns_unmodified(self) -> None:
        svc = _make_service()
        text = "hello world"
        result, truncated = svc._truncate(text, max_kb=256)
        assert result == text
        assert truncated is False

    def test_over_limit_truncates_with_flag(self) -> None:
        svc = _make_service()
        text = "A" * 4096
        result, truncated = svc._truncate(text, max_kb=1)
        assert truncated is True
        assert len(result.encode("utf-8")) <= 1024


# ── _extract_text ──────────────────────────────────────────────────────────────


class TestExtractText:
    def test_strips_script_and_style_tags(self) -> None:
        svc = _make_service()
        html = (
            "<html><head><style>body { color: red; }</style></head>"
            "<body><script>alert('evil')</script><p>Visible paragraph text</p></body>"
            "</html>"
        )
        result = svc._extract_text(html)
        assert "Visible paragraph text" in result
        assert "alert" not in result
        assert "color: red" not in result


# ── fetch ──────────────────────────────────────────────────────────────────────


class TestFetch:
    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_returns_extracted_text(self) -> None:
        respx.get("https://example.com/page").mock(
            return_value=httpx.Response(
                200, html="<html><body><p>Hello</p></body></html>"
            )
        )
        svc = _make_service(allowed_domains=["example.com"])
        req = BrowserFetchRequest(url="https://example.com/page")
        resp = await svc.fetch(req)
        assert "Hello" in resp.text
        assert resp.status_code == 200
        assert resp.truncated is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_disallowed_domain_raises_before_network_call(self) -> None:
        route = respx.get("https://evil.example/").mock(
            return_value=httpx.Response(200, html="<html></html>")
        )
        svc = _make_service(allowed_domains=["example.com"])
        req = BrowserFetchRequest(url="https://evil.example/")
        with pytest.raises(BrowserAuthorizationError):
            await svc.fetch(req)
        assert route.called is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_non_2xx_response_passthrough(self) -> None:
        # No raise_for_status is performed at the service layer; the status
        # code and whatever body text exists are passed through unmodified,
        # letting the caller/LLM decide how to interpret it.
        respx.get("https://example.com/missing").mock(
            return_value=httpx.Response(
                404, html="<html><body><p>Not Found</p></body></html>"
            )
        )
        svc = _make_service(allowed_domains=["example.com"])
        req = BrowserFetchRequest(url="https://example.com/missing")
        resp = await svc.fetch(req)
        assert resp.status_code == 404
        assert "Not Found" in resp.text

    @pytest.mark.asyncio
    @respx.mock
    async def test_fetch_timeout_propagates_raw_httpx_exception(self) -> None:
        # BrowserService.fetch() intentionally does not catch httpx errors —
        # per the service.py implementation doc, httpx.HTTPError subclasses
        # propagate unhandled to server.py, which registers no handler for
        # them either (only BrowserAuthorizationError/BrowserValidationError
        # have exception_handlers in server.py), so a raw httpx exception is
        # the correct, current behavior at this layer.
        respx.get("https://example.com/slow").mock(
            side_effect=httpx.TimeoutException("timed out")
        )
        svc = _make_service(allowed_domains=["example.com"])
        req = BrowserFetchRequest(url="https://example.com/slow")
        with pytest.raises(httpx.TimeoutException):
            await svc.fetch(req)


# ── build_service ──────────────────────────────────────────────────────────────


class TestBuildService:
    def test_empty_allowed_domains_logs_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        cfg = _make_config(allowed_domains=[])
        with caplog.at_level(logging.WARNING, logger="mcp_servers.browser.service"):
            build_service(cfg)
        assert any("allowed_domains" in r.message for r in caplog.records)


# ── fmt_fetch ────────────────────────────────────────────────────────────────


class TestFmtFetch:
    @pytest.mark.asyncio
    async def test_fmt_fetch_formats_success_result(self) -> None:
        from unittest.mock import AsyncMock, patch

        svc = _make_service(allowed_domains=["example.com"])
        mock_result = BrowserFetchResponse(
            text="Hello world",
            truncated=False,
            url="https://example.com/",
            status_code=200,
            elapsed_sec=0.1,
        )
        with patch.object(svc, "fetch", new=AsyncMock(return_value=mock_result)):
            result = await svc.fmt_fetch({"url": "https://example.com/"})
        assert "status_code=200" in result
        assert "Hello world" in result

    @pytest.mark.asyncio
    async def test_fmt_fetch_truncated_flag(self) -> None:
        from unittest.mock import AsyncMock, patch

        svc = _make_service(allowed_domains=["example.com"])
        mock_result = BrowserFetchResponse(
            text="a" * 100,
            truncated=True,
            url="https://example.com/",
            status_code=200,
            elapsed_sec=0.2,
        )
        with patch.object(svc, "fetch", new=AsyncMock(return_value=mock_result)):
            result = await svc.fmt_fetch({"url": "https://example.com/"})
        assert "[RESPONSE TRUNCATED]" in result
