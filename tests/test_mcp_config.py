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
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000")
        assert cfg.transport == TransportType.HTTP
        assert cfg.startup_mode == StartupMode.PERSISTENT
        assert cfg.healthcheck_mode == HealthcheckMode.HTTP

    def test_http_transport_requires_url(self) -> None:
        with pytest.raises(ValueError, match="url"):
            McpServerConfig(TransportType.HTTP, "")

    def test_subprocess_http_valid(self) -> None:
        cfg = McpServerConfig(
            TransportType.HTTP, "http://localhost", startup_mode=StartupMode.SUBPROCESS
        )
        assert cfg.startup_mode == StartupMode.SUBPROCESS

    def test_invalid_transport_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid TransportType"):
            McpServerConfig("invalid", "")

    def test_http_empty_url_raises(self) -> None:
        with pytest.raises(ValueError, match="url must not be empty"):
            McpServerConfig(TransportType.HTTP, "")

    def test_invalid_startup_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid StartupMode"):
            McpServerConfig(
                TransportType.HTTP, "http://127.0.0.1:8000", startup_mode="always"
            )

    def test_startup_mode_empty_string_raises(self) -> None:
        """Empty string for startup_mode should raise ValueError."""
        with pytest.raises(ValueError):
            McpServerConfig(
                TransportType.HTTP, "http://127.0.0.1:8000", startup_mode=""
            )

    def test_invalid_healthcheck_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid HealthcheckMode"):
            McpServerConfig(
                TransportType.HTTP,
                "http://127.0.0.1:8000",
                healthcheck_mode="unknown",
            )

    def test_tool_names_default_empty(self) -> None:
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000")
        assert cfg.tool_names == []

    def test_startup_timeout_default(self) -> None:
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000")
        assert cfg.startup_timeout_sec == 30

    def test_subprocess_http_simple(self) -> None:
        """subprocess startup_mode with HTTP transport should be valid."""
        cfg = McpServerConfig(
            TransportType.HTTP,
            "http://127.0.0.1:8000",
            startup_mode=StartupMode.SUBPROCESS,
        )
        assert cfg.startup_mode == StartupMode.SUBPROCESS

    def test_persistent_http_valid(self) -> None:
        """persistent startup_mode with HTTP transport should be valid (regression guard)."""
        cfg = McpServerConfig(
            TransportType.HTTP,
            "http://127.0.0.1:8000",
            startup_mode=StartupMode.PERSISTENT,
        )
        assert cfg.startup_mode == StartupMode.PERSISTENT

    def test_direct_runtime_invalid_string_raises(self) -> None:
        """Direct runtime construction with invalid strings must fail."""
        with pytest.raises(ValueError, match="not a valid TransportType"):
            McpServerConfig("invalid", "http://127.0.0.1:8000")

    def test_direct_runtime_invalid_startup_mode_raises(self) -> None:
        """Direct runtime construction with invalid startup_mode must fail."""
        with pytest.raises(ValueError, match="not a valid StartupMode"):
            McpServerConfig(
                TransportType.HTTP, "http://127.0.0.1:8000", startup_mode="always"
            )

    def test_direct_runtime_invalid_healthcheck_mode_raises(self) -> None:
        """Direct runtime construction with invalid healthcheck_mode must fail."""
        with pytest.raises(ValueError, match="not a valid HealthcheckMode"):
            McpServerConfig(
                TransportType.HTTP, "http://127.0.0.1:8000", healthcheck_mode="unknown"
            )

    def test_stdio_transport_rejected(self) -> None:
        """transport='stdio' must be rejected as a removed enum value."""
        with pytest.raises(ValueError, match="not a valid TransportType"):
            McpServerConfig("stdio", "http://127.0.0.1:8000")

    def test_ondemand_startup_mode_rejected(self) -> None:
        """startup_mode='ondemand' must be rejected as a removed enum value."""
        with pytest.raises(ValueError, match="not a valid StartupMode"):
            McpServerConfig(
                TransportType.HTTP, "http://127.0.0.1:8000", startup_mode="ondemand"
            )

    def test_ping_tool_healthcheck_rejected(self) -> None:
        """healthcheck_mode='ping_tool' must be rejected as a removed enum value."""
        with pytest.raises(ValueError, match="not a valid HealthcheckMode"):
            McpServerConfig(
                TransportType.HTTP,
                "http://127.0.0.1:8000",
                healthcheck_mode="ping_tool",
            )


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
                }
            }
        }
        result = _build_mcp_servers(cfg)
        assert "my_server" in result
        assert result["my_server"].url == "http://127.0.0.1:9999"

    def test_toml_string_values_default_when_absent(self) -> None:
        """_build_mcp_servers must apply defaults for missing TOML string values."""
        cfg = {
            "mcp_servers": {
                "minimal": {
                    "transport": "http",
                    "url": "http://127.0.0.1:8000",
                }
            }
        }
        result = _build_mcp_servers(cfg)
        s = result["minimal"]
        assert s.transport == TransportType.HTTP
        assert s.startup_mode == StartupMode.PERSISTENT
        assert s.healthcheck_mode == HealthcheckMode.HTTP
        assert s.call_timeout_sec == 60.0
        assert s.startup_timeout_sec == 30
        assert s.tool_names == []
        assert s.auth_token == ""
        assert s.role == ""

    def test_auth_token_and_role_parsed(self) -> None:
        cfg = {
            "mcp_servers": {
                "secure": {
                    "transport": "http",
                    "url": "http://127.0.0.1:8000",
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
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000")
        assert cfg.auth_token == ""

    def test_role_default_empty(self) -> None:
        cfg = McpServerConfig(TransportType.HTTP, "http://127.0.0.1:8000")
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
