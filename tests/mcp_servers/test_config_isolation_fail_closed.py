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
