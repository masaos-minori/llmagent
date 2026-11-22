"""
tests/test_agent_negative_paths.py

Characterization tests for agent layer negative paths and edge cases.
"""

from __future__ import annotations

import datetime
from typing import Any

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.memory.scoring import recency_boost
from agent.services.exceptions import ConfigReloadValidationError
from agent.tool_enums import RiskLevel
from agent.tool_policy import classify_risk
from shared.runtime_tool_registry import RuntimeToolRegistry

from tests.agent._config_test_defaults import SHIPPED_DB_PATH_KEYS
from tests.agent.test_tool_policy import _runtime_tool


def _cfg(**overrides: Any) -> AgentConfig:
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "llm_retry_base_delay": 1.0,
        "serial_tool_calls": False,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": ["shell_execute"],
        "approval_shell_safe_prefixes": ["/bin/", "/usr/bin/"],
        "approval_github_allowed_repos": [],
        "allowed_root": "/opt/llm",
        # build_agent_config() resolves the typed DB configuration from the mapping, so the fixture supplies the mirrored path keys.
        **SHIPPED_DB_PATH_KEYS,
        "sqlite_vec_so": "/opt/llm/sqlite-vec/vec0.so",
        "memory_local_only": True,
        "memory_embed_enabled": False,
        "mcp_servers": {
            "test_server": {
                "transport": "http",
                "url": "http://localhost:8011",
                "auth_token": "test-token",
            }
        },
    }
    merged = {**defaults, **overrides}
    return build_agent_config(merged)


class TestRemovedConfigKeysRejected:
    """AGENT-1: A config that still sets a removed strict/profile key is rejected."""

    @pytest.mark.parametrize(
        "overrides",
        [
            {"tool_definitions_strict": True},
            {"routing_drift_strict": True},
            {"security_profile": "production"},
        ],
    )
    def test_removed_key_rejected(self, overrides: dict[str, Any]) -> None:
        # Removed keys are no longer in the allowed set: the production
        # validator rejects them and the build raises.
        with pytest.raises(ConfigReloadValidationError):
            _cfg(**overrides)

    def test_empty_allowed_root_rejected(self) -> None:
        with pytest.raises(ValueError, match="allowed_root"):
            _cfg(allowed_root="")


class TestRecencyDaysBoundary:
    """AGENT-2: Exactly 7-day boundary should trigger boost calculation."""

    def test_recency_boundary_exactly_7_days_returns_zero(self) -> None:
        past = (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7)
        ).isoformat()
        assert recency_boost(past, recency_days=7.0) == 0.0

    def test_recency_boundary_6_days_returns_positive(self) -> None:
        past = (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=6)
        ).isoformat()
        boost = recency_boost(past, recency_days=7.0)
        assert boost > 0.0

    def test_recency_boundary_8_days_returns_zero(self) -> None:
        past = (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=8)
        ).isoformat()
        assert recency_boost(past, recency_days=7.0) == 0.0

    def test_recency_boundary_7_days_with_floating_point(self) -> None:
        past = (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=168)
        ).isoformat()
        boost = recency_boost(past, recency_days=7.0)
        assert boost >= 0.0

    def test_recency_boundary_6_days_23_hours_returns_positive(self) -> None:
        past = (
            datetime.datetime.now(datetime.UTC) - datetime.timedelta(hours=167)
        ).isoformat()
        boost = recency_boost(past, recency_days=7.0)
        assert boost > 0.0


class TestForceOverwriteClobberRisk:
    """AGENT-4: force/overwrite/clobber should not elevate read-type tools.

    agentcfg003 REQ-004/REQ-011: the base risk comes from the declared tier
    (the removed approval_risk_rules map no longer exists); the flag escalation
    applies only to tools whose declared tier carries a base risk."""

    @staticmethod
    def _registry(tier: str, *, is_write: bool, name: str) -> RuntimeToolRegistry:
        tool = _runtime_tool(name, tier=tier, is_write=is_write)
        return RuntimeToolRegistry(
            tools={name: tool}, allowed_servers=frozenset({tool.server_key})
        )

    @pytest.mark.parametrize("flag", ["force", "overwrite", "clobber"])
    def test_read_tool_flag_not_elevated(self, flag: str) -> None:
        cfg = _cfg()
        reg = self._registry("READ_ONLY", is_write=False, name="read_file")
        result = classify_risk(cfg, "read_file", {flag: True}, reg)
        assert result == RiskLevel.NONE

    @pytest.mark.parametrize("flag", ["force", "overwrite", "clobber"])
    def test_write_tool_flag_elevated(self, flag: str) -> None:
        cfg = _cfg()
        reg = self._registry("WRITE_DANGEROUS", is_write=True, name="write_file")
        result = classify_risk(cfg, "write_file", {flag: True}, reg)
        assert result == RiskLevel.HIGH
