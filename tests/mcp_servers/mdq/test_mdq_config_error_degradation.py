"""tests/mcp_servers/mdq/test_mdq_config_error_degradation.py

Regression tests for REQ-007: the single startup-configuration result raises instead of
degrading when `ConfigLoader.load()` raises a config error.

- `startup_config.load_startup_config()` raises; there is no fallback path, so a missing
  production configuration is a pre-bind failure and the message names the field path only.
- `mdq_server` and `health_check` read the result, so a missing production configuration
  raises at import, before bind: there is no empty-token fallback and no `deps["config"]`
  entry a request could report (AC-6).

The `ConfigLoader` patch targets the class attribute on the module that looks the symbol up,
so the mock is bound to exactly where the code reads it.
"""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from types import MappingProxyType
from unittest.mock import patch

import pytest
from mcp_servers.mdq import mdq_server, startup_config
from mcp_servers.mdq.health_check import _collect_dependencies
from mcp_servers.mdq.startup_config import StartupConfig
from shared.config_errors import ConfigMissingError, ConfigParseError, ConfigReadError
from shared.config_field_types import ConfigFieldTypeError
from shared.mcp_health_contract import HEALTH_REASON_SERVER_UNAVAILABLE


class TestStartupConfigPreBindFailure:
    """REQ-007, AC-6: `load_startup_config()` has no fallback path, so a missing
    production configuration raises before bind and the message names the field
    path only."""

    def test_missing_config_raises_instead_of_returning_a_fallback(self) -> None:
        with patch.object(
            startup_config.ConfigLoader,
            "load",
            side_effect=ConfigMissingError(
                "Config file not found: /opt/llm/config/mdq_mcp_server.toml"
            ),
        ):
            with pytest.raises(ConfigMissingError) as exc:
                startup_config.load_startup_config()
        message = str(exc.value)
        assert message == "config key 'mdq_mcp_server.toml' is missing"
        assert "/opt/llm" not in message

    def test_parse_error_message_names_the_field_path_only(self) -> None:
        with patch.object(
            startup_config.ConfigLoader,
            "load",
            side_effect=ConfigParseError(
                "Invalid TOML in /opt/llm/config/mdq_mcp_server.toml: illegal character"
            ),
        ):
            with pytest.raises(ConfigParseError) as exc:
                startup_config.load_startup_config()
        assert str(exc.value) == "config key 'mdq_mcp_server.toml' could not be parsed"

    def test_read_error_message_names_the_field_path_only(self) -> None:
        with patch.object(
            startup_config.ConfigLoader,
            "load",
            side_effect=ConfigReadError(
                "Cannot read config file /opt/llm/config/mdq_mcp_server.toml: Permission denied"
            ),
        ):
            with pytest.raises(ConfigReadError) as exc:
                startup_config.load_startup_config()
        assert str(exc.value) == "config key 'mdq_mcp_server.toml' could not be read"

    def test_the_loader_is_called_once(self) -> None:
        with patch.object(
            startup_config.ConfigLoader,
            "load",
            return_value={"db_path": "/tmp/x.sqlite", "auth_token": "tok"},
        ) as load:
            startup_config.load_startup_config()
        assert load.call_count == 1

    def test_the_result_is_immutable(self) -> None:
        with patch.object(
            startup_config.ConfigLoader,
            "load",
            return_value={"db_path": "/tmp/x.sqlite", "auth_token": "tok"},
        ):
            config = startup_config.load_startup_config()
        with pytest.raises(TypeError):
            config.values["db_path"] = "/tmp/other.sqlite"
        with pytest.raises(FrozenInstanceError):
            config.db_path = "/tmp/other.sqlite"

    def test_a_wrong_typed_key_names_the_field_path_without_the_value(self) -> None:
        with patch.object(
            startup_config.ConfigLoader,
            "load",
            return_value={"db_path": 123, "auth_token": "tok"},
        ):
            with pytest.raises(ConfigFieldTypeError) as exc:
                startup_config.load_startup_config()
        message = str(exc.value)
        assert "mdq_mcp_server.toml.db_path" in message
        assert "123" not in message

    def test_the_token_value_is_not_reachable_from_the_result_repr(self) -> None:
        with patch.object(
            startup_config.ConfigLoader,
            "load",
            return_value={"db_path": "/tmp/x.sqlite", "auth_token": "secret-token"},
        ):
            config = startup_config.load_startup_config()
        assert "secret-token" not in repr(config)
        assert config.auth_token == "secret-token"


class TestConsumersDoNotDegradeAConfigError:
    """The consumers no longer swallow a configuration error (REQ-007, AC-6).

    `mdq_server` authenticates from the shared result and `health_check` probes against it, so
    the failure surfaces at import rather than as a degraded health value.
    """

    def test_the_server_has_no_empty_token_fallback(self) -> None:
        assert not hasattr(mdq_server, "_load_auth_token")

    def test_health_reports_no_config_dependency(self, tmp_path) -> None:
        startup = StartupConfig(
            values=MappingProxyType({}),
            db_path=str(tmp_path / "absent.sqlite"),
            auth_token="test-token",
        )
        deps, _details, _startup, _present, _schema_error, _checked, _stats = (
            _collect_dependencies(startup)
        )
        assert "config" not in deps
        assert deps["db_file"] == HEALTH_REASON_SERVER_UNAVAILABLE
