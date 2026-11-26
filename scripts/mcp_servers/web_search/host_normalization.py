#!/usr/bin/env python3
"""scripts/mcp_servers/web_search/host_normalization.py — Single host normalization.

One function normalizes a hostname (lowercase, IDNA ASCII, one trailing dot removed)
and is the only normalization used by configuration loading, the posture check, and
runtime authorization, so a configured allowlist entry and a request host are always
compared in the same form. Allowlist entries are validated strictly; an error names
the setting and the entry index, never the value.

Dependency direction: mcp_servers.web_search.host_normalization → (stdlib only, leaf module)
Import from here:  from mcp_servers.web_search.host_normalization import normalize_host
"""

from __future__ import annotations

import re

_SETTING = "browser_allowed_domains"
_MAX_HOST_LENGTH = 253
_LABEL_RE = re.compile(r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$")

# Checked in this order, so "https://h/p" is a scheme error and "u:p@h" a userinfo
# error rather than a port error.
_FORBIDDEN_CHARS: tuple[tuple[str, str], ...] = (
    ("/", "path"),
    ("?", "query"),
    ("#", "fragment"),
    ("@", "userinfo"),
    (":", "port"),
)


class HostNormalizationError(ValueError):
    """Raised when a host or an allowlist entry cannot be normalized.

    `reason` is one of `not_string`, `not_list`, `blank`, `scheme`, `path`,
    `query`, `fragment`, `userinfo`, `port`, `malformed`, or `duplicate`. The message
    never contains the rejected value.
    """

    def __init__(self, message: str, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def normalize_host(value: object) -> str:
    """Return the lowercase IDNA ASCII form of a bare hostname.

    A scheme, path, query, fragment, user information, or port, a blank or
    non-string value, and a malformed name raise `HostNormalizationError`. Exactly
    one trailing dot is removed.
    """
    if not isinstance(value, str):
        raise HostNormalizationError("host is not a string", "not_string")
    if not value.strip():
        raise HostNormalizationError("host is blank", "blank")
    if "://" in value:
        raise HostNormalizationError("host contains a scheme", "scheme")
    for char, reason in _FORBIDDEN_CHARS:
        if char in value:
            raise HostNormalizationError(f"host contains a {reason}", reason)
    host = value.lower()
    if host.endswith("."):
        host = host[:-1]
    if not host:
        raise HostNormalizationError("host is blank", "blank")
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise HostNormalizationError("host is malformed", "malformed") from exc
    if len(ascii_host) > _MAX_HOST_LENGTH or not all(
        _LABEL_RE.match(label) for label in ascii_host.split(".")
    ):
        raise HostNormalizationError("host is malformed", "malformed")
    return ascii_host


def validate_allowlist(entries: object) -> list[str]:
    """Return the normalized allowlist, or raise on the first invalid entry.

    An empty list is valid and means `browser_fetch` is disabled. A duplicate after
    normalization is rejected, naming both indexes.
    """
    if not isinstance(entries, list):
        raise HostNormalizationError(f"{_SETTING} must be a list", "not_list")
    normalized: list[str] = []
    first_index: dict[str, int] = {}
    for index, entry in enumerate(entries):
        try:
            host = normalize_host(entry)
        except HostNormalizationError as exc:
            raise HostNormalizationError(
                f"{_SETTING}[{index}] is invalid: {exc.reason}", exc.reason
            ) from exc
        if host in first_index:
            raise HostNormalizationError(
                f"{_SETTING}[{index}] duplicates {_SETTING}[{first_index[host]}]",
                "duplicate",
            )
        first_index[host] = index
        normalized.append(host)
    return normalized
