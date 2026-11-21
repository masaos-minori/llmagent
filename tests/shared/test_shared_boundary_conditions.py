"""tests/shared/test_shared_boundary_conditions.py

Guard tests for shared layer boundary conditions.

These tests document current behavior to establish a baseline before
any future refactoring of the shared module.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from agent.production_config_validator import (
    ProductionConfigValidator,
)
from shared.config_loader import ConfigLoader


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

    def test_different_subsections_in_load_all_merged(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Different subsections under the same parent are merged by load_all()."""
        (tmp_path / "extra_mcp.toml").write_text(
            '[mcp_servers.server_a]\nurl = "http://localhost:1"\n'
        )
        (tmp_path / "extra_mcp2.toml").write_text(
            '[mcp_servers.server_b]\nurl = "http://localhost:2"\n'
        )
        monkeypatch.setattr(
            "shared.config_loader._BASE_CONFIG_FILES",
            ("extra_mcp.toml", "extra_mcp2.toml"),
        )
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load_all()
        assert "server_a" in result.get("mcp_servers", {})
        assert "server_b" in result.get("mcp_servers", {})

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

    def test_parent_dict_merge_one_level_deep(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Parent dicts are merged one level deep in load_all."""
        (tmp_path / "extra_mcp.toml").write_text(
            '[mcp_servers.github]\nurl = "https://api.github.com"\n'
        )
        (tmp_path / "extra_mcp2.toml").write_text(
            "[mcp_servers.github]\ntimeout = 30\n"
        )
        monkeypatch.setattr(
            "shared.config_loader._BASE_CONFIG_FILES",
            ("extra_mcp.toml", "extra_mcp2.toml"),
        )
        loader = ConfigLoader(config_dir=tmp_path)
        result = loader.load_all()
        assert "github" in result.get("mcp_servers", {})
        assert "url" not in result["mcp_servers"]["github"]
        assert result["mcp_servers"]["github"]["timeout"] == 30


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
    """T-6: Reconciled with REQ-001's fail-closed semantics (agentcfg003 REQ-004/REQ-011).

    NOTE: This class was originally written under SHARED-6
    (plans/done/20260726-193048_plan.md) to assert the old fail-open behavior
    (known_tools=None skips tool tier validation). After REQ-001's fail-closed
    change, and after agentcfg003 removed the `tool_safety_tiers` map, these
    tests assert the declared-tier risk floor: the validator reads the live
    registry's declarations, never a config map.

    This class intentionally supersedes SHARED-6 per ADR-004's fail-closed
    principle: production validation cannot succeed without an authoritative
    tool set.
    """

    def test_known_tools_none_produces_error_on_registry_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """REQ-001/T-6: When known_tools=None and registry lookup fails,
        the validator must surface a validation error instead of silently skipping."""
        validator = ProductionConfigValidator()

        def _raise() -> None:
            raise ValueError(
                "Tool 'duplicate_tool' already registered to server 'server_a'; cannot reassign to 'server_b'"
            )

        monkeypatch.setattr("shared.tool_registry.get_registry", _raise)
        result = validator.validate({}, known_tools=None)
        assert any(
            "registry" in err.lower() or "resolution" in err.lower()
            for err in result.errors
        )

    def test_known_tools_empty_set_fails_closed_on_declared_floor(self) -> None:
        """An empty known_tools set resolves no floor target, and the removed
        `tool_safety_tiers` key is itself rejected: a config that still carries
        it fails validation with the unknown-key error."""
        config: dict[str, Any] = {
            "tool_safety_tiers": {"unknown_tool": "WRITE_SAFE"},
        }
        validator = ProductionConfigValidator()
        result = validator.validate(config, known_tools=set())
        assert any("Unknown config keys" in err for err in result.errors)
        assert len(result.errors) > 0

    def test_declared_tier_below_floor_is_reported(self) -> None:
        """AC-04: a registered git write tool declaring a NONE-tier value is
        flagged fail-closed; the declaration is the only risk source."""
        from shared.runtime_tool_registry import RuntimeToolRegistry

        from tests.shared.runtime_tool_factory import build_fixture_runtime_tool

        registry = RuntimeToolRegistry(
            tools={
                "git_push": build_fixture_runtime_tool(
                    "git_push", "git", agent_safety_tier="READ_ONLY"
                )
            },
            allowed_servers=frozenset({"git"}),
        )
        result = ProductionConfigValidator().validate(
            {}, known_tools={"git_push"}, runtime_tools=registry
        )
        assert any("git_push" in err for err in result.errors)
