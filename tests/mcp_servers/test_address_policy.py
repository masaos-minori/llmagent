"""tests/mcp_servers/test_address_policy.py

Unit tests for mcp_servers/address_policy.py: prohibited-address classification and
fail-closed resolution of every A and AAAA answer.
"""

from __future__ import annotations

import socket
from collections.abc import Sequence

import pytest
from mcp_servers.address_policy import (
    AddressRejectedError,
    is_public_address,
    resolve_public_addresses,
)


def _resolver(*answers: str):
    async def _resolve(host: str, port: int) -> Sequence[str]:
        return list(answers)

    return _resolve


@pytest.mark.parametrize(
    "address",
    [
        "8.8.8.8",
        "1.1.1.1",
        "93.184.216.34",
        "2606:4700:4700::1111",
        "::ffff:8.8.8.8",
    ],
)
def test_public_addresses_are_public(address: str) -> None:
    assert is_public_address(address) is True


@pytest.mark.parametrize(
    "address",
    [
        "127.0.0.1",
        "127.255.255.254",
        "10.0.0.1",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.1.1",
        "169.254.169.254",
        "100.64.0.1",
        "0.0.0.0",
        "240.0.0.1",
        "224.0.0.1",
        "239.255.255.250",
        "::1",
        "::",
        "fc00::1",
        "fd12:3456::1",
        "fe80::1",
        "ff02::1",
        "::ffff:127.0.0.1",
        "::ffff:10.0.0.1",
        "::ffff:169.254.169.254",
        "fe80::1%eth0",
        "not-an-ip",
        "",
    ],
)
def test_prohibited_or_unparseable_addresses_are_not_public(address: str) -> None:
    assert is_public_address(address) is False


@pytest.mark.asyncio
async def test_public_answers_are_returned_in_order_without_duplicates() -> None:
    result = await resolve_public_addresses(
        "example.com", 443, resolver=_resolver("8.8.8.8", "1.1.1.1", "8.8.8.8")
    )

    assert result == ("8.8.8.8", "1.1.1.1")


@pytest.mark.asyncio
async def test_ip_literal_host_is_validated_without_a_lookup() -> None:
    async def _must_not_run(host: str, port: int) -> Sequence[str]:
        raise AssertionError("resolver must not be called for an IP literal")

    assert await resolve_public_addresses("8.8.8.8", 443, resolver=_must_not_run) == (
        "8.8.8.8",
    )
    with pytest.raises(AddressRejectedError) as excinfo:
        await resolve_public_addresses("127.0.0.1", 80, resolver=_must_not_run)
    assert excinfo.value.kind == "prohibited_address"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "answers",
    [
        ("127.0.0.1",),
        ("10.0.0.5",),
        ("169.254.169.254",),
        ("::1",),
        ("::ffff:10.0.0.1",),
        ("8.8.8.8", "10.0.0.5"),
        ("10.0.0.5", "8.8.8.8"),
        ("2606:4700:4700::1111", "fe80::1"),
    ],
)
async def test_any_prohibited_answer_rejects_the_whole_set(
    answers: tuple[str, ...],
) -> None:
    with pytest.raises(AddressRejectedError) as excinfo:
        await resolve_public_addresses("example.com", 443, resolver=_resolver(*answers))

    assert excinfo.value.kind == "prohibited_address"
    assert "example.com" in str(excinfo.value)
    for address in answers:
        assert address not in str(excinfo.value)


@pytest.mark.asyncio
async def test_an_empty_answer_fails_closed() -> None:
    with pytest.raises(AddressRejectedError) as excinfo:
        await resolve_public_addresses("example.com", 443, resolver=_resolver())

    assert excinfo.value.kind == "resolution_failed"


@pytest.mark.asyncio
async def test_a_resolver_exception_fails_closed() -> None:
    async def _boom(host: str, port: int) -> Sequence[str]:
        raise OSError("name or service not known")

    with pytest.raises(AddressRejectedError) as excinfo:
        await resolve_public_addresses("example.com", 443, resolver=_boom)

    assert excinfo.value.kind == "resolution_failed"


@pytest.mark.asyncio
async def test_the_default_resolver_maps_gaierror_to_resolution_failed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _fail(*args: object, **kwargs: object) -> list[object]:
        raise socket.gaierror("lookup disabled in tests")

    monkeypatch.setattr(socket, "getaddrinfo", _fail)

    with pytest.raises(AddressRejectedError) as excinfo:
        await resolve_public_addresses("example.com", 443)

    assert excinfo.value.kind == "resolution_failed"


@pytest.mark.asyncio
async def test_the_default_resolver_returns_the_looked_up_addresses(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _lookup(*args: object, **kwargs: object) -> list[tuple[object, ...]]:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))]

    monkeypatch.setattr(socket, "getaddrinfo", _lookup)

    assert await resolve_public_addresses("example.com", 443) == ("8.8.8.8",)
