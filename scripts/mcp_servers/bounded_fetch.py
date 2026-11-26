#!/usr/bin/env python3
"""scripts/mcp_servers/bounded_fetch.py — Bounded, pinned, redirect-checked download.

A reusable outbound GET for MCP servers: every hop runs a caller-supplied host policy
and the address policy, the connection is pinned to the validated address with the
original host kept as the `Host` header and the TLS server name, redirects are
followed by a bounded loop, only 2xx responses and allowed media types reach the
caller, and the body is streamed under independent raw, decoded, and parser-input
byte limits. Environment proxies are never used.

Dependency direction: mcp_servers.bounded_fetch → httpx, mcp_servers.address_policy
Import from here:  from mcp_servers.bounded_fetch import fetch_bounded, FetchLimits
"""

from __future__ import annotations

import asyncio
import time
import zlib
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from http import HTTPStatus
from urllib.parse import urljoin, urlsplit

import httpx

from mcp_servers.address_policy import (
    KIND_RESOLUTION_FAILED,
    AddressRejectedError,
    Resolver,
    resolve_public_addresses,
)

_REDIRECT_STATUSES = frozenset(
    {
        HTTPStatus.MOVED_PERMANENTLY,
        HTTPStatus.FOUND,
        HTTPStatus.SEE_OTHER,
        HTTPStatus.TEMPORARY_REDIRECT,
        HTTPStatus.PERMANENT_REDIRECT,
    }
)
_RAW_CHUNK_BYTES = 8192
_ACCEPT_ENCODING = "gzip, deflate"
_DEFAULT_PORTS = {"http": 80, "https": 443}

TRUNCATED_BY_RAW = "raw"
TRUNCATED_BY_DECODED = "decoded"
TRUNCATED_BY_PARSER_INPUT = "parser_input"


@dataclass(frozen=True)
class FetchLimits:
    """Independent byte limits of one download.

    `raw_bytes` bounds the bytes read from the network, `decoded_bytes` the bytes
    produced by content decoding, `parser_input_bytes` the body handed to the caller's
    parser, and `returned_bytes` the caller's own output (carried, not enforced here).
    """

    raw_bytes: int
    decoded_bytes: int
    parser_input_bytes: int
    returned_bytes: int

    def __post_init__(self) -> None:
        """Reject a non-positive limit."""
        for name in (
            "raw_bytes",
            "decoded_bytes",
            "parser_input_bytes",
            "returned_bytes",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"FetchLimits.{name} must be a positive integer")


@dataclass(frozen=True)
class BoundedFetchResult:
    """The accepted response of a bounded fetch."""

    final_url: str
    status_code: int
    content_type: str
    charset: str | None
    body: bytes
    download_truncated: bool
    truncated_by: str | None
    declared_length: int | None
    elapsed_sec: float


class FetchStatusError(RuntimeError):
    """A non-2xx final response; carries the status and a coarse category."""

    def __init__(self, status_code: int, category: str) -> None:
        super().__init__(f"upstream answered HTTP {status_code} ({category})")
        self.status_code = status_code
        self.category = category


class FetchRedirectError(RuntimeError):
    """A redirect that cannot be followed safely (no target, bad scheme, too many)."""


class FetchContentTypeError(RuntimeError):
    """The response media type is not in the caller's allowed set."""

    def __init__(self, content_type: str) -> None:
        super().__init__(f"unsupported content type: {content_type or '(none)'}")
        self.content_type = content_type


class FetchUnsupportedEncodingError(RuntimeError):
    """The content encoding is not supported or the body cannot be decoded."""

    def __init__(self, encoding: str) -> None:
        super().__init__(f"unsupported or undecodable content encoding: {encoding}")
        self.encoding = encoding


@dataclass(frozen=True)
class _Redirect:
    location: str


def _status_category(status: int) -> str:
    if status == HTTPStatus.TOO_MANY_REQUESTS:
        return "rate_limited"
    if 400 <= status < 500:
        return "client_error"
    if 500 <= status < 600:
        return "server_error"
    return "other"


