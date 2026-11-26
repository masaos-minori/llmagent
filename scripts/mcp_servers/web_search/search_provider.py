#!/usr/bin/env python3
"""scripts/mcp_servers/web_search/search_provider.py

Search provider implementations for web-search-mcp.

Dependency direction: mcp_servers.web_search.search_provider → duckduckgo_search, mcp_servers.web_search.web_search_models
Import from here:  from mcp_servers.web_search.search_provider import search_duckduckgo
"""

from __future__ import annotations

import asyncio
import ipaddress
from urllib.parse import urlsplit

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from mcp_servers.address_policy import (
    KIND_PROHIBITED_ADDRESS,
    AddressRejectedError,
    Resolver,
)
from mcp_servers.bounded_fetch import (
    FetchContentTypeError,
    FetchLimits,
    FetchRedirectError,
    FetchStatusError,
    FetchUnsupportedEncodingError,
    fetch_bounded,
)
from mcp_servers.web_search.host_normalization import (
    HostNormalizationError,
    normalize_host,
)
from mcp_servers.web_search.web_search_models import (
    BrowserAuthorizationError,
    BrowserConfig,
    BrowserFetchRequest,
    BrowserFetchResponse,
    BrowserHttpStatusError,
    BrowserUnsupportedContentError,
    BrowserValidationError,
    SearchResult,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchProviderError,
    WebSearchTimeoutError,
)

# Network limits of one browser_fetch (the returned-text limit comes from the
# configured browser_max_response_kb): raw bytes read, bytes after content decoding,
# and bytes handed to the parser.
_FETCH_RAW_LIMIT_BYTES = 2 * 1024 * 1024
_FETCH_DECODED_LIMIT_BYTES = 8 * 1024 * 1024
_FETCH_PARSER_INPUT_LIMIT_BYTES = 2 * 1024 * 1024
_ALLOWED_CONTENT_TYPES = frozenset({"text/html", "text/plain"})


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

    _validate_raw_items(raw)
    return _build_search_results(raw)


def _validate_raw_items(raw: list[dict[str, str]]) -> None:
    """Raise WebSearchParseError if any raw result item is not a dict."""
    for item in raw:
        if not isinstance(item, dict):
            raise WebSearchParseError(
                f"unexpected result item type: {type(item).__name__}"
            )


def _build_search_results(raw: list[dict[str, str]]) -> list[SearchResult]:
    """Convert validated raw DuckDuckGo result dicts into SearchResult objects."""
    return [
        SearchResult(
            title=r.get("title", ""),
            url=r.get("href", ""),
            body=r.get("body", ""),
            provider="duckduckgo",
        )
        for r in raw
    ]


def _host_in_allowlist(hostname: str, allowed_domains: set[str]) -> bool:
    """Return True when the normalized `hostname` matches a normalized member.

    A member that cannot be normalized never matches, so a bad entry fails closed.
    """
    for entry in allowed_domains:
        try:
            if normalize_host(entry) == hostname:
                return True
        except HostNormalizationError:
            continue
    return False


def _reject_prohibited_ip_literal(host: str) -> None:
    """Raise BrowserAuthorizationError for a loopback/link-local/private/reserved/
    multicast IP-literal host; a non-IP host and a public IP pass."""
    try:
        ip = ipaddress.ip_address(host)
    except ValueError:
        return
    if (
        ip.is_loopback
        or ip.is_link_local
        or ip.is_private
        or ip.is_reserved
        or ip.is_multicast
    ):
        raise BrowserAuthorizationError(f"IP-literal target not allowed: {host!r}")


def _check_domain(url: str, allowed_domains: set[str]) -> str:
    """Validate URL scheme and hostname; return the normalized hostname.

    Raises BrowserValidationError for a malformed URL (bad scheme, missing or
    invalid hostname). Raises BrowserAuthorizationError when the hostname
    is an IP literal in a loopback/link-local/private/reserved/multicast
    range (checked unconditionally, regardless of the allowlist — defense
    in depth) or when it does not match allowed_domains (fail-closed: an
    empty allowlist denies everything). Matching is on the normalized form
    (lowercase, IDNA ASCII, one trailing dot removed) of both the URL host and
    each allowlist member.
    """
    parts = urlsplit(url)
    if parts.scheme not in ("http", "https"):
        raise BrowserValidationError(f"Unsupported URL scheme: {parts.scheme!r}")
    raw_host = (parts.hostname or "").lower()
    if not raw_host:
        raise BrowserValidationError("URL is missing a hostname")
    _reject_prohibited_ip_literal(raw_host)
    try:
        hostname = normalize_host(raw_host)
    except HostNormalizationError as exc:
        raise BrowserValidationError("URL has an invalid hostname") from exc
    if not _host_in_allowlist(hostname, allowed_domains):
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


