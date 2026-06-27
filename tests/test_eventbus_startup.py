"""tests/test_eventbus_startup.py
Event Bus startup safety guard tests for public bind detection.
"""

from __future__ import annotations

import ipaddress
import pytest

from scripts.eventbus.config import (
    EventBusConfig,
    _is_public_host,
)


def test_is_public_host_0000() -> None:
    assert _is_public_host("0.0.0.0") is True


def test_is_public_host_ipv6_wildcard() -> None:
    assert _is_public_host("::") is True


def test_is_public_host_loopback_v4() -> None:
    assert _is_public_host("127.0.0.1") is False


def test_is_public_host_loopback_v6() -> None:
    assert _is_public_host("::1") is False


def test_is_public_host_private_192() -> None:
    assert _is_public_host("192.168.1.1") is False


def test_is_public_host_private_10() -> None:
    assert _is_public_host("10.0.0.1") is False


def test_is_public_host_private_172() -> None:
    assert _is_public_host("172.16.0.1") is False


def test_is_public_host_valid_hostname() -> None:
    # A hostname that resolves to 0.0.0.0 would be treated as public
    assert _is_public_host("example.com") is True


def test_safe_bind_127_0_0_1() -> None:
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        host="127.0.0.1",
    )
    assert cfg.host == "127.0.0.1"


def test_safe_bind_loopback_v6() -> None:
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        host="::1",
    )
    assert cfg.host == "::1"


def test_unsafe_bind_0000_fails_without_override() -> None:
    with pytest.raises(ValueError, match="Event Bus bound to public address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="0.0.0.0",
        )


def test_unsafe_bind_ipv6_wildcard_fails_without_override() -> None:
    with pytest.raises(ValueError, match="Event Bus bound to public address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="::",
        )


def test_unsafe_bind_0000_succeeds_with_override() -> None:
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        host="0.0.0.0",
        allow_public_bind=True,
    )
    assert cfg.host == "0.0.0.0"
    assert cfg.allow_public_bind is True


def test_private_ip_allowed_without_override() -> None:
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        host="192.168.1.1",
    )
    assert cfg.host == "192.168.1.1"
