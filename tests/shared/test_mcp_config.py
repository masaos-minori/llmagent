"""tests/test_mcp_config.py
Unit tests for shared.mcp_config.McpServerConfig validation and _build_mcp_servers.

The parser half of this file pins the strict type rules the MCP table shares with the
startup builders and the reload path (REQ-001), including the inputs the reload path used
to accept, and pins that a raised message names the server key and the field but never the
value, because auth_token and env carry credentials (REQ-011).
"""

from typing import Any

import pytest
from shared.mcp_config import (
    McpServerConfig,
    StartupMode,
    TransportType,
    _build_mcp_servers,
    _build_single_server,
)

# One valid server table that every rejection case below varies by one field.
_BASE_SERVER: dict[str, Any] = {
    "transport": "http",
    "url": "http://127.0.0.1:8000",
    "auth_token": "test-token",
}


def _server(**overrides: Any) -> dict[str, Any]:
    return {**_BASE_SERVER, **overrides}


class SecretRepr:
    """A wrong-typed value whose repr carries a secret, proving repr is never used."""

    def __repr__(self) -> str:
        return "<hunter2-token>"


class TestMcpServerConfigValidation:
    def test_valid_http_config(self) -> None:
        cfg = McpServerConfig(
            TransportType.HTTP, "http://127.0.0.1:8000", auth_token="test-token"
        )
        assert cfg.transport == TransportType.HTTP
        assert cfg.startup_mode == StartupMode.NONE

    def test_http_transport_requires_url(self) -> None:
        with pytest.raises(ValueError, match="url"):
            McpServerConfig(TransportType.HTTP, "")

    def test_subprocess_http_valid(self) -> None:
        cfg = McpServerConfig(
            TransportType.HTTP,
            "http://localhost",
            startup_mode=StartupMode.SUBPROCESS,
            cmd=["server.py"],
            auth_token="test-token",
        )
        assert cfg.startup_mode == StartupMode.SUBPROCESS

    def test_subprocess_non_required_rejected(self) -> None:
        with pytest.raises(ValueError, match="ADR-004 Exceptions"):
            McpServerConfig(
                TransportType.HTTP,
                "http://localhost",
                startup_mode=StartupMode.SUBPROCESS,
                cmd=["server.py"],
                auth_token="test-token",
                required=False,
            )

    def test_persistent_non_required_allowed(self) -> None:
        cfg = McpServerConfig(
            TransportType.HTTP,
            "http://localhost",
            startup_mode=StartupMode.PERSISTENT,
            auth_token="test-token",
            required=False,
        )
        assert cfg.required is False

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

    def test_startup_timeout_default(self) -> None:
        cfg = McpServerConfig(
            TransportType.HTTP, "http://127.0.0.1:8000", auth_token="test-token"
        )
        assert cfg.startup_timeout_sec == 30

    def test_subprocess_http_simple(self) -> None:
        """subprocess startup_mode with HTTP transport should be valid."""
        cfg = McpServerConfig(
            TransportType.HTTP,
            "http://127.0.0.1:8000",
            startup_mode=StartupMode.SUBPROCESS,
            cmd=["server.py"],
            auth_token="test-token",
        )
        assert cfg.startup_mode == StartupMode.SUBPROCESS

    def test_persistent_http_valid(self) -> None:
        """persistent startup_mode with HTTP transport should be valid (regression guard)."""
        cfg = McpServerConfig(
            TransportType.HTTP,
            "http://127.0.0.1:8000",
            startup_mode=StartupMode.PERSISTENT,
            auth_token="test-token",
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
                    "auth_token": "test-token",
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
                    "auth_token": "test-token",
                }
            }
        }
        result = _build_mcp_servers(cfg)
        s = result["minimal"]
        assert s.transport == TransportType.HTTP
        assert s.startup_mode == StartupMode.NONE
        assert s.call_timeout_sec == 60.0
        assert s.startup_timeout_sec == 30
        assert s.role == ""
        assert s.control_auth_token == ""

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

    def test_control_auth_token_resolves_tolerantly(self, monkeypatch) -> None:
        """mcpdl004 REQ-002: a resolved ${ENV:...} control token is used, and an unset
        variable leaves it empty (control closed) instead of stopping the Agent."""
        monkeypatch.setenv("MCP_TEST_CONTROL_TOKEN", "control-secret")
        cfg = {
            "mcp_servers": {
                "ctrl": {
                    "transport": "http",
                    "url": "http://127.0.0.1:8000",
                    "auth_token": "test-token",
                    "control_auth_token": "${ENV:MCP_TEST_CONTROL_TOKEN}",
                }
            }
        }
        result = _build_mcp_servers(cfg)
        assert result["ctrl"].control_auth_token == "control-secret"

        cfg["mcp_servers"]["ctrl"]["control_auth_token"] = "${ENV:MCP_UNSET_TEST_TOKEN}"
        monkeypatch.delenv("MCP_UNSET_TEST_TOKEN", raising=False)
        result = _build_mcp_servers(cfg)
        assert result["ctrl"].control_auth_token == ""

    def test_auth_token_default_empty_raises(self) -> None:
        """mcpauth: an empty auth_token is no longer a valid default for enabled servers (REQ-004)."""
        with pytest.raises(ValueError, match="auth_token must not be empty"):
            McpServerConfig(
                TransportType.HTTP,
                "http://127.0.0.1:8000",
                startup_mode=StartupMode.PERSISTENT,
            )

    def test_role_default_empty(self) -> None:
        cfg = McpServerConfig(
            TransportType.HTTP, "http://127.0.0.1:8000", auth_token="test-token"
        )
        assert cfg.role == ""

    def test_subprocess_http_with_cmd_env_parsed(self) -> None:
        """subprocess startup_mode with cmd and env must be parsed from TOML dict."""
        cfg = {
            "mcp_servers": {
                "srv": {
                    "transport": "http",
                    "url": "http://127.0.0.1:8000",
                    "startup_mode": "subprocess",
                    "cmd": ["python3", "server.py"],
                    "env": {"PORT": "9000"},
                    "auth_token": "test-token",
                }
            }
        }
        result = _build_mcp_servers(cfg)
        s = result["srv"]
        assert s.startup_mode == StartupMode.SUBPROCESS
        assert s.cmd == ["python3", "server.py"]
        assert s.env == {"PORT": "9000"}

    def test_subprocess_without_cmd_raises(self) -> None:
        """subprocess startup_mode without cmd key must raise ValueError."""
        cfg = {
            "mcp_servers": {
                "srv": {
                    "transport": "http",
                    "url": "http://127.0.0.1:8000",
                    "startup_mode": "subprocess",
                }
            }
        }
        with pytest.raises(ValueError, match="cmd must not be empty"):
            _build_mcp_servers(cfg)

    def test_unsupported_transport_raises_from_toml(self) -> None:
        """transport='stdio' in TOML dict must raise ValueError after enum removal."""
        cfg = {
            "mcp_servers": {
                "srv": {
                    "transport": "stdio",
                    "url": "http://127.0.0.1:8000",
                }
            }
        }
        with pytest.raises(ValueError):
            _build_mcp_servers(cfg)

    def test_unsupported_startup_mode_raises_from_toml(self) -> None:
        """startup_mode='ondemand' in TOML dict must raise ValueError after enum removal."""
        cfg = {
            "mcp_servers": {
                "srv": {
                    "transport": "http",
                    "url": "http://127.0.0.1:8000",
                    "startup_mode": "ondemand",
                }
            }
        }
        with pytest.raises(ValueError):
            _build_mcp_servers(cfg)


