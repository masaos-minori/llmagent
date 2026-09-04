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
from agent.tool_enums import RiskLevel
from agent.tool_policy import classify_risk


def _cfg(**overrides: Any) -> AgentConfig:
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "tool_cache_ttl": 300,
        "top_k_search": 20,
        "top_k_rerank": 15,
        "rag_top_k": 5,
        "use_mqe": True,
        "use_search": True,
        "use_rrf": True,
        "use_rerank": True,
        "llm_max_retries": 3,
        "llm_retry_base_delay": 1.0,
        "rag_min_score": 0.0,
        "max_chunks_per_doc": 2,
        "use_two_stage_fetch": False,
        "two_stage_max_docs": 2,
        "serial_tool_calls": False,
        "use_semantic_cache": False,
        "semantic_cache_threshold": 0.92,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": ["shell_execute"],
        "tool_definitions_strict": True,
        "routing_drift_strict": True,
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_shell_safe_prefixes": ["/bin/", "/usr/bin/"],
        "approval_github_allowed_repos": [],
        "allowed_root": "",
        "security_profile": "production",
        "security_lockdown_enabled": False,
        "memory_local_only": True,
        "memory_embed_enabled": False,
        "mcp_servers": {
            "test_server": {"transport": "http", "url": "http://localhost:8011"}
        },
    }
    merged = {**defaults, **overrides}
    return build_agent_config(merged)


class TestSecurityProfileInvalidValue:
    """AGENT-1: Invalid security_profile value should raise ValueError."""

    def test_invalid_security_profile_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _cfg(security_profile="INVALID_PROFILE")

    def test_empty_string_security_profile_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _cfg(security_profile="")

    def test_numeric_security_profile_raises_value_error(self) -> None:
        with pytest.raises(ValueError):
            _cfg(security_profile="123")


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
