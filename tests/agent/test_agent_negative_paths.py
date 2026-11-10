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


def _cfg(**overrides: Any) -> AgentConfig:
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "llm_retry_base_delay": 1.0,
        "serial_tool_calls": False,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": ["shell_execute"],
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_shell_safe_prefixes": ["/bin/", "/usr/bin/"],
        "approval_github_allowed_repos": [],
        "allowed_root": "/opt/llm",
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
    """AGENT-4: force/overwrite/clobber should not elevate read-type tools."""

    def test_read_tool_force_flag_not_elevated(self) -> None:
        cfg = _cfg(approval_risk_rules={"read_file": "none"})
        result = classify_risk(cfg, "read_file", {"force": True})
        assert result == RiskLevel.NONE

    def test_read_tool_overwrite_flag_not_elevated(self) -> None:
        cfg = _cfg(approval_risk_rules={"read_file": "none"})
        result = classify_risk(cfg, "read_file", {"overwrite": True})
        assert result == RiskLevel.NONE

    def test_read_tool_clobber_flag_not_elevated(self) -> None:
        cfg = _cfg(approval_risk_rules={"read_file": "none"})
        result = classify_risk(cfg, "read_file", {"clobber": True})
        assert result == RiskLevel.NONE

    def test_write_tool_force_flag_elevated(self) -> None:
        cfg = _cfg(approval_risk_rules={"write_file": "medium"})
        result = classify_risk(cfg, "write_file", {"force": True})
        assert result == RiskLevel.HIGH

    def test_write_tool_overwrite_flag_elevated(self) -> None:
        cfg = _cfg(approval_risk_rules={"write_file": "medium"})
        result = classify_risk(cfg, "write_file", {"overwrite": True})
        assert result == RiskLevel.HIGH

    def test_write_tool_clobber_flag_elevated(self) -> None:
        cfg = _cfg(approval_risk_rules={"write_file": "medium"})
        result = classify_risk(cfg, "write_file", {"clobber": True})
        assert result == RiskLevel.HIGH