class TestRequiredDefault:
    def test_required_default_true_on_direct_construction(self) -> None:
        cfg = McpServerConfig(
            TransportType.HTTP, "http://127.0.0.1:8000", auth_token="test-token"
        )
        assert cfg.required is True

    def test_required_default_true_from_toml_absent_key(self) -> None:
        """_build_mcp_servers must apply True default when 'required' TOML key is absent."""
        cfg = {
            "mcp_servers": {
                "minimal": {
                    "transport": "http",
                    "url": "http://127.0.0.1:8000",
                    "auth_token": "test-token",
                }
            }
        }
        result = _build_mcp_servers(cfg)
        s = result["minimal"]
        assert s.required is True

    def test_required_default_reflects_adr004_inv14(self) -> None:
        """ADR-004 Decision #12/INV-14: unspecified criticality must default to required.

        An undefined/undeterminable component criticality must never be assumed
        non-required; the safe default is `required=True`.
        """
        cfg = McpServerConfig(
            TransportType.HTTP, "http://127.0.0.1:8000", auth_token="test-token"
        )
        assert cfg.required is True


def test_valid_string_transport_rejected() -> None:
    """'http' is a valid transport string value but not a TransportType instance — must be rejected."""
    with pytest.raises(ValueError):
        McpServerConfig("http", "http://127.0.0.1:8000")


