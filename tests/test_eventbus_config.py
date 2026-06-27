"""tests/test_eventbus_config.py
EventBusConfig dataclass validation tests.
"""

from __future__ import annotations

import warnings

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


def test_valid_config_with_host_field() -> None:
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
    )
    assert cfg.port == 8015
    assert cfg.host == "127.0.0.1"


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


def test_no_warning_with_default_poll_interval() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            poll_interval_ms=500,
        )
        assert len(w) == 0


def test_no_warning_with_default_offset_checkpoint() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            offset_checkpoint_interval=10,
        )
        assert len(w) == 0


def test_warning_poll_interval_ms_non_default() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            poll_interval_ms=1000,
        )
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "poll_interval_ms" in str(w[0].message)


def test_warning_offset_checkpoint_interval_non_default() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            offset_checkpoint_interval=30,
        )
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "offset_checkpoint_interval" in str(w[0].message)


def test_both_warnings_when_both_non_default() -> None:
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            poll_interval_ms=1000,
            offset_checkpoint_interval=30,
        )
        assert len(w) == 2
        assert any("poll_interval_ms" in str(warn.message) for warn in w)
        assert any("offset_checkpoint_interval" in str(warn.message) for warn in w)
