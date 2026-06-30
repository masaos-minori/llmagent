"""tests/test_mcp_config.py
Unit tests for shared.mcp_config.McpServerConfig validation and _build_mcp_servers.
"""

import pytest
from shared.mcp_config import (
    HealthcheckMode,
    McpServerConfig,
    SecurityProfile,
    StartupMode,
    TransportType,
    _build_mcp_servers,
)


class TestMcpServerConfigValidation:
    def test_valid_http_config(self) -> None:
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000", [])
        assert cfg.transport == TransportType.HTTP
        assert cfg.startup_mode == StartupMode.PERSISTENT
        assert cfg.healthcheck_mode == HealthcheckMode.HTTP

    def test_valid_stdio_config(self) -> None:
        cfg = McpServerConfig(
            TransportType.STDIO, "", ["python", "server.py"], healthcheck_mode=HealthcheckMode.PROCESS
        )
        assert cfg.transport == TransportType.STDIO
        assert cfg.startup_mode == StartupMode.PERSISTENT
        assert cfg.healthcheck_mode == HealthcheckMode.PROCESS

    def test_invalid_transport_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid TransportType"):
            McpServerConfig("invalid", "", [])

    def test_http_empty_url_raises(self) -> None:
        with pytest.raises(ValueError, match="url must not be empty"):
            McpServerConfig(TransportType.HTTP, "", [])

    def test_stdio_empty_cmd_raises(self) -> None:
        with pytest.raises(ValueError, match="cmd must not be empty"):
            McpServerConfig(TransportType.STDIO, "", [])

    def test_invalid_startup_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid StartupMode"):
            McpServerConfig(
                TransportType.HTTP, "http://127.0.0.1:8000", [], startup_mode="always"
            )

    def test_invalid_healthcheck_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid HealthcheckMode"):
            McpServerConfig(
                TransportType.HTTP,
                "http://127.0.0.1:8000",
                [],
                healthcheck_mode="unknown",
            )

    def test_explicit_startup_mode_ondemand(self) -> None:
        cfg = McpServerConfig(
            TransportType.STDIO, "", ["python", "s.py"], startup_mode=StartupMode.ONDEMAND
        )
        assert cfg.startup_mode == StartupMode.ONDEMAND

    def test_explicit_healthcheck_ping_tool(self) -> None:
        cfg = McpServerConfig(
            TransportType.STDIO,
            "",
            ["python", "s.py"],
            healthcheck_mode=HealthcheckMode.PING_TOOL,
        )
        assert cfg.healthcheck_mode == HealthcheckMode.PING_TOOL

    def test_tool_names_default_empty(self) -> None:
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000", [])
        assert cfg.tool_names == []

    def test_env_default_empty_dict(self) -> None:
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000", [])
        assert cfg.env == {}

    def test_idle_timeout_default_zero(self) -> None:
        cfg = McpServerConfig(TransportType.STDIO, "", ["python", "s.py"])
        assert cfg.idle_timeout_sec == 0

    def test_ondemand_http_raises(self) -> None:
        """ondemand startup_mode with HTTP transport should raise ValueError."""
        with pytest.raises(
            ValueError, match="ondemand.*is only valid for transport='stdio'"
        ):
            McpServerConfig(
                TransportType.HTTP, "http://127.0.0.1:8000", [], startup_mode=StartupMode.ONDEMAND
            )

    def test_subprocess_stdio_raises(self) -> None:
        """subprocess startup_mode with stdio transport should raise ValueError."""
        with pytest.raises(
            ValueError, match="subprocess.*is only valid for transport='http'"
        ):
            McpServerConfig(TransportType.STDIO, "", ["python", "s.py"], startup_mode=StartupMode.SUBPROCESS)

    def test_persistent_http_valid(self) -> None:
        """persistent startup_mode with HTTP transport should be valid (regression guard)."""
        cfg = McpServerConfig(
            TransportType.HTTP, "http://127.0.0.1:8000", [], startup_mode=StartupMode.PERSISTENT
        )
        assert cfg.startup_mode == StartupMode.PERSISTENT

    def test_direct_runtime_invalid_string_raises(self) -> None:
        """Direct runtime construction with invalid strings must fail."""
        with pytest.raises(ValueError, match="not a valid TransportType"):
            McpServerConfig("invalid", "http://127.0.0.1:8000", [])

    def test_direct_runtime_invalid_startup_mode_raises(self) -> None:
        """Direct runtime construction with invalid startup_mode must fail."""
        with pytest.raises(ValueError, match="not a valid StartupMode"):
            McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000", [], startup_mode="always")

    def test_direct_runtime_invalid_healthcheck_mode_raises(self) -> None:
        """Direct runtime construction with invalid healthcheck_mode must fail."""
        with pytest.raises(ValueError, match="not a valid HealthcheckMode"):
            McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000", [], healthcheck_mode="unknown")


