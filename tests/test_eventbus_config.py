"""tests/test_eventbus_config.py
EventBusConfig dataclass validation tests.
"""

from __future__ import annotations

import pytest

from scripts.eventbus.config import EventBusConfig


def test_invalid_port_too_low() -> None:
    with pytest.raises(ValueError, match="port must be 1024-65535"):
        EventBusConfig(
            port=0,
            db_path="",
            storage_dir="",
            offsets_dir="",
            deadletter_dir="",
            max_retry=3,
        )


def test_invalid_port_too_high() -> None:
    with pytest.raises(ValueError, match="port must be 1024-65535"):
        EventBusConfig(
            port=70000,
            db_path="",
            storage_dir="",
            offsets_dir="",
            deadletter_dir="",
            max_retry=3,
        )


def test_invalid_max_retry_zero() -> None:
    with pytest.raises(ValueError, match="max_retry must be >= 1"):
        EventBusConfig(
            port=8015,
            db_path="",
            storage_dir="",
            offsets_dir="",
            deadletter_dir="",
            max_retry=0,
        )


def test_invalid_poll_interval_zero() -> None:
    with pytest.raises(ValueError, match="poll_interval_ms must be >= 1"):
        EventBusConfig(
            port=8015,
            db_path="",
            storage_dir="",
            offsets_dir="",
            deadletter_dir="",
            max_retry=3,
            poll_interval_ms=0,
        )


def test_invalid_offset_checkpoint_zero() -> None:
    with pytest.raises(ValueError, match="offset_checkpoint_interval must be >= 1"):
        EventBusConfig(
            port=8015,
            db_path="",
            storage_dir="",
            offsets_dir="",
            deadletter_dir="",
            max_retry=3,
            offset_checkpoint_interval=0,
        )


def test_valid_config_without_host_field() -> None:
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
    )
    assert cfg.port == 8015
    # host is not a field — this test validates no host attribute exists
    assert not hasattr(cfg, "host")


def test_valid_config_with_deprecated_defaults() -> None:
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
    )
    assert cfg.poll_interval_ms == 500
    assert cfg.offset_checkpoint_interval == 10
