"""tests/mcp_servers/mdq/test_mdq_config_error_degradation.py

Regression tests for REQ-004: both missing-config callers degrade instead of raising
when `ConfigLoader.load()` raises `ConfigMissingError`.

- `mdq_server._load_auth_token()` returns "" (fail-closed) on `ConfigMissingError`.
- `health_check._collect_dependencies()` records the error under `deps["config"]` and
  returns without raising.

The two callers bind `ConfigLoader` via a module-level `from shared.config_loader import
ConfigLoader`, so the patch targets the class attribute on the *under-test* module
(`mdq_server.ConfigLoader` / `health_check.ConfigLoader`) rather than the origin module.
That keeps the mock bound to exactly where the code looks the symbol up.
"""

from __future__ import annotations

from unittest.mock import patch

from mcp_servers.mdq import health_check, mdq_server
from mcp_servers.mdq.health_check import _collect_dependencies
from shared.config_errors import ConfigMissingError


class TestConfigErrorDegradation:
    def test_load_auth_token_returns_empty_on_config_missing_error(self) -> None:
        with patch.object(
            mdq_server.ConfigLoader,
            "load",
            side_effect=ConfigMissingError("no such toml"),
        ):
            assert mdq_server._load_auth_token() == ""

    def test_collect_dependencies_records_config_error(self) -> None:
        with patch.object(
            health_check.ConfigLoader,
            "load",
            side_effect=ConfigMissingError("no such toml"),
        ):
            deps, _details, mdq_cfg, *_rest = _collect_dependencies()
        assert "config" in deps
        assert deps["config"].startswith("check failed:")
        assert mdq_cfg == {}
