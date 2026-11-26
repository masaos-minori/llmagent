#!/usr/bin/env python3
"""scripts/mcp_servers/address_policy.py — Public-address policy for outbound fetches.

Resolves every A and AAAA answer of a host and accepts it only when all answers are
public addresses. A prohibited answer rejects the whole set (mixed answers are not
filtered), and an empty answer or a failed lookup fails closed.

Dependency direction: mcp_servers.address_policy → (stdlib only, leaf module)
Import from here:  from mcp_servers.address_policy import resolve_public_addresses
"""

from __future__ import annotations

import asyncio
import ipaddress
import socket
from collections.abc import Awaitable, Callable, Sequence

KIND_PROHIBITED_ADDRESS = "prohibited_address"
KIND_RESOLUTION_FAILED = "resolution_failed"

Resolver = Callable[[str, int], Awaitable[Sequence[str]]]


class AddressRejectedError(RuntimeError):
    """Raised when a host cannot be shown to resolve only to public addresses.

    `kind` is `prohibited_address` when an answer is not public and
    `resolution_failed` when no usable answer could be obtained. The message names
    the host and the kind, never the resolved addresses.
    """

    def __init__(self, host: str, kind: str) -> None:
        super().__init__(f"address policy rejected host {host!r}: {kind}")
        self.host = host
        self.kind = kind


def _strip_scope(address: str) -> str:
    """Return `address` without an IPv6 zone suffix such as `%eth0`."""
    return address.split("%", 1)[0]


def is_public_address(address: str) -> bool:
    """Return True only for a global unicast address.

    An IPv4-mapped IPv6 address is judged as the IPv4 address it wraps. An
    unparseable value is not public.
    """
    try:
        parsed = ipaddress.ip_address(_strip_scope(address))
    except ValueError:
        return False
    if isinstance(parsed, ipaddress.IPv6Address) and parsed.ipv4_mapped is not None:
        parsed = parsed.ipv4_mapped
    return bool(
        parsed.is_global
        and not parsed.is_private
        and not parsed.is_loopback
        and not parsed.is_link_local
        and not parsed.is_reserved
        and not parsed.is_multicast
        and not parsed.is_unspecified
    )


async def _default_resolver(host: str, port: int) -> Sequence[str]:
    """Resolve `host` with the running loop's resolver and return the addresses."""
    loop = asyncio.get_running_loop()
    infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    return [str(info[4][0]) for info in infos]


def _is_ip_literal(host: str) -> bool:
    try:
        ipaddress.ip_address(_strip_scope(host))
    except ValueError:
        return False
    return True


async def resolve_public_addresses(
    host: str, port: int, *, resolver: Resolver | None = None
) -> tuple[str, ...]:
    """Return the validated addresses of `host`, or raise `AddressRejectedError`.

    An IP-literal host is validated directly with no lookup. Otherwise every answer
    must be public: one prohibited answer rejects the whole set. The returned tuple
    keeps the answer order without duplicates, and is the list a connection must
    use, so a caller does not resolve the same hop again.
    """
    if _is_ip_literal(host):
        if not is_public_address(host):
            raise AddressRejectedError(host, KIND_PROHIBITED_ADDRESS)
        return (_strip_scope(host),)

    lookup = resolver if resolver is not None else _default_resolver
    try:
        answers = await lookup(host, port)
    except (OSError, RuntimeError) as exc:
        raise AddressRejectedError(host, KIND_RESOLUTION_FAILED) from exc

    unique = tuple(dict.fromkeys(_strip_scope(str(a)) for a in answers))
    if not unique:
        raise AddressRejectedError(host, KIND_RESOLUTION_FAILED)
    if not all(is_public_address(a) for a in unique):
        raise AddressRejectedError(host, KIND_PROHIBITED_ADDRESS)
    return unique
