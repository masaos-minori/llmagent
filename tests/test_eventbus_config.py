"""tests/test_eventbus_config.py
Event Bus configuration validation tests.
"""

from __future__ import annotations

import pytest

from eventbus.config import EventBusConfig


class TestConfigValidation:
    def test_valid_port_range(self) -> None:
        """Valid port in range [1024, 65535] should not raise."""
        cfg = EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
        )
        assert cfg.port == 8015

    def test_invalid_port_too_low(self) -> None:
        """Port below 1024 should raise ValueError."""
        with pytest.raises(ValueError, match="port must be 1024-65535"):
            EventBusConfig(
                port=80,
                db_path="/tmp/eventbus.sqlite",
                storage_dir="/tmp/storage",
                offsets_dir="/tmp/offsets",
                deadletter_dir="/tmp/deadletter",
                max_retry=3,
            )

    def test_invalid_port_too_high(self) -> None:
        """Port above 65535 should raise ValueError."""
        with pytest.raises(ValueError, match="port must be 1024-65535"):
            EventBusConfig(
                port=70000,
                db_path="/tmp/eventbus.sqlite",
                storage_dir="/tmp/storage",
                offsets_dir="/tmp/offsets",
                deadletter_dir="/tmp/deadletter",
                max_retry=3,
            )

    def test_invalid_port_zero(self) -> None:
        """Port 0 should raise ValueError."""
        with pytest.raises(ValueError, match="port must be 1024-65535"):
            EventBusConfig(
                port=0,
                db_path="/tmp/eventbus.sqlite",
                storage_dir="/tmp/storage",
                offsets_dir="/tmp/offsets",
                deadletter_dir="/tmp/deadletter",
                max_retry=3,
            )

    def test_invalid_max_retry_zero(self) -> None:
        """max_retry=0 should raise ValueError."""
        with pytest.raises(ValueError, match="max_retry must be >= 1"):
            EventBusConfig(
                port=8015,
                db_path="/tmp/eventbus.sqlite",
                storage_dir="/tmp/storage",
                offsets_dir="/tmp/offsets",
                deadletter_dir="/tmp/deadletter",
                max_retry=0,
            )

    def test_invalid_max_retry_negative(self) -> None:
        """max_retry=-1 should raise ValueError."""
        with pytest.raises(ValueError, match="max_retry must be >= 1"):
            EventBusConfig(
                port=8015,
                db_path="/tmp/eventbus.sqlite",
                storage_dir="/tmp/storage",
                offsets_dir="/tmp/offsets",
                deadletter_dir="/tmp/deadletter",
                max_retry=-1,
            )

    def test_valid_min_values(self) -> None:
        """Minimum valid values for all fields."""
        cfg = EventBusConfig(
            port=1024,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=1,
            poll_interval_ms=1,
            offset_checkpoint_interval=1,
        )
        assert cfg.port == 1024
        assert cfg.max_retry == 1
        assert cfg.poll_interval_ms == 1
        assert cfg.offset_checkpoint_interval == 1

    def test_valid_max_values(self) -> None:
        """Maximum valid port value."""
        cfg = EventBusConfig(
            port=65535,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=100,
        )
        assert cfg.port == 65535