def _media_type(header: str) -> tuple[str, str | None]:
    """Return the lowercased media type and the charset parameter, if any."""
    media, _, params = header.partition(";")
    charset: str | None = None
    for part in params.split(";"):
        key, _, value = part.strip().partition("=")
        if key.strip().lower() == "charset" and value:
            charset = value.strip().strip("\"'").lower() or None
    return media.strip().lower(), charset


class _BoundedDecoder:
    """Incremental content decoder whose output per call is capped by a budget."""

    def __init__(self, encoding: str) -> None:
        self._encoding = encoding
        self._started = False
        if encoding in ("", "identity"):
            self._zlib: zlib._Decompress | None = None
        elif encoding in ("gzip", "x-gzip"):
            self._zlib = zlib.decompressobj(zlib.MAX_WBITS | 32)
        elif encoding == "deflate":
            self._zlib = zlib.decompressobj(zlib.MAX_WBITS)
        else:
            raise FetchUnsupportedEncodingError(encoding)

    def feed(self, chunk: bytes, budget: int) -> tuple[bytes, bool]:
        """Return `(decoded bytes up to budget, whether more output was cut)`."""
        if self._zlib is None:
            return chunk[:budget], len(chunk) > budget
        try:
            out = self._zlib.decompress(chunk, budget)
        except zlib.error as exc:
            if self._encoding == "deflate" and not self._started:
                self._zlib = zlib.decompressobj(-zlib.MAX_WBITS)
                self._started = True
                return self.feed(chunk, budget)
            raise FetchUnsupportedEncodingError(self._encoding) from exc
        self._started = True
        cut = len(out) >= budget and bool(
            self._zlib.unconsumed_tail or not self._zlib.eof
        )
        return out, cut


def _pinned_url(url: str, address: str) -> tuple[str, str]:
    """Return the request URL targeting `address` and the original `Host` value."""
    parts = urlsplit(url)
    host = parts.hostname or ""
    host_header = f"{host}:{parts.port}" if parts.port else host
    literal = f"[{address}]" if ":" in address else address
    netloc = f"{literal}:{parts.port}" if parts.port else literal
    return parts._replace(netloc=netloc).geturl(), host_header


def _declared_length(headers: Mapping[str, str]) -> int | None:
    try:
        value = int(headers.get("content-length", ""))
    except ValueError:
        return None
    return value if value >= 0 else None


async def _read_body(
    response: httpx.Response, decoder: _BoundedDecoder, limits: FetchLimits
) -> tuple[bytes, str | None]:
    """Stream the body under the three limits; return it and what stopped it."""
    body = bytearray()
    raw_total = 0
    decoded_total = 0
    truncated_by: str | None = None
    async for chunk in response.aiter_raw(chunk_size=_RAW_CHUNK_BYTES):
        allowed = limits.raw_bytes - raw_total
        if allowed <= 0:
            truncated_by = TRUNCATED_BY_RAW
            break
        raw_cut = len(chunk) > allowed
        raw_total += min(len(chunk), allowed)
        out, decoded_cut = decoder.feed(
            chunk[:allowed], limits.decoded_bytes - decoded_total
        )
        decoded_total += len(out)
        room = limits.parser_input_bytes - len(body)
        body += out[:room]
        if len(out) > room:
            truncated_by = TRUNCATED_BY_PARSER_INPUT
        elif decoded_cut:
            truncated_by = TRUNCATED_BY_DECODED
        elif raw_cut:
            truncated_by = TRUNCATED_BY_RAW
        if truncated_by is not None:
            break
    return bytes(body), truncated_by