def _decode_body(body: bytes, charset: str | None) -> str:
    """Decode a fetched body with its declared charset, falling back to UTF-8."""
    try:
        return body.decode(charset or "utf-8", errors="replace")
    except LookupError:
        return body.decode("utf-8", errors="replace")


async def fetch_browser(
    req: BrowserFetchRequest,
    cfg: BrowserConfig,
    *,
    resolver: Resolver | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
) -> BrowserFetchResponse:
    """Fetch a URL and return extracted, truncated text.

    Steps:
      1. Domain allowlist and IP-literal/loopback check
      2. Clamp caller-supplied max_response_kb to the server maximum
      3. Bounded fetch: every hop is allowlist-checked, every resolved address must
         be public, the connection is pinned to the validated address, redirects are
         bounded, only 2xx text/html and text/plain responses are accepted, and
         raw, decoded, and parser-input bytes are limited independently
      4. Extract visible text from HTML (plain text is used as is)
      5. Truncate the extracted text if over the size cap

    `resolver` and `transport` exist for tests; production callers omit them.

    Raises:
        BrowserValidationError: on a malformed URL (bad scheme or missing hostname).
        BrowserAuthorizationError: on an IP-literal target, a non-allowlisted
            domain, or a host that resolves to a prohibited address.
        WebSearchNetworkError: when the host cannot be resolved.
        BrowserHttpStatusError: on a non-2xx outcome or an unusable redirect.
        BrowserUnsupportedContentError: on a content type or encoding that is not
            supported.
    """
    allowed = set(cfg.allowed_domains)
    _check_domain(req.url, allowed)
    max_response_kb = min(
        req.max_response_kb or cfg.max_response_kb, cfg.max_response_kb
    )
    limits = FetchLimits(
        raw_bytes=_FETCH_RAW_LIMIT_BYTES,
        decoded_bytes=_FETCH_DECODED_LIMIT_BYTES,
        parser_input_bytes=_FETCH_PARSER_INPUT_LIMIT_BYTES,
        returned_bytes=max_response_kb * 1024,
    )

    try:
        fetched = await fetch_bounded(
            req.url,
            limits=limits,
            host_policy=lambda url: _check_domain(url, allowed),
            allowed_content_types=_ALLOWED_CONTENT_TYPES,
            timeout_sec=float(cfg.timeout_sec),
            resolver=resolver,
            transport=transport,
        )
    except AddressRejectedError as exc:
        if exc.kind == KIND_PROHIBITED_ADDRESS:
            raise BrowserAuthorizationError(str(exc)) from exc
        raise WebSearchNetworkError(str(exc)) from exc
    except FetchStatusError as exc:
        raise BrowserHttpStatusError(str(exc), exc.status_code, exc.category) from exc
    except FetchRedirectError as exc:
        raise BrowserHttpStatusError(str(exc), 0, "redirect") from exc
    except FetchContentTypeError as exc:
        raise BrowserUnsupportedContentError(str(exc), exc.content_type) from exc
    except FetchUnsupportedEncodingError as exc:
        raise BrowserUnsupportedContentError(str(exc), exc.encoding) from exc

    text = _decode_body(fetched.body, fetched.charset)
    if fetched.content_type == "text/html":
        text = _extract_text(text)
    else:
        text = text.strip()
    text, truncated = _truncate(text, max_response_kb)

    return BrowserFetchResponse(
        text=text,
        truncated=truncated,
        url=req.url,
        status_code=fetched.status_code,
        elapsed_sec=fetched.elapsed_sec,
        download_truncated=fetched.download_truncated,
        content_type=fetched.content_type,
    )