class TestBuildMcpServers:
    def test_empty_mcp_servers_raises_value_error(self) -> None:
        cfg = {
            "web_search_url": "http://127.0.0.1:8005",
            "github_server_url": "http://127.0.0.1:8006",
        }
        with pytest.raises(
            ValueError, match="mcp_servers config section is missing or empty"
        ):
            _build_mcp_servers(cfg)

    def test_mcp_servers_key_overrides_defaults(self) -> None:
        cfg = {
            "mcp_servers": {
                "my_server": {
                    "transport": "http",
                    "url": "http://127.0.0.1:9999",
                    "cmd": [],
                }
            }
        }
        result = _build_mcp_servers(cfg)
        assert "my_server" in result
        assert result["my_server"].url == "http://127.0.0.1:9999"

    def test_toml_string_values_parsed_from_config(self) -> None:
        """_build_mcp_servers must accept TOML string values and convert to enums."""
        cfg = {
            "mcp_servers": {
                "my_stdio": {
                    "transport": "stdio",
                    "url": "",
                    "cmd": ["python", "s.py"],
                    "startup_mode": "ondemand",
                    "healthcheck_mode": "ping_tool",
                    "idle_timeout_sec": 300,
                    "working_dir": "/tmp",
                    "env": {"FOO": "bar"},
                    "tool_names": ["my_tool"],
                }
            }
        }
        result = _build_mcp_servers(cfg)
        s = result["my_stdio"]
        assert s.transport == TransportType.STDIO
        assert s.startup_mode == StartupMode.ONDEMAND
        assert s.healthcheck_mode == HealthcheckMode.PING_TOOL
        assert s.idle_timeout_sec == 300
        assert s.working_dir == "/tmp"
        assert s.env == {"FOO": "bar"}
        assert s.tool_names == ["my_tool"]

    def test_toml_string_values_default_when_absent(self) -> None:
        """_build_mcp_servers must apply defaults for missing TOML string values."""
        cfg = {
            "mcp_servers": {
                "minimal": {
                    "transport": "http",
                    "url": "http://127.0.0.1:8000",
                    "cmd": [],
                }
            }
        }
        result = _build_mcp_servers(cfg)
        s = result["minimal"]
        assert s.transport == TransportType.HTTP
        assert s.startup_mode == StartupMode.PERSISTENT
        assert s.healthcheck_mode == HealthcheckMode.HTTP
        assert s.idle_timeout_sec == 0
        assert s.working_dir == ""
        assert s.env == {}
        assert s.tool_names == []
        assert s.auth_token == ""
        assert s.role == ""

    def test_auth_token_and_role_parsed(self) -> None:
        cfg = {
            "mcp_servers": {
                "secure": {
                    "transport": "http",
                    "url": "http://127.0.0.1:8000",
                    "cmd": [],
                    "auth_token": "my-secret",
                    "role": "file_write",
                }
            }
        }
        result = _build_mcp_servers(cfg)
        s = result["secure"]
        assert s.auth_token == "my-secret"
        assert s.role == "file_write"

    def test_auth_token_default_empty(self) -> None:
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000", [])
        assert cfg.auth_token == ""

    def test_role_default_empty(self) -> None:
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000", [])
        assert cfg.role == ""


class TestSecurityProfile:
    def test_local_value(self) -> None:
        assert SecurityProfile.LOCAL == "local"

    def test_production_value(self) -> None:
        assert SecurityProfile.PRODUCTION == "production"

    def test_invalid_value_raises(self) -> None:
        with pytest.raises(ValueError):
            SecurityProfile("invalid")

    def test_str_to_enum_local(self) -> None:
        assert SecurityProfile("local") == SecurityProfile.LOCAL

    def test_str_to_enum_production(self) -> None:
        assert SecurityProfile("production") == SecurityProfile.PRODUCTION