async def _request_once(
    client: httpx.AsyncClient,
    url: str,
    hostname: str,
    address: str,
    *,
    limits: FetchLimits,
    allowed_content_types: frozenset[str],
    headers: Mapping[str, str] | None,
    started: float,
) -> BoundedFetchResult | _Redirect:
    """Send one pinned GET and return the accepted result or the redirect target."""
    pinned, host_header = _pinned_url(url, address)
    request_headers = {
        **(headers or {}),
        "Host": host_header,
        "Accept-Encoding": _ACCEPT_ENCODING,
    }
    async with client.stream(
        "GET",
        pinned,
        headers=request_headers,
        extensions={"sni_hostname": hostname},
    ) as response:
        status = response.status_code
        if status in _REDIRECT_STATUSES:
            location = response.headers.get("location", "")
            if not location:
                raise FetchRedirectError("redirect without a Location header")
            target = urljoin(url, location)
            if urlsplit(target).scheme not in _DEFAULT_PORTS:
                raise FetchRedirectError("redirect to a non-http(s) scheme")
            return _Redirect(target)
        if not 200 <= status < 300:
            raise FetchStatusError(status, _status_category(status))
        media, charset = _media_type(response.headers.get("content-type", ""))
        if media not in allowed_content_types:
            raise FetchContentTypeError(media)
        encoding = response.headers.get("content-encoding", "").strip().lower()
        decoder = _BoundedDecoder(encoding)
        body, truncated_by = await _read_body(response, decoder, limits)
        return BoundedFetchResult(
            final_url=url,
            status_code=status,
            content_type=media,
            charset=charset,
            body=body,
            download_truncated=truncated_by is not None,
            truncated_by=truncated_by,
            declared_length=_declared_length(response.headers),
            elapsed_sec=time.perf_counter() - started,
        )


async def _fetch(
    url: str,
    *,
    limits: FetchLimits,
    host_policy: Callable[[str], str],
    allowed_content_types: frozenset[str],
    timeout_sec: float,
    max_redirects: int,
    resolver: Resolver | None,
    transport: httpx.AsyncBaseTransport | None,
    headers: Mapping[str, str] | None,
) -> BoundedFetchResult:
    started = time.perf_counter()
    async with httpx.AsyncClient(
        timeout=timeout_sec,
        follow_redirects=False,
        trust_env=False,
        transport=transport,
    ) as client:
        current = url
        for _hop in range(max_redirects + 1):
            hostname = host_policy(current)
            parts = urlsplit(current)
            port = parts.port or _DEFAULT_PORTS.get(parts.scheme, 443)
            addresses = await resolve_public_addresses(
                hostname, port, resolver=resolver
            )
            outcome: BoundedFetchResult | _Redirect | None = None
            last_error: httpx.ConnectError | None = None
            for address in addresses:
                try:
                    outcome = await _request_once(
                        client,
                        current,
                        hostname,
                        address,
                        limits=limits,
                        allowed_content_types=allowed_content_types,
                        headers=headers,
                        started=started,
                    )
                except httpx.ConnectError as exc:
                    last_error = exc
                    continue
                break
            if outcome is None:
                if last_error is not None:
                    raise last_error
                raise AddressRejectedError(hostname, KIND_RESOLUTION_FAILED)
            if isinstance(outcome, BoundedFetchResult):
                return outcome
            current = outcome.location
        raise FetchRedirectError(f"more than {max_redirects} redirects")


async def fetch_bounded(
    url: str,
    *,
    limits: FetchLimits,
    host_policy: Callable[[str], str],
    allowed_content_types: frozenset[str],
    timeout_sec: float,
    max_redirects: int = 5,
    resolver: Resolver | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
    headers: Mapping[str, str] | None = None,
) -> BoundedFetchResult:
    """GET `url` under the policies above and return the accepted response.

    `host_policy(url)` runs on every hop, returns the validated hostname, and raises
    the caller's own exception to reject a host (it propagates unchanged). Address
    rejection raises `AddressRejectedError`. The whole call runs under an overall
    deadline of `timeout_sec * (max_redirects + 1)` seconds, raised as an
    `httpx.TimeoutException`. `transport` and `resolver` exist for tests.
    """
    try:
        async with asyncio.timeout(timeout_sec * (max_redirects + 1)):
            return await _fetch(
                url,
                limits=limits,
                host_policy=host_policy,
                allowed_content_types=allowed_content_types,
                timeout_sec=timeout_sec,
                max_redirects=max_redirects,
                resolver=resolver,
                transport=transport,
                headers=headers,
            )
    except TimeoutError as exc:
        raise httpx.ReadTimeout("overall fetch deadline exceeded") from exc
