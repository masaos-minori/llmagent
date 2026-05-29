"""tests/test_mcp_config.py
Unit tests for shared.mcp_config.McpServerConfig validation.
"""

import pytest
from shared.mcp_config import McpServerConfig, _build_mcp_servers


class TestMcpServerConfigValidation:
    def test_valid_http_config(self) -> None:
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [], "file-mcp")
        assert cfg.transport == "http"

    def test_valid_stdio_config(self) -> None:
        cfg = McpServerConfig("stdio", "", ["python", "server.py"], "")
        assert cfg.transport == "stdio"

    def test_invalid_transport_raises(self) -> None:
        with pytest.raises(ValueError, match="transport must be 'http' or 'stdio'"):
            McpServerConfig("invalid", "", [], "")

    def test_http_empty_url_raises(self) -> None:
        with pytest.raises(ValueError, match="url must not be empty"):
            McpServerConfig("http", "", [], "")

    def test_stdio_empty_cmd_raises(self) -> None:
        with pytest.raises(ValueError, match="cmd must not be empty"):
            McpServerConfig("stdio", "", [], "")


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
