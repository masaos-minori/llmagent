"""tests/test_eventbus_startup.py
Event Bus startup safety guard tests for public bind detection.
"""

from __future__ import annotations

import json
import socket
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
from db.schema_sql import build_eventbus_schema_sql, eventbus_schema_version
from eventbus.config import (
    EventBusConfig,
    _is_public_host,
)
from eventbus.db_conn import open_db


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
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        host="127.0.0.1",
        auth_token="test-token",
    )
    assert cfg.host == "127.0.0.1"


def test_safe_bind_loopback_v6() -> None:
    cfg = EventBusConfig(
        port=8015,
        db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage",
        deadletter_dir="/tmp/deadletter",
        max_retry=3,
        host="::1",
        auth_token="test-token",
    )
    assert cfg.host == "::1"


def test_unsafe_bind_0000_fails_without_override() -> None:
    with pytest.raises(ValueError, match="Event Bus bound to non-loopback address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="0.0.0.0",
            auth_token="test-token",
        )


def test_unsafe_bind_ipv6_wildcard_fails_without_override() -> None:
    with pytest.raises(ValueError, match="Event Bus bound to non-loopback address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="::",
            auth_token="test-token",
        )


def test_private_ip_rejected() -> None:
    with pytest.raises(ValueError, match="Event Bus bound to non-loopback address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="192.168.1.1",
            auth_token="test-token",
        )


def test_unsafe_bind_private_10_fails() -> None:
    with pytest.raises(ValueError, match="Event Bus bound to non-loopback address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="10.0.0.1",
            auth_token="test-token",
        )


def test_unsafe_bind_private_172_fails() -> None:
    with pytest.raises(ValueError, match="Event Bus bound to non-loopback address"):
        EventBusConfig(
            port=8015,
            db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage",
            deadletter_dir="/tmp/deadletter",
            max_retry=3,
            host="172.16.0.1",
            auth_token="test-token",
        )


