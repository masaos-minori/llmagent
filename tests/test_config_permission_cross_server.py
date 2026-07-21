"""Verify ConfigLoader.restrict_to() prevents cross-server config file access."""

from __future__ import annotations

import pytest
from shared.config_errors import ConfigPermissionError
from shared.config_loader import ConfigLoader


@pytest.fixture(autouse=True)
def reset_config_loader(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reset ConfigLoader class-level allowlist after each test."""
    monkeypatch.setattr(ConfigLoader, "_allowed_files", None)


def test_cross_server_config_load_raises_config_permission_error(tmp_path) -> None:
    ConfigLoader.restrict_to("agent.toml")
    loader = ConfigLoader(config_dir=tmp_path)
    with pytest.raises(ConfigPermissionError):
        loader.load("shell_mcp_server.toml")


def test_own_config_load_allowed(tmp_path) -> None:
    agent_toml = tmp_path / "agent.toml"
    agent_toml.write_text("[agent]\n")
    ConfigLoader.restrict_to("agent.toml")
    loader = ConfigLoader(config_dir=tmp_path)
    try:
        loader.load("agent.toml")
    except ConfigPermissionError:
        pytest.fail("Own config file load raised ConfigPermissionError unexpectedly")


def test_unrestricted_allows_any_file(tmp_path) -> None:
    shell_toml = tmp_path / "shell_mcp_server.toml"
    shell_toml.write_text("[shell]\n")
    loader = ConfigLoader(config_dir=tmp_path)
    try:
        loader.load("shell_mcp_server.toml")
    except ConfigPermissionError:
        pytest.fail("Unrestricted ConfigLoader raised ConfigPermissionError")


def test_security_audit_config_blocked_in_restricted_agent_process() -> None:
    """Calling load_shell_audit_config() under restrict_to('agent.toml') raises RuntimeError."""
    ConfigLoader.restrict_to("agent.toml")
    from agent.security_audit_config import load_shell_audit_config

    with pytest.raises(RuntimeError, match="not permitted"):
        load_shell_audit_config()
