"""tests/mcp_servers/test_bounded_fetch.py

Unit tests for mcp_servers/bounded_fetch.py: pinned connection, bounded redirects,
2xx-only results, content-type gate, and independent raw, decoded, and parser-input
limits. No test touches the network: the transport and the resolver are injected.
"""

from __future__ import annotations

import gzip
import zlib
from collections.abc import AsyncIterator, Sequence
from urllib.parse import urlsplit

import httpx
import pytest
from mcp_servers.address_policy import AddressRejectedError
from mcp_servers.bounded_fetch import (
    BoundedFetchResult,
    FetchContentTypeError,
    FetchLimits,
    FetchRedirectError,
    FetchStatusError,
    FetchUnsupportedEncodingError,
    fetch_bounded,
)

_PUBLIC = "93.184.216.34"
_HTML = {"content-type": "text/html; charset=utf-8"}
_TYPES = frozenset({"text/html", "text/plain"})


class _AsyncStream(httpx.AsyncByteStream):
    def __init__(self, source: AsyncIterator[bytes]) -> None:
        self._source = source

    async def __aiter__(self) -> AsyncIterator[bytes]:
        async for chunk in self._source:
            yield chunk


def _response(
    status: int, content: bytes = b"", headers: dict[str, str] | None = None
) -> httpx.Response:
    """A response whose body is a real stream, as a network transport returns it."""

    async def _one() -> AsyncIterator[bytes]:
        if content:
            yield content

    return httpx.Response(status, stream=_AsyncStream(_one()), headers=headers)


_LIMITS = FetchLimits(
    raw_bytes=1024 * 1024,
    decoded_bytes=4 * 1024 * 1024,
    parser_input_bytes=1024 * 1024,
    returned_bytes=1024,
)


def _resolver(*answers: str, calls: list[str] | None = None):
    async def _resolve(host: str, port: int) -> Sequence[str]:
        if calls is not None:
            calls.append(host)
        return list(answers) or [_PUBLIC]

    return _resolve


def _allow(*hosts: str):
    allowed = {h.lower() for h in hosts}

    def _policy(url: str) -> str:
        host = (urlsplit(url).hostname or "").lower()
        if host not in allowed:
            raise PermissionError(f"host not allowed: {host}")
        return host

    return _policy


class _Recorder:
    def __init__(self, handler) -> None:
        self.requests: list[httpx.Request] = []
        self._handler = handler

    def transport(self) -> httpx.MockTransport:
        async def _call(request: httpx.Request) -> httpx.Response:
            self.requests.append(request)
            return await self._handler(request)

        return httpx.MockTransport(_call)


async def _fetch(
    url: str,
    handler,
    *,
    limits: FetchLimits = _LIMITS,
    hosts: tuple[str, ...] = ("example.com",),
    types: frozenset[str] = _TYPES,
    resolver=None,
    max_redirects: int = 5,
) -> tuple[BoundedFetchResult, _Recorder]:
    recorder = _Recorder(handler)
    result = await fetch_bounded(
        url,
        limits=limits,
        host_policy=_allow(*hosts),
        allowed_content_types=types,
        timeout_sec=5.0,
        max_redirects=max_redirects,
        resolver=resolver or _resolver(),
        transport=recorder.transport(),
    )
    return result, recorder


def _ok(body: bytes = b"<html>hi</html>", headers: dict[str, str] | None = None):
    async def _handler(request: httpx.Request) -> httpx.Response:
        return _response(200, body, headers=headers or _HTML)

    return _handler


@pytest.mark.asyncio
async def test_a_2xx_html_response_returns_the_body_and_metadata() -> None:
    result, _ = await _fetch("https://example.com/page", _ok())

    assert result.status_code == 200
    assert result.body == b"<html>hi</html>"
    assert result.content_type == "text/html"
    assert result.charset == "utf-8"
    assert result.download_truncated is False
    assert result.truncated_by is None


@pytest.mark.asyncio
async def test_the_request_is_pinned_to_the_validated_address() -> None:
    result, rec = await _fetch("https://example.com:8443/a?q=1", _ok())

    request = rec.requests[0]
    assert request.url.host == _PUBLIC
    assert request.url.port == 8443
    assert request.url.path == "/a"
    assert request.url.query == b"q=1"
    assert request.headers["host"] == "example.com:8443"
    assert request.extensions["sni_hostname"] == "example.com"
    assert result.final_url == "https://example.com:8443/a?q=1"


@pytest.mark.asyncio
async def test_an_ipv6_address_is_bracketed_in_the_pinned_url() -> None:
    _, rec = await _fetch(
        "https://example.com/", _ok(), resolver=_resolver("2606:4700:4700::1111")
    )

    assert rec.requests[0].url.host == "2606:4700:4700::1111"
    assert rec.requests[0].headers["host"] == "example.com"


