"""tests/test_eventbus_config.py
EventBusConfig dataclass validation tests.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from eventbus.config import EventBusConfig, load_config


def test_invalid_port_too_low() -> None:
    with pytest.raises(ValueError, match="port must be 1024-65535"):
        EventBusConfig(
            port=0,
            db_path="",
            storage_dir="",
            offsets_dir="",
            deadletter_dir="",
            max_retry=3,
            auth_token="test-token",
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
            auth_token="test-token",
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
            auth_token="test-token",
        )


def test_valid_config_with_host_field() -> None:
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        auth_token="test-token",
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
        'auth_token = "test-token"\n'
        "poll_interval_ms = 1000\n"
    )
    with pytest.raises(ValueError, match="unknown key"):
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
        'auth_token = "test-token"\n'
        "offset_checkpoint_interval = 30\n"
    )
    with pytest.raises(ValueError, match="unknown key"):
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
        'auth_token = "test-token"\n'
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
        'host = "127.0.0.1"\n'
        'auth_token = "test-token"\n'
    )
    cfg = load_config(toml_path)
    assert cfg.port == 8015
    assert cfg.auth_token == "test-token"


def test_load_config_call_sites_pass_get_config_path() -> None:
    """Both call sites in eventbus/app.py must pass get_config_path()'s return value to load_config()."""
    import inspect

    import eventbus.app as eb_app

    source = inspect.getsource(eb_app)
    # Find all occurrences of load_config( — each must be followed by get_config_path()
    idx = 0
    count = 0
    while True:
        pos = source.find("load_config(", idx)
        if pos == -1:
            break
        count += 1
        # Extract the argument portion after "load_config("
        paren_start = pos + len("load_config(")
        depth = 1
        i = paren_start
        while i < len(source) and depth > 0:
            if source[i] == "(":
                depth += 1
            elif source[i] == ")":
                depth -= 1
            i += 1
        arg_text = source[paren_start : i - 1].strip()
        assert "get_config_path()" in arg_text, (
            f"Call site {count} does not pass get_config_path(): '{arg_text}'"
        )
        idx = i

    assert count >= 2, f"Expected at least 2 load_config() calls, found {count}"


def test_non_loopback_host_raises_value_error() -> None:
    """REQ-007: Regression test confirming EventBusConfig rejects non-loopback hosts."""
    # IPv4 non-loopback
    with pytest.raises(ValueError, match="non-loopback"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/test.db",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="0.0.0.0",
            auth_token="test-token",
        )

    # IPv6 non-loopback
    with pytest.raises(ValueError, match="non-loopback"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/test.db",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="::ffff:192.168.1.1",
            auth_token="test-token",
        )


def test_load_config_rejects_unknown_key(tmp_path: Path) -> None:
    """REQ-005: load_config() raises ValueError for unknown TOML keys."""
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text("""
port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
host = "127.0.0.1"
auth_token = "test-token"
unknown_key = "should-be-rejected"
""")
    with pytest.raises(ValueError, match="unknown key"):
        load_config(config_file)


def test_load_config_accepts_new_optional_keys(tmp_path: Path) -> None:
    """load_config() should accept the three new threshold keys and use them."""
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text("""
port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
host = "127.0.0.1"
auth_token = "test-token"
slow_consumer_threshold = 200
subscriber_queue_maxsize = 2000
backlog_health_threshold = 1000
""")
    cfg = load_config(config_file)
    assert cfg.slow_consumer_threshold == 200
    assert cfg.subscriber_queue_maxsize == 2000
    assert cfg.backlog_health_threshold == 1000


def test_load_config_rejects_wrong_type(tmp_path: Path) -> None:
    """REQ-005: load_config() raises ValueError for wrong-type keys."""
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text("""
port = "not-an-int"
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
host = "127.0.0.1"
auth_token = "test-token"
""")
    with pytest.raises(ValueError, match="type"):
        load_config(config_file)


def test_load_config_rejects_empty_auth_token(tmp_path: Path) -> None:
    """REQ-005: load_config() raises ValueError for empty auth_token."""
    config_file = tmp_path / "eventbus.toml"
    config_file.write_text("""
port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
host = "127.0.0.1"
auth_token = ""
""")
    with pytest.raises(ValueError, match="auth_token"):
        load_config(config_file)


def test_valid_threshold_configuration() -> None:
    """Valid thresholds should not raise during initialization."""
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        auth_token="test-token",
        slow_consumer_threshold=100,
        subscriber_queue_maxsize=1000,
        backlog_health_threshold=500,
    )
    assert cfg.slow_consumer_threshold == 100
    assert cfg.subscriber_queue_maxsize == 1000
    assert cfg.backlog_health_threshold == 500


def test_slow_consumer_threshold_equal_to_maxsize_raises() -> None:
    """slow_consumer_threshold must be strictly less than subscriber_queue_maxsize."""
    with pytest.raises(ValueError, match="slow_consumer_threshold"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            auth_token="test-token",
            slow_consumer_threshold=1000,
            subscriber_queue_maxsize=1000,
            backlog_health_threshold=500,
        )


def test_backlog_health_threshold_exceeds_maxsize_raises() -> None:
    """backlog_health_threshold must be <= subscriber_queue_maxsize."""
    with pytest.raises(ValueError, match="backlog_health_threshold"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            auth_token="test-token",
            slow_consumer_threshold=100,
            subscriber_queue_maxsize=1000,
            backlog_health_threshold=1001,
        )