def _free_loopback_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def test_main_post_start_verification_binds_loopback(tmp_path: Path) -> None:
    """Real subprocess integration test for `_main()`'s post-start socket
    verification (ADR-013 INV-06): the actual bound socket is loopback, confirmed
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
        f'deadletter_dir = "{tmp_path / "deadletter"}"\n'
        f"max_retry = 3\n"
        f'host = "127.0.0.1"\n'
        f'auth_token = "test-token"\n'
    )

    proc = subprocess.Popen(
        [sys.executable, "-m", "eventbus.app"],
        env={
            "EVENTBUS_CONFIG_PATH": str(config_path),
            "EVENTBUS_SCHEMA_PATH": __import__("os").environ["EVENTBUS_SCHEMA_PATH"],
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


def test_main_failing_lifespan_exits_without_attributeerror(tmp_path: Path) -> None:
    """Real subprocess integration test for a failing Event Bus lifespan: with a
    missing envelope schema the uvicorn lifespan fails at the schema read, so
    `_main()`'s post-start override must return cleanly instead of raising a
    secondary `AttributeError` for the missing `self.servers`. Asserts both halves
    of the contract: the real cause is logged and no `AttributeError` surfaces,
    and the process still exits non-zero."""
    port = _free_loopback_port()
    config_path = tmp_path / "eventbus.toml"
    config_path.write_text(
        f"port = {port}\n"
        f'db_path = "{tmp_path / "eventbus.sqlite"}"\n'
        f'storage_dir = "{tmp_path / "storage"}"\n'
        f'deadletter_dir = "{tmp_path / "deadletter"}"\n'
        f"max_retry = 3\n"
        f'host = "127.0.0.1"\n'
        f'auth_token = "test-token"\n'
    )
    missing_schema = tmp_path / "missing_schema.json"  # intentionally never created

    proc = subprocess.Popen(
        [sys.executable, "-m", "eventbus.app"],
        env={
            "EVENTBUS_CONFIG_PATH": str(config_path),
            "EVENTBUS_SCHEMA_PATH": str(missing_schema),
            "PATH": __import__("os").environ.get("PATH", ""),
        },
        cwd=str(Path(__file__).resolve().parents[2] / "scripts"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        proc.wait(timeout=20.0)
        output = proc.stdout.read() if proc.stdout else ""
        assert "Application startup failed. Exiting." in output, output
        assert "AttributeError" not in output, output
        assert proc.returncode != 0, output
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5.0)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5.0)


# ── Startup schema shape gate (a matching version stamp alone is refused) ──


def _stamped_database(tmp_path: Path, name: str, ddl: str) -> Path:
    """Build a database from ddl and stamp it with the current schema version."""
    path = tmp_path / name
    conn = sqlite3.connect(path)
    conn.executescript(ddl)
    conn.execute(f"PRAGMA user_version = {eventbus_schema_version()}")
    conn.commit()
    conn.close()
    return path


def test_canonical_stamped_database_passes_the_startup_shape_gate(
    tmp_path: Path,
) -> None:
    """A canonical database reopened with a matching stamp passes the shape gate."""
    path = tmp_path / "eventbus.sqlite"
    open_db(str(path)).close()  # creates the canonical schema and stamps it
    open_db(str(path)).close()  # found == expected: the shared fingerprint check runs
    conn = sqlite3.connect(path)
    version = int(conn.execute("PRAGMA user_version").fetchone()[0])
    conn.close()
    assert version == eventbus_schema_version()


def test_malformed_stamped_database_missing_index_is_refused(tmp_path: Path) -> None:
    """A database stamped with the current version but missing a required index is
    refused at open_db: the stamp alone does not prove the shape."""
    ddl = build_eventbus_schema_sql().replace(
        "CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);", ""
    )
    path = _stamped_database(tmp_path, "eventbus_missing_index.sqlite", ddl)
    with pytest.raises(RuntimeError, match="indexes differ"):
        open_db(str(path))


def test_malformed_stamped_database_changed_nullability_is_refused(
    tmp_path: Path,
) -> None:
    """A stamped database whose column nullability deviates from schema.sql is refused."""
    ddl = build_eventbus_schema_sql().replace(
        "    topic                  TEXT    NOT NULL,",
        "    topic                  TEXT,",
    )
    path = _stamped_database(tmp_path, "eventbus_nullable.sqlite", ddl)
    with pytest.raises(RuntimeError, match="columns differ"):
        open_db(str(path))


# ── Real-subprocess startup gate tests (startup failure and readiness) ──


def _launch_eventbus_subprocess(config_path: Path) -> subprocess.Popen[str]:
    """Launch the real `_main()` with the same harness as the loopback tests."""
    return subprocess.Popen(
        [sys.executable, "-m", "eventbus.app"],
        env={
            "EVENTBUS_CONFIG_PATH": str(config_path),
            "EVENTBUS_SCHEMA_PATH": __import__("os").environ["EVENTBUS_SCHEMA_PATH"],
            "PATH": __import__("os").environ.get("PATH", ""),
        },
        cwd=str(Path(__file__).resolve().parents[2] / "scripts"),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def _terminate_eventbus_subprocess(proc: subprocess.Popen[str]) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=5.0)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5.0)


def _write_subprocess_config(
    tmp_path: Path, *, port: int, db_path: Path, config_name: str = "eventbus.toml"
) -> Path:
    (tmp_path / "storage").mkdir(exist_ok=True)
    (tmp_path / "deadletter").mkdir(exist_ok=True)
    config_path = tmp_path / config_name
    config_path.write_text(
        f"port = {port}\n"
        f'db_path = "{db_path}"\n'
        f'storage_dir = "{tmp_path / "storage"}"\n'
        f'deadletter_dir = "{tmp_path / "deadletter"}"\n'
        f"max_retry = 3\n"
        f'host = "127.0.0.1"\n'
        f'auth_token = "test-token"\n'
    )
    return config_path


def test_main_malformed_stamped_db_rejected_at_startup(tmp_path: Path) -> None:
    """A correctly-stamped-but-malformed database must fail the real lifespan:
    the subprocess exits non-zero with the startup-failure output."""
    port = _free_loopback_port()
    ddl = build_eventbus_schema_sql().replace(
        "CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);", ""
    )
    db_path = _stamped_database(tmp_path, "eventbus_malformed.sqlite", ddl)
    config_path = _write_subprocess_config(tmp_path, port=port, db_path=db_path)

    proc = _launch_eventbus_subprocess(config_path)
    try:
        proc.wait(timeout=20.0)
        output = proc.stdout.read() if proc.stdout else ""
        assert "Application startup failed. Exiting." in output, output
        assert proc.returncode != 0, output
    finally:
        _terminate_eventbus_subprocess(proc)


def test_main_canonical_db_passes_readiness_gate(tmp_path: Path) -> None:
    """A canonical database reaches the provisional readiness signal via the real
    /health body: db == ok AND dlq_task == running. The HTTP status is not
    asserted, mirroring the deploy gate's capacity-only 503 tolerance."""
    port = _free_loopback_port()
    db_path = tmp_path / "eventbus.sqlite"
    open_db(str(db_path)).close()  # canonical schema, stamped
    config_path = _write_subprocess_config(tmp_path, port=port, db_path=db_path)

    proc = _launch_eventbus_subprocess(config_path)
    try:
        deadline = time.monotonic() + 15.0
        health: dict[str, object] | None = None
        while time.monotonic() < deadline:
            if proc.poll() is not None:
                break
            try:
                request = urllib.request.Request(
                    f"http://127.0.0.1:{port}/health",
                    headers={"Authorization": "Bearer test-token"},
                )
                with urllib.request.urlopen(request, timeout=2) as response:
                    health = json.loads(response.read())
                break
            except urllib.error.HTTPError as exc:  # 503: read the body anyway
                health = json.loads(exc.read())
                break
            except OSError:
                time.sleep(0.2)
        assert health is not None, (
            "eventbus subprocess never served /health: "
            f"{proc.stdout.read() if proc.stdout else ''}"
        )
        assert health["db"] == "ok", health
        assert health["dlq_task"] == "running", health
    finally:
        _terminate_eventbus_subprocess(proc)