@pytest.mark.asyncio
async def test_user_information_is_never_sent() -> None:
    _, rec = await _fetch("https://user:secret@example.com/", _ok())

    assert "authorization" not in rec.requests[0].headers
    assert "secret" not in str(rec.requests[0].url)


@pytest.mark.asyncio
async def test_the_resolver_runs_once_per_hop_and_cannot_change_the_address() -> None:
    answers = iter([[_PUBLIC], ["10.0.0.5"]])
    calls: list[str] = []

    async def _rebinding(host: str, port: int) -> Sequence[str]:
        calls.append(host)
        return next(answers)

    _, rec = await _fetch("https://example.com/", _ok(), resolver=_rebinding)

    assert calls == ["example.com"]
    assert rec.requests[0].url.host == _PUBLIC


@pytest.mark.asyncio
async def test_environment_proxies_are_ignored(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HTTPS_PROXY", "http://proxy.invalid:3128")
    monkeypatch.setenv("HTTP_PROXY", "http://proxy.invalid:3128")

    _, rec = await _fetch("https://example.com/", _ok())

    assert rec.requests[0].url.host == _PUBLIC


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "answers",
    [("10.0.0.5",), ("127.0.0.1",), ("169.254.169.254",), (_PUBLIC, "10.0.0.5")],
)
async def test_a_prohibited_answer_rejects_before_any_request(
    answers: tuple[str, ...],
) -> None:
    rec_holder: list[_Recorder] = []

    async def _handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("no request may be sent")

    with pytest.raises(AddressRejectedError) as excinfo:
        recorder = _Recorder(_handler)
        rec_holder.append(recorder)
        await fetch_bounded(
            "https://example.com/",
            limits=_LIMITS,
            host_policy=_allow("example.com"),
            allowed_content_types=_TYPES,
            timeout_sec=5.0,
            resolver=_resolver(*answers),
            transport=recorder.transport(),
        )

    assert excinfo.value.kind == "prohibited_address"
    assert rec_holder[0].requests == []


@pytest.mark.asyncio
async def test_the_host_policy_error_propagates_unchanged() -> None:
    with pytest.raises(PermissionError):
        await _fetch("https://evil.example/", _ok())


def _redirect(location: str, status: int = 302):
    async def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, headers={"location": location})

    return _handler


@pytest.mark.asyncio
async def test_a_redirect_within_the_policy_is_followed_and_reresolved() -> None:
    calls: list[str] = []

    async def _handler(request: httpx.Request) -> httpx.Response:
        if request.headers["host"] == "example.com":
            return httpx.Response(
                301, headers={"location": "https://docs.example.com/x"}
            )
        return _response(200, b"final", headers=_HTML)

    result, rec = await _fetch(
        "https://example.com/",
        _handler,
        hosts=("example.com", "docs.example.com"),
        resolver=_resolver(calls=calls),
    )

    assert result.body == b"final"
    assert calls == ["example.com", "docs.example.com"]
    assert result.final_url == "https://docs.example.com/x"
    assert len(rec.requests) == 2


@pytest.mark.asyncio
async def test_a_relative_location_is_resolved_against_the_current_url() -> None:
    async def _handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/start":
            return httpx.Response(307, headers={"location": "/landing"})
        return _response(200, b"ok", headers=_HTML)

    result, _ = await _fetch("https://example.com/start", _handler)

    assert result.final_url == "https://example.com/landing"


@pytest.mark.asyncio
async def test_a_redirect_to_a_host_outside_the_policy_is_rejected() -> None:
    with pytest.raises(PermissionError):
        await _fetch("https://example.com/", _redirect("https://evil.example/"))


@pytest.mark.asyncio
async def test_a_redirect_to_a_prohibited_address_is_rejected_on_that_hop() -> None:
    answers = {"example.com": _PUBLIC, "internal.example.com": "10.0.0.5"}

    async def _resolve(host: str, port: int) -> Sequence[str]:
        return [answers[host]]

    with pytest.raises(AddressRejectedError):
        await _fetch(
            "https://example.com/",
            _redirect("https://internal.example.com/"),
            hosts=("example.com", "internal.example.com"),
            resolver=_resolve,
        )


@pytest.mark.asyncio
@pytest.mark.parametrize("location", ["ftp://example.com/x", "file:///etc/passwd"])
async def test_a_redirect_to_a_non_http_scheme_is_rejected(location: str) -> None:
    with pytest.raises(FetchRedirectError):
        await _fetch("https://example.com/", _redirect(location))


