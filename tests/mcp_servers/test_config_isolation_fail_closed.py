"""tests/mcp_servers/test_config_isolation_fail_closed.py

Unit tests for Config Isolation fail-closed behavior when own_config_file is falsy.
"""

from __future__ import annotations

import pytest
from mcp_servers.dispatch import DispatchResult
from mcp_servers.server import MCPServer
from shared.config_errors import ConfigPermissionError

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
