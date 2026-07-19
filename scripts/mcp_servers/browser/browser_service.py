#!/usr/bin/env python3
"""mcp_servers/browser/service.py

BrowserService business logic for browser-mcp: fetches a URL, enforces a
fail-closed domain allowlist plus IP-literal/loopback rejection (defense in
depth), extracts visible text from HTML, and truncates the result with a
flag — mirroring ShellService's allowlist-and-reject / truncate-with-flag
shape in scripts/mcp_servers/shell/service.py.

Dependency direction: browser_mcp_models -> browser_mcp_service -> browser_mcp_server
"""

from __future__ import annotations

import ipaddress
import logging
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

import httpx
from bs4 import BeautifulSoup

from mcp_servers.browser.browser_models import (
    BrowserAuthorizationError,
    BrowserConfig,
    BrowserFetchRequest,
    BrowserFetchResponse,
    BrowserValidationError,
)
from mcp_servers.server import ToolArgs

logger = logging.getLogger(__name__)


class BrowserService:
    """Encapsulates outbound HTTP fetch with a domain allowlist and text extraction."""

    def __init__(self, cfg: BrowserConfig) -> None:
        """Initialize with browser config including allowlist, size cap, and timeout."""
        self._allowed_domains: set[str] = set(cfg.allowed_domains)
        self._max_response_kb = cfg.max_response_kb
        self._timeout_sec = cfg.timeout_sec

    def _check_domain(self, url: str) -> str:
        """Validate URL scheme and hostname; return the validated hostname.

        Raises BrowserValidationError for a malformed URL (bad scheme or
        missing hostname). Raises BrowserAuthorizationError when the
        hostname is an IP literal in a loopback/link-local/private/
        reserved/multicast range (checked unconditionally, regardless of
        the allowlist — defense in depth) or when it does not match
        allowed_domains (fail-closed: an empty allowlist denies everything).
        """
        parts = urlsplit(url)
        if parts.scheme not in ("http", "https"):
            raise BrowserValidationError(f"Unsupported URL scheme: {parts.scheme!r}")
        hostname = (parts.hostname or "").lower()
        if not hostname:
            raise BrowserValidationError("URL is missing a hostname")
        try:
            ip = ipaddress.ip_address(hostname)
        except ValueError:
            pass
        else:
            if (
                ip.is_loopback
                or ip.is_link_local
                or ip.is_private
                or ip.is_reserved
                or ip.is_multicast
            ):
                raise BrowserAuthorizationError(
                    f"IP-literal target not allowed: {hostname!r}"
                )
        if hostname not in self._allowed_domains:
            raise BrowserAuthorizationError(f"Domain not in allowlist: {hostname!r}")
        return hostname

    async def fetch(self, req: BrowserFetchRequest) -> BrowserFetchResponse:
        """Fetch a URL and return extracted, truncated text.

        Steps:
          1. Domain allowlist and IP-literal/loopback check
          2. Clamp caller-supplied max_response_kb to the server maximum
          3. GET the URL via httpx.AsyncClient with the configured timeout
          4. Extract visible text from the HTML response
          5. Truncate the extracted text if over the size cap
        """
        self._check_domain(req.url)
        max_response_kb = min(
            req.max_response_kb or self._max_response_kb, self._max_response_kb
        )

        async with httpx.AsyncClient(timeout=self._timeout_sec) as client:
            resp = await client.get(req.url)

        text = self._extract_text(resp.text)
        text, truncated = self._truncate(text, max_response_kb)

        return BrowserFetchResponse(
            text=text,
            truncated=truncated,
            url=req.url,
            status_code=resp.status_code,
            elapsed_sec=resp.elapsed.total_seconds(),
        )

    def _extract_text(self, html: str) -> str:
        """Parse HTML and return visible text, stripping script/style tags."""
        soup = BeautifulSoup(html, "lxml")
        for tag in soup(["script", "style"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    def _truncate(self, text: str, max_kb: int) -> tuple[str, bool]:
        """Truncate text to max_kb kilobytes, slicing bytes before decoding.

        Encoding to bytes and slicing there (rather than naive character
        slicing) avoids cutting a multibyte UTF-8 character in half, mirroring
        SubprocessRunner.truncate_output's byte-slice-before-decode approach.
        """
        encoded = text.encode("utf-8")
        max_bytes = max_kb * 1024
        if len(encoded) <= max_bytes:
            return text, False
        return encoded[:max_bytes].decode("utf-8", errors="replace"), True

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_fetch(self, args: ToolArgs) -> str:
        """Fetch a URL via the service and format the result as plain text."""
        req = BrowserFetchRequest(**args)
        result = await self.fetch(req)
        return self._format_fetch_result(result)

    @staticmethod
    def _format_fetch_result(result: BrowserFetchResponse) -> str:
        """Format a BrowserFetchResponse as plain text for the LLM."""
        parts: list[str] = [
            f"status_code={result.status_code} elapsed={result.elapsed_sec}s"
        ]
        if result.truncated:
            parts.append("[RESPONSE TRUNCATED]")
        parts.append(result.text)
        return "\n".join(parts)

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        """Build and return the MCP tool dispatch table keyed by tool name."""
        return {
            "browser_fetch": self.fmt_fetch,
        }


def build_service(cfg: BrowserConfig) -> BrowserService:
    """Construct a BrowserService from a BrowserConfig object."""
    if not cfg.allowed_domains:
        logger.warning(
            "browser allowed_domains is empty — all domains will be rejected",
        )
    return BrowserService(cfg)
