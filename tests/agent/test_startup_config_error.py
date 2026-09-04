"""Behavior-lock tests proving each config-error path's documented severity is produced under its condition."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from agent.config_builders import ConfigLoadError, build_agent_config
from shared.config_loader import ConfigLoader

from scripts.shared.config_errors import ConfigMissingError


class TestBuildAgentConfigErrorPath:
    """REQ-002 consequence: build_agent_config() aborts before security_profile_val
    computation when agent.toml is missing."""

    def test_missing_agent_toml_raises_config_load_error(self) -> None:
        """build_agent_config() raises ConfigLoadError when agent.toml is missing.

        This is a consequence of REQ-001's fix: ConfigLoader.load_all() defaults to
        strict=True, so ConfigMissingError propagates through load_config() as
        ConfigLoadError. Execution never reaches security_profile_val computation.
        """
        with patch.object(ConfigLoader, "load_all", side_effect=OSError("no file")):
            with pytest.raises(ConfigLoadError, match="Config load failed"):
                build_agent_config()

    def test_startup_fails_without_agent_toml(self):
        """REQ-001: Startup fails when agent.toml is missing (strict-default)."""
        from agent.context import AgentContext

        with patch.object(
            ConfigLoader, "load_all", side_effect=ConfigMissingError("agent.toml")
        ):
            with pytest.raises(RuntimeError, match="Failed to load agent config"):
                AgentContext()

    def test_build_agent_config_requires_agent_toml(self):
        """REQ-002: build_agent_config() raises ConfigLoadError when agent.toml is missing."""
        with patch.object(
            ConfigLoader, "load_all", side_effect=ConfigMissingError("agent.toml")
        ):
            with pytest.raises(ConfigLoadError, match="Config load failed"):
                build_agent_config()
