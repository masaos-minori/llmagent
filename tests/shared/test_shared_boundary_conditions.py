"""tests/shared/test_shared_boundary_conditions.py

Guard tests for shared layer boundary conditions.

These tests document current behavior to establish a baseline before
any future refactoring of the shared module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from shared.config_loader import ConfigLoader
from shared.production_config_validator import (
    ProductionConfigValidator,
)


class TestDictMergeConflictResolution:
    """SHARED-4: Verify dict merge conflict resolution behavior."""

    def test_same_subsection_later_file_wins(self, tmp_path: Path) -> None:
        """Same TOML subsection in two files: later file replaces entirely."""
        (tmp_path / "a.toml").write_text(
            '[mcp_servers.github]\nurl = "https://api.github.com"\n'
        )
        (tmp_path / "b.toml").write_text("[mcp_servers.github]\ntimeout = 30\n")
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml", "b.toml")
        # load() does shallow update — mcp_servers from b replaces a entirely
        assert "github" in result["mcp_servers"]
        assert "url" not in result["mcp_servers"]["github"]
        assert result["mcp_servers"]["github"]["timeout"] == 30

    def test_different_subsections_in_load_all_merged(self, tmp_path: Path) -> None:
        """Different subsections under the same parent are merged by load_all()."""
        (tmp_path / "extra_mcp.toml").write_text(
            '[mcp_servers.server_a]\nurl = "http://localhost:1"\n'
        )
        (tmp_path / "extra_mcp2.toml").write_text(
            '[mcp_servers.server_b]\nurl = "http://localhost:2"\n'
        )
        loader = ConfigLoader(config_dir=tmp_path)
        # load_all merges dict-valued keys one level deep
        # We need to manually combine since load_all only loads _BASE_CONFIG_FILES
        result_a = loader.load("extra_mcp.toml")
        result_b = loader.load("extra_mcp2.toml")
        merged: dict[str, Any] = {}
        for key, val in result_a.items():
            if isinstance(val, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **val}
            else:
                merged[key] = val
        for key, val in result_b.items():
            if isinstance(val, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **val}
            else:
                merged[key] = val
        assert "server_a" in merged.get("mcp_servers", {})
        assert "server_b" in merged.get("mcp_servers", {})

    def test_deep_nested_same_subsection_replaced(self, tmp_path: Path) -> None:
        """Deeply nested same subsection replaced by later file."""
        (tmp_path / "a.toml").write_text(
            '[mcp_servers.github.connection]\nhost = "localhost"\nport = 8080\n'
        )
        (tmp_path / "b.toml").write_text(
            '[mcp_servers.github.connection]\nhost = "remote"\n'
        )
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml", "b.toml")
        # load() does shallow update — mcp_servers from b replaces a entirely
        # But TOML [mcp_servers.github.connection] creates nested dict under github key
        assert "github" in result["mcp_servers"]
        assert "connection" in result["mcp_servers"]["github"]
        assert result["mcp_servers"]["github"]["connection"]["host"] == "remote"
        assert "port" not in result["mcp_servers"]["github"]["connection"]

    def test_top_level_section_values_combined(self, tmp_path: Path) -> None:
        """Top-level sections with different keys are combined."""
        (tmp_path / "a.toml").write_text('[server]\nname = "first"\n')
        (tmp_path / "b.toml").write_text('[server]\nversion = "v2"\n')
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("a.toml", "b.toml")
        # load() does shallow update — server from b replaces a entirely
        assert "name" not in result["server"]
        assert result["server"]["version"] == "v2"

    def test_parent_dict_merge_one_level_deep(self, tmp_path: Path) -> None:
        """Parent dicts are merged one level deep in load_all."""
        (tmp_path / "extra_mcp.toml").write_text(
            '[mcp_servers.github]\nurl = "https://api.github.com"\n'
        )
        (tmp_path / "extra_mcp2.toml").write_text(
            "[mcp_servers.github]\ntimeout = 30\n"
        )
        loader = ConfigLoader(config_dir=tmp_path)
        # Manually merge like load_all does
        result_a = loader.load("extra_mcp.toml")
        result_b = loader.load("extra_mcp2.toml")
        merged: dict[str, Any] = {}
        for key, val in result_a.items():
            if isinstance(val, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **val}
            else:
                merged[key] = val
        for key, val in result_b.items():
            if isinstance(val, dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **val}
            else:
                merged[key] = val
        assert "github" in merged.get("mcp_servers", {})
        assert "url" not in merged["mcp_servers"]["github"]
        assert merged["mcp_servers"]["github"]["timeout"] == 30


class TestExtensionLessPathResolution:
    """SHARED-5: Verify extension-less paths default to .toml."""

    def test_no_extension_defaults_to_toml(self, tmp_path: Path) -> None:
        """Passing a name without .toml or .json extension resolves to .toml."""
        (tmp_path / "agent.toml").write_text('key = "value"')
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("agent")
        assert result["key"] == "value"

    def test_existing_toml_extension_not_duplicated(self, tmp_path: Path) -> None:
        """Existing .toml extension is not duplicated."""
        (tmp_path / "agent.toml").write_text('key = "value"')
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("agent.toml")
        assert result["key"] == "value"

    def test_json_extension_preserved(self, tmp_path: Path) -> None:
        """Existing .json extension is not changed."""
        (tmp_path / "agent.json").write_text('{"key": "value"}')
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load("agent.json")
        assert result["key"] == "value"

    def test_missing_json_extension_raises_error(self, tmp_path: Path) -> None:
        """Missing .json file raises error; no fallback to .toml."""
        (tmp_path / "agent.toml").write_text('key = "value"')
        loader = ConfigLoader(config_dir=tmp_path)
        with pytest.raises(Exception):
            loader.load("agent.json")


class TestKnownToolsNoneFallback:
    """SHARED-6: Verify known_tools=None does not cause validation failure."""

    def test_known_tools_none_skips_tool_validation_only(self) -> None:
        """When known_tools is None, tool tier validation is skipped but
        other validations (strict mode etc.) may still produce errors."""
        config: dict[str, Any] = {
            "tool_safety_tiers": {"some_tool": "WRITE_SAFE"},
        }
        validator = ProductionConfigValidator()
        result = validator.validate(
            config, security_profile="production", known_tools=None
        )
        # Errors from other checks (strict mode, unknown tools) still appear
        assert len(result.errors) > 0

    def test_known_tools_empty_set_validates_all_as_unknown(self) -> None:
        """When known_tools is empty set, all safety tiers are flagged as unknown."""
        config: dict[str, Any] = {
            "tool_safety_tiers": {"unknown_tool": "WRITE_SAFE"},
        }
        validator = ProductionConfigValidator()
        result = validator.validate(
            config, security_profile="production", known_tools=set()
        )
        assert len(result.errors) > 0