@pytest.mark.asyncio
async def test_a_redirect_without_a_location_is_an_error() -> None:
    async def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302)

    with pytest.raises(FetchRedirectError):
        await _fetch("https://example.com/", _handler)


@pytest.mark.asyncio
async def test_the_redirect_bound_allows_five_hops_and_rejects_the_sixth() -> None:
    async def _chain(request: httpx.Request) -> httpx.Response:
        n = int(request.url.path.removeprefix("/hop") or 0)
        if n < 5:
            return httpx.Response(302, headers={"location": f"/hop{n + 1}"})
        return _response(200, b"end", headers=_HTML)

    result, _ = await _fetch("https://example.com/hop0", _chain)
    assert result.body == b"end"

    async def _endless(request: httpx.Request) -> httpx.Response:
        n = int(request.url.path.removeprefix("/hop") or 0)
        return httpx.Response(302, headers={"location": f"/hop{n + 1}"})

    with pytest.raises(FetchRedirectError):
        await _fetch("https://example.com/hop0", _endless)


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
async def test_non_2xx_statuses_raise_with_a_category_and_no_body(
    status: int, category: str
) -> None:
    async def _handler(request: httpx.Request) -> httpx.Response:
        return _response(status, b"<html>error page</html>", headers=_HTML)

    with pytest.raises(FetchStatusError) as excinfo:
        await _fetch("https://example.com/", _handler)

    assert excinfo.value.status_code == status
    assert excinfo.value.category == category
    assert "error page" not in str(excinfo.value)


@pytest.mark.asyncio
@pytest.mark.parametrize("media", ["application/pdf", "application/zip", "image/png"])
async def test_binary_types_are_rejected_before_the_body_is_read(media: str) -> None:
    async def _body() -> AsyncIterator[bytes]:
        raise AssertionError("the body must not be read")
        yield b""

    async def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, stream=_AsyncStream(_body()), headers={"content-type": media}
        )

    with pytest.raises(FetchContentTypeError) as excinfo:
        await _fetch("https://example.com/", _handler)

    assert excinfo.value.content_type == media


@pytest.mark.asyncio
async def test_a_missing_content_type_is_rejected() -> None:
    async def _handler(request: httpx.Request) -> httpx.Response:
        return _response(200, b"data")

    with pytest.raises(FetchContentTypeError):
        await _fetch("https://example.com/", _handler)


@pytest.mark.asyncio
async def test_text_plain_is_accepted() -> None:
    result, _ = await _fetch(
        "https://example.com/",
        _ok(b"plain", {"content-type": "text/plain"}),
    )

    assert result.content_type == "text/plain"
    assert result.body == b"plain"


def _chunked(chunks: list[bytes], headers: dict[str, str]):
    async def _gen() -> AsyncIterator[bytes]:
        for chunk in chunks:
            yield chunk

    async def _handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=_AsyncStream(_gen()), headers=headers)

    return _handler


@pytest.mark.asyncio
async def test_the_raw_limit_stops_the_stream() -> None:
    limits = FetchLimits(
        raw_bytes=10_000,
        decoded_bytes=10**7,
        parser_input_bytes=10**7,
        returned_bytes=10,
    )
    chunks = [b"a" * 4096] * 10

    result, _ = await _fetch(
        "https://example.com/", _chunked(chunks, _HTML), limits=limits
    )

    assert result.truncated_by == "raw"
    assert result.download_truncated is True
    assert len(result.body) <= 10_000


@pytest.mark.asyncio
async def test_the_parser_input_limit_caps_the_body() -> None:
    limits = FetchLimits(
        raw_bytes=10**7,
        decoded_bytes=10**7,
        parser_input_bytes=5_000,
        returned_bytes=10,
    )
    chunks = [b"b" * 4096] * 10

    result, _ = await _fetch(
        "https://example.com/", _chunked(chunks, _HTML), limits=limits
    )

    assert result.truncated_by == "parser_input"
    assert len(result.body) == 5_000


@pytest.mark.asyncio
async def test_the_decoded_limit_stops_a_decompression_bomb() -> None:
    bomb = gzip.compress(b"\x00" * 5_000_000)
    limits = FetchLimits(
        raw_bytes=10**7,
        decoded_bytes=200_000,
        parser_input_bytes=10**7,
        returned_bytes=10,
    )
    headers = {**_HTML, "content-encoding": "gzip"}

    result, _ = await _fetch(
        "https://example.com/", _chunked([bomb], headers), limits=limits
    )

    assert result.truncated_by == "decoded"
    assert len(result.body) == 200_000
    assert len(bomb) < 20_000


