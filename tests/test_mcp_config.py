"""tests/test_mcp_config.py
Unit tests for shared.mcp_config.McpServerConfig validation and _build_mcp_servers.
"""

import pytest
from shared.mcp_config import McpServerConfig, _build_mcp_servers


class TestMcpServerConfigValidation:
    def test_valid_http_config(self) -> None:
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [], "file-mcp")
        assert cfg.transport == "http"
        assert cfg.startup_mode == "persistent"
        assert cfg.healthcheck_mode == "http"  # auto-inferred

    def test_valid_stdio_config(self) -> None:
        cfg = McpServerConfig("stdio", "", ["python", "server.py"], "")
        assert cfg.transport == "stdio"
        assert cfg.startup_mode == "persistent"
        assert cfg.healthcheck_mode == "process"  # auto-inferred

    def test_invalid_transport_raises(self) -> None:
        with pytest.raises(ValueError, match="transport must be 'http' or 'stdio'"):
            McpServerConfig("invalid", "", [], "")

    def test_http_empty_url_raises(self) -> None:
        with pytest.raises(ValueError, match="url must not be empty"):
            McpServerConfig("http", "", [], "")

    def test_stdio_empty_cmd_raises(self) -> None:
        with pytest.raises(ValueError, match="cmd must not be empty"):
            McpServerConfig("stdio", "", [], "")

    def test_invalid_startup_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="startup_mode must be"):
            McpServerConfig(
                "http", "http://127.0.0.1:8000", [], "", startup_mode="always"
            )

    def test_invalid_healthcheck_mode_raises(self) -> None:
        with pytest.raises(ValueError, match="healthcheck_mode must be"):
            McpServerConfig(
                "http",
                "http://127.0.0.1:8000",
                [],
                "",
                healthcheck_mode="unknown",
            )

    def test_explicit_startup_mode_ondemand(self) -> None:
        cfg = McpServerConfig(
            "stdio", "", ["python", "s.py"], "", startup_mode="ondemand"
        )
        assert cfg.startup_mode == "ondemand"

    def test_explicit_healthcheck_ping_tool(self) -> None:
        cfg = McpServerConfig(
            "stdio",
            "",
            ["python", "s.py"],
            "",
            healthcheck_mode="ping_tool",
        )
        assert cfg.healthcheck_mode == "ping_tool"

    def test_tool_names_default_empty(self) -> None:
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [], "")
        assert cfg.tool_names == []

    def test_env_default_empty_dict(self) -> None:
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [], "")
        assert cfg.env == {}

    def test_idle_timeout_default_zero(self) -> None:
        cfg = McpServerConfig("stdio", "", ["python", "s.py"], "")
        assert cfg.idle_timeout_sec == 0


class TestBuildMcpServers:
    def test_empty_mcp_servers_uses_legacy_fallback(self) -> None:
        cfg = {
            "web_search_url": "http://127.0.0.1:8005",
            "github_server_url": "http://127.0.0.1:8006",
        }
        result = _build_mcp_servers(cfg)
        assert "web_search" in result
        assert "github" in result

    def test_mcp_servers_key_overrides_defaults(self) -> None:
        cfg = {
            "mcp_servers": {
                "my_server": {
                    "transport": "http",
                    "url": "http://127.0.0.1:9999",
                    "cmd": [],
                    "openrc_service": "my-svc",
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
                    "openrc_service": "",
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
                    "openrc_service": "",
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
