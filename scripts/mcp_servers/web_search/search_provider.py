#!/usr/bin/env python3
"""mcp_servers/web_search/search_provider.py

Search provider implementations for web-search-mcp.

Dependency direction: mcp_servers.web_search.search_provider → duckduckgo_search, mcp_servers.web_search.models
Import from here:  from mcp_servers.web_search.search_provider import search_duckduckgo
"""

from __future__ import annotations

import asyncio
import ipaddress
from urllib.parse import urlsplit

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from mcp_servers.web_search.web_search_models import (
    BrowserAuthorizationError,
    BrowserConfig,
    BrowserFetchRequest,
    BrowserFetchResponse,
    BrowserValidationError,
    SearchResult,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchProviderError,
    WebSearchTimeoutError,
)


async def search_duckduckgo(
    query: str, max_results: int, search_timeout_sec: float
) -> list[SearchResult]:
    """Execute a text search using DuckDuckGo. No API key required.

    Raises:
        WebSearchTimeoutError: if the search exceeds search_timeout_sec.
        WebSearchNetworkError: on a network-level provider failure.
        WebSearchProviderError: on any other provider-side failure.
        WebSearchParseError: if a raw result item is not a dict.
    """

    def _sync_search() -> list[dict]:
        """Run the synchronous DuckDuckGo search within a thread pool."""
        with DDGS() as ddgs:
            return list(ddgs.text(query, max_results=max_results))

    try:
        raw = await asyncio.wait_for(
            asyncio.to_thread(_sync_search), timeout=search_timeout_sec
        )
    except TimeoutError as e:
        raise WebSearchTimeoutError(
            f"DuckDuckGo search timed out after {search_timeout_sec}s"
        ) from e
    except (RuntimeError, OSError) as e:
        raise WebSearchNetworkError(f"DuckDuckGo search failed: {e}") from e
    except Exception as e:  # noqa: BLE001 — classification fallback, see UNK-01
        raise WebSearchProviderError(f"DuckDuckGo search failed: {e}") from e

    for item in raw:
        if not isinstance(item, dict):
            raise WebSearchParseError(
                f"unexpected result item type: {type(item).__name__}"
            )

    return [
        SearchResult(
            title=r.get("title", ""),
            url=r.get("href", ""),
            body=r.get("body", ""),
            provider="duckduckgo",
        )
        for r in raw
    ]


def _check_domain(url: str, allowed_domains: set[str]) -> str:
    """Validate URL scheme and hostname; return the validated hostname.

    Raises BrowserValidationError for a malformed URL (bad scheme or
    missing hostname). Raises BrowserAuthorizationError when the hostname
    is an IP literal in a loopback/link-local/private/reserved/multicast
    range (checked unconditionally, regardless of the allowlist — defense
    in depth) or when it does not match allowed_domains (fail-closed: an
    empty allowlist denies everything).
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
    if hostname not in allowed_domains:
        raise BrowserAuthorizationError(f"Domain not in allowlist: {hostname!r}")
    return hostname


def _extract_text(html: str) -> str:
    """Parse HTML and return visible text, stripping script/style tags."""
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)


def _truncate(text: str, max_kb: int) -> tuple[str, bool]:
    """Truncate text to max_kb kilobytes, slicing bytes before decoding.

    Encoding to bytes and slicing there (rather than naive character
    slicing) avoids cutting a multibyte UTF-8 character in half.
    """
    encoded = text.encode("utf-8")
    max_bytes = max_kb * 1024
    if len(encoded) <= max_bytes:
        return text, False
    return encoded[:max_bytes].decode("utf-8", errors="replace"), True


async def fetch_browser(
    req: BrowserFetchRequest, cfg: BrowserConfig
) -> BrowserFetchResponse:
    """Fetch a URL and return extracted, truncated text.

    Steps:
      1. Domain allowlist and IP-literal/loopback check
      2. Clamp caller-supplied max_response_kb to the server maximum
      3. GET the URL via httpx.AsyncClient with the configured timeout
      4. Extract visible text from the HTML response
      5. Truncate the extracted text if over the size cap

    Raises:
        BrowserValidationError: on a malformed URL (bad scheme or missing hostname).
        BrowserAuthorizationError: on an IP-literal target or a non-allowlisted domain.
    """
    _check_domain(req.url, set(cfg.allowed_domains))
    max_response_kb = min(
        req.max_response_kb or cfg.max_response_kb, cfg.max_response_kb
    )

    async with httpx.AsyncClient(timeout=cfg.timeout_sec) as client:
        resp = await client.get(req.url)

    text = _extract_text(resp.text)
    text, truncated = _truncate(text, max_response_kb)

    return BrowserFetchResponse(
        text=text,
        truncated=truncated,
        url=req.url,
        status_code=resp.status_code,
        elapsed_sec=resp.elapsed.total_seconds(),
    )
