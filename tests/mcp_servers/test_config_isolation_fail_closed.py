"""tests/mcp_servers/test_config_isolation_fail_closed.py

Unit tests for Config Isolation fail-closed behavior when own_config_file is
falsy, plus the mcpdl003 dedup bootstrap in ``run_http()``: the server's own
``[dedup]`` table is validated and injected into the dispatcher before any
socket exists, and a missing table aborts startup.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from mcp_servers import dispatch as dispatch_module
from mcp_servers.dispatch import DispatchResult
from mcp_servers.server import MCPServer
from shared.config_errors import (
    ConfigMissingError,
    ConfigParseError,
    ConfigPermissionError,
)
from shared.mcp_dedup_config import _config_fingerprint, load_dedup_section

# ─────────────────────────────────────────────────────────────────────────────
# Fail-closed: falsy own_config_file raises ConfigPermissionError
# ─────────────────────────────────────────────────────────────────────────────


class _NoConfigFileServer(MCPServer):
    """Minimal server with falsy own_config_file (inherited from MCPServer base class)."""

    server_name = "no-config-test"
    server_version = "1.0"
    http_host = "127.0.0.1"
    http_port = 9999
    app_module = "noconfig:app"
    mcp_tools: list[dict[str, object]] = []

    async def dispatch(self, name: str, args: dict) -> DispatchResult:
        return DispatchResult("noop", False)


def test_falsy_own_config_file_raises_config_permission_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A falsy own_config_file causes run_http() to raise ConfigPermissionError instead of starting unrestricted."""
    import uvicorn

    def _fake_run(self: object) -> None:
        self.started = True  # type: ignore[attr-defined] — uvicorn.Server.run sets this at runtime after __init__

    monkeypatch.setattr(uvicorn.Server, "run", _fake_run)

    server = _NoConfigFileServer()
    assert server.own_config_file == ""

    with pytest.raises(
        ConfigPermissionError, match="Config Isolation: own_config_file is falsy"
    ):
        server.run_http()


# ─────────────────────────────────────────────────────────────────────────────
# Dedup bootstrap (mcpdl003 REQ-001/REQ-006)
# ─────────────────────────────────────────────────────────────────────────────


class _BootstrapProbeServer(MCPServer):
    """Minimal server whose own_config_file is set per test."""

    server_name = "bootstrap-probe"
    server_version = "1.0"
    http_host = "127.0.0.1"
    http_port = 9995
    app_module = "bootstrapprobe:app"
    mcp_tools = [
        {
            "name": "probe_write_tool",
            "description": "probe",
            "retry_policy": "same_logical_call_only",
        }
    ]

    async def dispatch(self, name: str, args: dict) -> DispatchResult:
        return DispatchResult("noop", False)


def _write_own_config(name: str, text: str) -> None:
    cfg_dir = Path(os.environ["LLMAGENT_CONFIG_DIR"])
    (cfg_dir / name).write_text(text, encoding="utf-8")


