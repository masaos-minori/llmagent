"""tests/mcp_servers/web_search/test_host_normalization.py

Unit tests for host_normalization.py: the single normalization used by config
loading, the posture check, and runtime authorization, plus strict allowlist
entry validation.
"""

from __future__ import annotations

import pytest
from mcp_servers.web_search.host_normalization import (
    HostNormalizationError,
    normalize_host,
    validate_allowlist,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("example.com", "example.com"),
        ("Example.COM", "example.com"),
        ("EXAMPLE.com.", "example.com"),
        ("example.com.", "example.com"),
        ("sub.example.co.uk", "sub.example.co.uk"),
        ("xn--r8jz45g.jp", "xn--r8jz45g.jp"),
        ("例え.jp", "xn--r8jz45g.jp"),
        ("EXAMPLE-1.com", "example-1.com"),
        ("127.0.0.1", "127.0.0.1"),
    ],
)
def test_normalize_host_returns_the_lowercase_ascii_form(
    value: str, expected: str
) -> None:
    assert normalize_host(value) == expected


def test_a_u_label_and_its_a_label_normalize_to_the_same_host() -> None:
    assert normalize_host("例え.jp") == normalize_host("XN--R8JZ45G.JP")


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (None, "not_string"),
        (123, "not_string"),
        (["example.com"], "not_string"),
        ("", "blank"),
        ("   ", "blank"),
        (".", "blank"),
        ("https://example.com", "scheme"),
        ("http://example.com/path", "scheme"),
        ("example.com/path", "path"),
        ("example.com/", "path"),
        ("example.com?x=1", "query"),
        ("example.com#frag", "fragment"),
        ("user@example.com", "userinfo"),
        ("user:pw@example.com", "userinfo"),
        ("example.com:8080", "port"),
        ("[::1]", "port"),
        ("exa mple.com", "malformed"),
        ("example..com", "malformed"),
        ("-example.com", "malformed"),
        ("example-.com", "malformed"),
        ("exa_mple.com", "malformed"),
        ("exa%41mple.com", "malformed"),
        ("a" * 64 + ".com", "malformed"),
        (("a" * 60 + ".") * 5 + "com", "malformed"),
        ("example.com\\evil", "malformed"),
    ],
)
def test_normalize_host_rejects_with_a_reason(value: object, reason: str) -> None:
    with pytest.raises(HostNormalizationError) as excinfo:
        normalize_host(value)

    assert excinfo.value.reason == reason


def test_the_error_message_never_echoes_the_value() -> None:
    with pytest.raises(HostNormalizationError) as excinfo:
        normalize_host("https://secret-host.example/path")

    assert "secret-host" not in str(excinfo.value)


def test_validate_allowlist_normalizes_in_order() -> None:
    assert validate_allowlist(["Example.COM", "例え.jp", "docs.example.org."]) == [
        "example.com",
        "xn--r8jz45g.jp",
        "docs.example.org",
    ]


def test_an_empty_allowlist_is_valid() -> None:
    assert validate_allowlist([]) == []


@pytest.mark.parametrize("value", [None, "example.com", ("example.com",), {"a": 1}])
def test_a_non_list_allowlist_is_rejected(value: object) -> None:
    with pytest.raises(HostNormalizationError) as excinfo:
        validate_allowlist(value)

    assert excinfo.value.reason == "not_list"


@pytest.mark.parametrize(
    ("entries", "index", "reason"),
    [
        (["ok.example", "https://bad.example"], 1, "scheme"),
        (["ok.example", "bad.example/path"], 1, "path"),
        (["bad.example:443"], 0, "port"),
        (["ok.example", "ok2.example", ""], 2, "blank"),
        (["ok.example", 5], 1, "not_string"),
        (["bad host.example"], 0, "malformed"),
    ],
)
def test_validate_allowlist_names_the_index_and_reason_not_the_value(
    entries: list[object], index: int, reason: str
) -> None:
    with pytest.raises(HostNormalizationError) as excinfo:
        validate_allowlist(entries)

    message = str(excinfo.value)
    assert f"browser_allowed_domains[{index}]" in message
    assert reason in message
    assert excinfo.value.reason == reason
    for entry in entries:
        if isinstance(entry, str) and len(entry) > 3:
            assert entry not in message


def test_a_duplicate_after_normalization_is_rejected_naming_both_indexes() -> None:
    with pytest.raises(HostNormalizationError) as excinfo:
        validate_allowlist(["Example.com", "other.example", "example.COM."])

    assert excinfo.value.reason == "duplicate"
    assert "[2]" in str(excinfo.value)
    assert "[0]" in str(excinfo.value)
    assert "example" not in str(excinfo.value).replace("browser_allowed_domains", "")
