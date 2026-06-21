"""tests/test_mcp_config.py
Unit tests for shared.mcp_config.McpServerConfig validation and _build_mcp_servers.
"""

import pytest
from shared.mcp_config import McpServerConfig, SecurityProfile, _build_mcp_servers


class TestMcpServerConfigValidation:
    def test_valid_http_config(self) -> None:
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [])
        assert cfg.transport == "http"
        assert cfg.startup_mode == "persistent"
        assert cfg.healthcheck_mode == "http"  # auto-inferred

    def test_valid_stdio_config(self) -> None:
        cfg = McpServerConfig("stdio", "", ["python", "server.py"])
        assert cfg.transport == "stdio"
        assert cfg.startup_mode == "persistent"
        assert cfg.healthcheck_mode == "http"  # dataclass default

    def test_invalid_transport_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid TransportType"):
            McpServerConfig("invalid", "", [])

    def test_http_empty_url_raises(self) -> None:
        with pytest.raises(ValueError, match="url must not be empty"):
            McpServerConfig("http", "", [])

    def test_stdio_empty_cmd_raises(self) -> None:
        with pytest.raises(ValueError, match="cmd must not be empty"):
            McpServerConfig("stdio", "", [])

    def test_invalid_startup_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid StartupMode"):
            McpServerConfig(
                "http", "http://127.0.0.1:8000", [], startup_mode="always"
            )

    def test_invalid_healthcheck_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="not a valid HealthcheckMode"):
            McpServerConfig(
                "http",
                "http://127.0.0.1:8000",
                [],
                healthcheck_mode="unknown",
            )

    def test_explicit_startup_mode_ondemand(self) -> None:
        cfg = McpServerConfig(
            "stdio", "", ["python", "s.py"], startup_mode="ondemand"
        )
        assert cfg.startup_mode == "ondemand"

    def test_explicit_healthcheck_ping_tool(self) -> None:
        cfg = McpServerConfig(
            "stdio",
            "",
            ["python", "s.py"],
            healthcheck_mode="ping_tool",
        )
        assert cfg.healthcheck_mode == "ping_tool"

    def test_tool_names_default_empty(self) -> None:
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [])
        assert cfg.tool_names == []

    def test_env_default_empty_dict(self) -> None:
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [])
        assert cfg.env == {}

    def test_idle_timeout_default_zero(self) -> None:
        cfg = McpServerConfig("stdio", "", ["python", "s.py"])
        assert cfg.idle_timeout_sec == 0


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

    def test_new_fields_parsed_from_config(self) -> None:
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
        assert s.startup_mode == "ondemand"
        assert s.healthcheck_mode == "ping_tool"
        assert s.idle_timeout_sec == 300
        assert s.working_dir == "/tmp"
        assert s.env == {"FOO": "bar"}
        assert s.tool_names == ["my_tool"]

    def test_new_fields_default_when_absent(self) -> None:
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
        assert s.startup_mode == "persistent"
        assert s.healthcheck_mode == "http"
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
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [])
        assert cfg.auth_token == ""

    def test_role_default_empty(self) -> None:
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [])
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