class TestAuthHeaders:
    """McpServerConfig.auth_headers() builds the Bearer header used by health probes."""

    def _cfg(self, token: str) -> McpServerConfig:
        return McpServerConfig(
            transport=TransportType.HTTP,
            url="http://localhost:8080",
            startup_mode=StartupMode.PERSISTENT,
            auth_token=token,
        )

    def test_returns_bearer_header_for_non_empty_token(self) -> None:
        assert self._cfg("s3cret").auth_headers() == {"Authorization": "Bearer s3cret"}

    def test_returns_empty_dict_for_empty_token(self) -> None:
        cfg = self._cfg("placeholder")
        cfg.auth_token = (
            ""  # bypass __post_init__ validation, which rejects "" at construction
        )
        assert cfg.auth_headers() == {}


# ── Strict parsing of the MCP table (REQ-001, REQ-011) ────────────────────────


class TestMcpParserRejectsNewlyRejectedInputs:
    """Every input the Plan lists as newly rejected is rejected by the MCP parser."""

    @pytest.mark.parametrize(
        ("key", "value", "expected"),
        [
            # cmd: a list of non-empty strings, never a split string.
            ("cmd", "python3", "must be list, got str"),
            ("cmd", [], "must not be empty"),
            ("cmd", ["python3", ""], r"cmd\[1\].*must not be empty"),
            ("cmd", {"arg": 1}, "must be list, got dict"),
            # required: a bool, never a TOML-looking string or number.
            ("required", "false", "must be bool, got str"),
            ("required", "true", "must be bool, got str"),
            ("required", 0, "must be bool, got int"),
            ("required", 1, "must be bool, got int"),
            # Integer fields: a string or a bool is not an int.
            ("startup_timeout_sec", "30", "must be int, got str"),
            ("startup_timeout_sec", True, "must be int, got bool"),
            ("max_stderr_log_files", "3", "must be int, got str"),
            ("max_stderr_log_files", False, "must be int, got bool"),
            # Float fields: a bool is not a number.
            ("call_timeout_sec", True, "must be float, got bool"),
            ("startup_stagger_delay_sec", False, "must be float, got bool"),
            ("max_stderr_log_size_mb", True, "must be float, got bool"),
            ("max_stderr_log_size_mb", "100", "must be float, got str"),
            # String fields: a number is not a string.
            ("role", 7, "must be str, got int"),
            ("url", 7, "must be str, got int"),
            ("transport", 7, "must be str, got int"),
            # env: dict[str, str].
            ("env", {"PORT": 9000}, r"env\['PORT'\].*must be str"),
            ("env", {9000: "PORT"}, "must be str"),
            ("env", ["PORT"], "must be dict, got list"),
        ],
    )
    def test_value_is_rejected_naming_the_field(
        self, key: str, value: Any, expected: str
    ) -> None:
        with pytest.raises(ValueError, match=expected) as excinfo:
            _build_single_server("srv", _server(**{key: value}))
        assert f"mcp_servers.srv.{key}" in str(excinfo.value)

    @pytest.mark.parametrize("key", ["enabled", "auto_start", "fields", "cmd_extra"])
    def test_unknown_key_is_rejected_by_name(self, key: str) -> None:
        # enabled and auto_start are not McpServerConfig fields and the parser never read
        # them: they are rejected as unknown keys, not type-checked.
        with pytest.raises(ValueError, match=f"unknown config key {key!r}") as excinfo:
            _build_single_server("srv", _server(**{key: True}))
        message = str(excinfo.value)
        assert "mcp_servers.srv" in message
        assert excinfo.value.field_path == f"mcp_servers.srv.{key}"

    def test_a_number_url_no_longer_fails_inside_urlparse(self) -> None:
        # Today url=7 reaches urlparse and fails as an AttributeError; the shared rule
        # rejects it as a type error before any parsing happens.
        with pytest.raises(ValueError, match="must be str") as excinfo:
            _build_single_server("srv", _server(url=7))
        assert "AttributeError" not in str(excinfo.value)

    @pytest.mark.parametrize(
        ("key", "value"),
        [
            ("auth_token", 7),
            ("control_auth_token", 7),
            ("call_timeout_sec", "60"),
            ("health_timeout", "5"),
            ("role", 7),
        ],
    )
    def test_the_rejected_value_is_not_in_the_message(
        self, key: str, value: Any
    ) -> None:
        class SecretValue:
            def __repr__(self) -> str:
                return "<hunter2-token>"

        with pytest.raises(ValueError) as excinfo:
            _build_single_server("srv", _server(**{key: SecretValue()}))
        assert "hunter2" not in str(excinfo.value)

    def test_an_env_value_is_not_in_the_message(self) -> None:
        with pytest.raises(ValueError, match="must be str") as excinfo:
            _build_single_server("srv", _server(env={"TOKEN": SecretRepr()}))
        assert "hunter2" not in str(excinfo.value)

    def test_the_server_key_qualifies_every_field_error(self) -> None:
        with pytest.raises(ValueError, match="mcp_servers.other_srv.call_timeout_sec"):
            _build_single_server("other_srv", _server(call_timeout_sec="60"))


