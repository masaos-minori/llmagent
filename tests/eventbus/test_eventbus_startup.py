"""tests/test_eventbus_startup.py
Event Bus startup safety guard tests for public bind detection.
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from eventbus.config import (
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
    assert _is_public_host("192.168.1.1") is True


def test_is_public_host_private_10() -> None:
    assert _is_public_host("10.0.0.1") is True


def test_is_public_host_private_172() -> None:
    assert _is_public_host("172.16.0.1") is True


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
    with pytest.raises(ValueError, match="Event Bus bound to non-loopback address"):
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
    with pytest.raises(ValueError, match="Event Bus bound to non-loopback address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="::",
        )


def test_private_ip_rejected() -> None:
    with pytest.raises(ValueError, match="Event Bus bound to non-loopback address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="192.168.1.1",
        )


def test_unsafe_bind_private_10_fails() -> None:
    with pytest.raises(ValueError, match="Event Bus bound to non-loopback address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="10.0.0.1",
        )


def test_unsafe_bind_private_172_fails() -> None:
    with pytest.raises(ValueError, match="Event Bus bound to non-loopback address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="172.16.0.1",
        )


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_main_post_start_verification_binds_loopback(tmp_path: Path) -> None:
    """Real subprocess integration test for `_main()`'s post-start socket
    verification (REQ-004): the actual bound socket is loopback, confirmed
    by connecting to it, not merely by reading the config value back."""
    port = _free_loopback_port()
    (tmp_path / "storage").mkdir()
    (tmp_path / "offsets").mkdir()
    (tmp_path / "deadletter").mkdir()
    config_path = tmp_path / "eventbus.toml"
    config_path.write_text(
        f"port = {port}\n"
        f'db_path = "{tmp_path / "eventbus.sqlite"}"\n'
        f'storage_dir = "{tmp_path / "storage"}"\n'
        f'offsets_dir = "{tmp_path / "offsets"}"\n'
        f'deadletter_dir = "{tmp_path / "deadletter"}"\n'
        f"max_retry = 3\n"
    )

    proc = subprocess.Popen(
        [sys.executable, "-m", "eventbus.app"],
        env={
            "EVENTBUS_CONFIG_PATH": str(config_path),
            "PATH": __import__("os").environ.get("PATH", ""),
        },
        cwd=str(Path(__file__).resolve().parents[2] / "scripts"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        deadline = time.monotonic() + 10.0
        connected = False
        while time.monotonic() < deadline:
            try:
                with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                    connected = True
                    break
            except OSError:
                if proc.poll() is not None:
                    break
                time.sleep(0.2)
        assert connected, (
            "eventbus subprocess did not accept a loopback connection: "
            f"{proc.stdout.read() if proc.stdout else ''}"
        )
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5.0)
