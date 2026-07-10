"""tests/test_eventbus_config.py
EventBusConfig dataclass validation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts.eventbus.config import EventBusConfig, load_config


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


def test_load_config_rejects_stray_poll_interval_ms(tmp_path: Path) -> None:
    toml_path = tmp_path / "eventbus.toml"
    toml_path.write_text(
        "port = 8015\n"
        'db_path = "/tmp/e.sqlite"\n'
        'storage_dir = "/tmp/storage"\n'
        'offsets_dir = "/tmp/offsets"\n'
        'deadletter_dir = "/tmp/deadletter"\n'
        "max_retry = 3\n"
        "poll_interval_ms = 1000\n"
    )
    with pytest.raises(ValueError, match="poll_interval_ms"):
        load_config(toml_path)


def test_load_config_rejects_stray_offset_checkpoint_interval(tmp_path: Path) -> None:
    toml_path = tmp_path / "eventbus.toml"
    toml_path.write_text(
        "port = 8015\n"
        'db_path = "/tmp/e.sqlite"\n'
        'storage_dir = "/tmp/storage"\n'
        'offsets_dir = "/tmp/offsets"\n'
        'deadletter_dir = "/tmp/deadletter"\n'
        "max_retry = 3\n"
        "offset_checkpoint_interval = 30\n"
    )
    with pytest.raises(ValueError, match="offset_checkpoint_interval"):
        load_config(toml_path)


def test_load_config_rejects_both_stray_keys(tmp_path: Path) -> None:
    toml_path = tmp_path / "eventbus.toml"
    toml_path.write_text(
        "port = 8015\n"
        'db_path = "/tmp/e.sqlite"\n'
        'storage_dir = "/tmp/storage"\n'
        'offsets_dir = "/tmp/offsets"\n'
        'deadletter_dir = "/tmp/deadletter"\n'
        "max_retry = 3\n"
        "poll_interval_ms = 1000\n"
        "offset_checkpoint_interval = 30\n"
    )
    with pytest.raises(ValueError) as exc_info:
        load_config(toml_path)
    assert "poll_interval_ms" in str(exc_info.value)
    assert "offset_checkpoint_interval" in str(exc_info.value)


def test_load_config_succeeds_without_stray_keys(tmp_path: Path) -> None:
    toml_path = tmp_path / "eventbus.toml"
    toml_path.write_text(
        "port = 8015\n"
        'db_path = "/tmp/e.sqlite"\n'
        'storage_dir = "/tmp/storage"\n'
        'offsets_dir = "/tmp/offsets"\n'
        'deadletter_dir = "/tmp/deadletter"\n'
        "max_retry = 3\n"
    )
    cfg = load_config(toml_path)
    assert cfg.port == 8015