class TestMcpParserKeepsAcceptedInputs:
    """The strict parser still accepts what the deployed configuration contains."""

    def test_absent_keys_take_the_defaults(self) -> None:
        cfg = _build_single_server("srv", _server())
        assert cfg.transport == TransportType.HTTP
        assert cfg.startup_mode == StartupMode.NONE
        assert cfg.call_timeout_sec == 60.0
        assert cfg.health_timeout is None
        assert cfg.startup_timeout_sec == 30
        assert cfg.startup_stagger_delay_sec == 0.0
        assert cfg.max_stderr_log_size_mb == 100.0
        assert cfg.max_stderr_log_files == 3
        assert cfg.role == ""
        assert cfg.cmd == []
        assert cfg.env == {}
        assert cfg.required is True

    def test_an_explicit_null_health_timeout_is_accepted(self) -> None:
        assert (
            _build_single_server("srv", _server(health_timeout=None)).health_timeout
            is None
        )

    def test_an_int_is_accepted_by_a_float_field_and_widened(self) -> None:
        cfg = _build_single_server("srv", _server(call_timeout_sec=60))
        assert cfg.call_timeout_sec == 60.0
        assert isinstance(cfg.call_timeout_sec, float)

    def test_an_empty_env_table_is_accepted(self) -> None:
        assert _build_single_server("srv", _server(env={})).env == {}

    def test_a_full_subprocess_table_is_accepted(self) -> None:
        cfg = _build_single_server(
            "srv",
            _server(
                startup_mode="subprocess",
                cmd=["/opt/llm/bin/mcp_shell"],
                env={"PORT": "8009"},
                required=True,
                call_timeout_sec=60.0,
                startup_timeout_sec=30,
                startup_stagger_delay_sec=0.5,
                max_stderr_log_size_mb=100.0,
                max_stderr_log_files=3,
                role="execute",
            ),
        )
        assert cfg.startup_mode == StartupMode.SUBPROCESS
        assert cfg.cmd == ["/opt/llm/bin/mcp_shell"]
        assert cfg.env == {"PORT": "8009"}

    def test_the_shipped_configuration_parses_under_the_strict_rules(self) -> None:
        # The strict parser must still accept every [mcp_servers.<key>] table the repository
        # ships, which is the UNK-01 check for the MCP half of the newly rejected list.
        from pathlib import Path

        from shared.config_loader import ConfigLoader

        config_dir = Path(__file__).resolve().parents[2] / "config"
        cfg = ConfigLoader(config_dir=config_dir).load_all()
        servers = _build_mcp_servers(cfg)
        assert servers, "the shipped configuration must parse into at least one server"