def test_missing_dedup_table_aborts_startup_before_serving(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """An own config without a [dedup] table raises ConfigMissingError before uvicorn runs."""
    import uvicorn

    reached: list[bool] = []

    def _fake_run(self: object) -> None:
        reached.append(True)

    monkeypatch.setattr(uvicorn.Server, "run", _fake_run)
    name = "bootstrap_nodedup_mcp_server.toml"
    _write_own_config(name, "# no dedup table here\nx = 1\n")
    server = _BootstrapProbeServer()
    server.own_config_file = name
    with pytest.raises(ConfigMissingError, match=r"carries no \[dedup\] table"):
        server.run_http()
    assert not reached


def test_valid_own_table_injects_dispatcher_globals(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A valid own [dedup] table opens the store and injects declared retry policies."""
    import uvicorn

    def _fake_run(self: object) -> None:
        self.started = True  # type: ignore[attr-defined] — uvicorn.Server.started set at runtime

    monkeypatch.setattr(uvicorn.Server, "run", _fake_run)
    name = "bootstrap_ok_mcp_server.toml"
    db_dir = Path(os.environ["LLMAGENT_DB_DIR"])
    _write_own_config(
        name,
        f'[dedup]\ndb_path = "{db_dir / "mcp_dedup.sqlite"}"\n',
    )
    server = _BootstrapProbeServer()
    server.own_config_file = name
    server.run_http()
    assert dispatch_module._dedup_store is not None
    assert dispatch_module._dedup_config is not None
    assert (db_dir / "mcp_dedup.sqlite").exists()
    assert dispatch_module._tool_retry_policies == {
        "probe_write_tool": "same_logical_call_only"
    }


def test_valid_optional_keys_load_and_keep_store_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A table carrying valid optional keys loads and injects with the store identity unchanged.

    Absent optional keys stay unset (REQ-007), and none of the new names is part of the config
    fingerprint, so the same table without them validates to the same values and the same
    fingerprint (owner decision D-5). Every committed config file carries none of these keys.
    """
    import uvicorn

    def _fake_run(self: object) -> None:
        self.started = True  # type: ignore[attr-defined] — uvicorn.Server.started set at runtime

    monkeypatch.setattr(uvicorn.Server, "run", _fake_run)
    name = "bootstrap_optional_keys_mcp_server.toml"
    db_dir = Path(os.environ["LLMAGENT_DB_DIR"])
    _write_own_config(
        name,
        "[dedup]\n"
        f'db_path = "{db_dir / "mcp_dedup.sqlite"}"\n'
        "max_dedup_rows = 20\n"
        "max_dedup_growth_per_hour = 100\n"
        "max_dedup_wal_mb = 64\n"
        'legal_hold_states = ["completed"]\n',
    )
    server = _BootstrapProbeServer()
    server.own_config_file = name
    server.run_http()

    config = dispatch_module._dedup_config
    assert config is not None
    assert config.max_dedup_rows == 20
    assert config.max_dedup_growth_per_hour == 100
    assert config.max_dedup_wal_mb == 64
    assert config.legal_hold_states == ("completed",)

    # The shape every committed config has today: no new key, so nothing is set.
    plain = load_dedup_section(
        {"db_path": str(db_dir / "mcp_dedup.sqlite")}, "committed_config.toml"
    )
    assert plain.max_dedup_rows is None
    assert plain.max_dedup_growth_per_hour is None
    assert plain.max_dedup_wal_mb is None
    assert plain.legal_hold_states == ()
    assert _config_fingerprint(plain) == _config_fingerprint(config)


@pytest.mark.parametrize(
    ("table", "match"),
    [
        (
            'retention_days = "two"\n',
            r"bootstrap_bad_mcp_server\.toml.*dedup\.retention_days",
        ),
        (
            "lease_seconds = true\n",
            r"bootstrap_bad_mcp_server\.toml.*dedup\.lease_seconds",
        ),
        (
            'db_path = "/elsewhere/other.sqlite"\n',
            r"bootstrap_bad_mcp_server\.toml.*canonical dedup store path",
        ),
        (
            "max_dedup_growth_per_hour = 1000001\n",
            r"bootstrap_bad_mcp_server\.toml.*dedup\.max_dedup_growth_per_hour",
        ),
        (
            'legal_hold_states = ["completed", "not_a_state"]\n',
            r"bootstrap_bad_mcp_server\.toml.*dedup\.legal_hold_states",
        ),
    ],
)
def test_invalid_own_table_aborts_startup_before_serving(
    monkeypatch: pytest.MonkeyPatch, table: str, match: str
) -> None:
    """An invalid [dedup] value names the server file and dedup.<key> and stops startup."""
    import uvicorn

    reached: list[bool] = []

    def _fake_run(self: object) -> None:
        reached.append(True)

    monkeypatch.setattr(uvicorn.Server, "run", _fake_run)
    name = "bootstrap_bad_mcp_server.toml"
    _write_own_config(name, f"[dedup]\n{table}")
    server = _BootstrapProbeServer()
    server.own_config_file = name
    with pytest.raises(ConfigParseError, match=match):
        server.run_http()
    assert not reached