@pytest.mark.asyncio
async def test_gzip_and_deflate_bodies_are_decoded() -> None:
    payload = b"<html>" + b"hello " * 100 + b"</html>"
    for encoding, data in (
        ("gzip", gzip.compress(payload)),
        ("x-gzip", gzip.compress(payload)),
        ("deflate", zlib.compress(payload)),
    ):
        result, _ = await _fetch(
            "https://example.com/",
            _chunked([data[:30], data[30:]], {**_HTML, "content-encoding": encoding}),
        )
        assert result.body == payload, encoding
        assert result.truncated_by is None, encoding


@pytest.mark.asyncio
@pytest.mark.parametrize("encoding", ["br", "zstd", "gzip, deflate", "compress"])
async def test_other_content_encodings_are_rejected(encoding: str) -> None:
    with pytest.raises(FetchUnsupportedEncodingError) as excinfo:
        await _fetch(
            "https://example.com/",
            _ok(b"x", {**_HTML, "content-encoding": encoding}),
        )

    assert excinfo.value.encoding == encoding


@pytest.mark.asyncio
async def test_a_corrupt_gzip_body_is_rejected() -> None:
    with pytest.raises(FetchUnsupportedEncodingError):
        await _fetch(
            "https://example.com/",
            _ok(b"not gzip at all", {**_HTML, "content-encoding": "gzip"}),
        )


@pytest.mark.asyncio
async def test_a_false_content_length_cannot_raise_a_limit() -> None:
    limits = FetchLimits(
        raw_bytes=5_000,
        decoded_bytes=10**7,
        parser_input_bytes=10**7,
        returned_bytes=10,
    )
    headers = {**_HTML, "content-length": "10"}

    result, _ = await _fetch(
        "https://example.com/",
        _chunked([b"c" * 4096] * 4, headers),
        limits=limits,
    )

    assert result.declared_length == 10
    assert result.truncated_by == "raw"
    assert len(result.body) <= 5_000


@pytest.mark.asyncio
async def test_a_missing_content_length_and_chunked_transfer_are_still_bounded() -> (
    None
):
    limits = FetchLimits(
        raw_bytes=6_000,
        decoded_bytes=10**7,
        parser_input_bytes=10**7,
        returned_bytes=10,
    )

    result, _ = await _fetch(
        "https://example.com/",
        _chunked([b"d" * 1000] * 50, _HTML),
        limits=limits,
    )

    assert result.declared_length is None
    assert result.truncated_by == "raw"
    assert len(result.body) <= 6_000


@pytest.mark.asyncio
async def test_a_body_exactly_at_the_limit_is_not_truncated() -> None:
    limits = FetchLimits(
        raw_bytes=4_000,
        decoded_bytes=4_000,
        parser_input_bytes=4_000,
        returned_bytes=10,
    )

    result, _ = await _fetch("https://example.com/", _ok(b"e" * 4_000), limits=limits)

    assert result.truncated_by is None
    assert len(result.body) == 4_000


@pytest.mark.asyncio
async def test_a_connect_error_on_one_address_moves_to_the_next() -> None:
    async def _handler(request: httpx.Request) -> httpx.Response:
        if request.url.host == "93.184.216.34":
            raise httpx.ConnectError("refused", request=request)
        return _response(200, b"second", headers=_HTML)

    result, rec = await _fetch(
        "https://example.com/",
        _handler,
        resolver=_resolver("93.184.216.34", "1.1.1.1"),
    )

    assert result.body == b"second"
    assert [r.url.host for r in rec.requests] == ["93.184.216.34", "1.1.1.1"]


@pytest.mark.asyncio
async def test_httpx_timeouts_propagate_raw() -> None:
    async def _handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(httpx.TimeoutException):
        await _fetch("https://example.com/", _handler)


def test_limits_must_be_positive_integers() -> None:
    for bad in (0, -1):
        with pytest.raises(ValueError):
            FetchLimits(
                raw_bytes=bad, decoded_bytes=1, parser_input_bytes=1, returned_bytes=1
            )


@pytest.mark.asyncio
async def test_one_large_network_chunk_is_counted_by_its_own_size() -> None:
    """A single read larger than the raw limit keeps exactly the allowed prefix."""
    limits = FetchLimits(
        raw_bytes=100_000,
        decoded_bytes=10**7,
        parser_input_bytes=10**7,
        returned_bytes=10,
    )

    result, _ = await _fetch(
        "https://example.com/",
        _chunked([b"f" * 3_000_000], _HTML),
        limits=limits,
    )

    assert result.truncated_by == "raw"
    assert len(result.body) == 100_000
