"""tests/test_config_dataclasses.py
Unit tests for validation logic in agent/config_dataclasses.py:
LLMConfig, RAGConfig, ToolConfig, ApprovalConfig, AgentConfig.
"""

from __future__ import annotations

import pytest
from agent.config_dataclasses import (
    AgentConfig,
    ApprovalConfig,
    LLMConfig,
    MCPConfig,
    MemoryConfig,
    RAGConfig,
    ToolConfig,
)

# ── LLMConfig ─────────────────────────────────────────────────────────────────


class TestLLMConfigValidation:
    def test_defaults_are_valid(self) -> None:
        cfg = LLMConfig()
        assert cfg.llm_url == ""
        assert cfg.llm_temperature == 0.2
        assert cfg.budget_warn_ratio == 0.8

    def test_budget_warn_ratio_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="budget_warn_ratio"):
            LLMConfig(budget_warn_ratio=0.0)

    def test_budget_warn_ratio_above_one_raises(self) -> None:
        with pytest.raises(ValueError, match="budget_warn_ratio"):
            LLMConfig(budget_warn_ratio=1.1)

    def test_budget_warn_ratio_one_is_valid(self) -> None:
        cfg = LLMConfig(budget_warn_ratio=1.0)
        assert cfg.budget_warn_ratio == 1.0

    def test_llm_max_retries_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="llm_max_retries"):
            LLMConfig(llm_max_retries=-1)

    def test_llm_max_retries_zero_is_valid(self) -> None:
        cfg = LLMConfig(llm_max_retries=0)
        assert cfg.llm_max_retries == 0

    def test_llm_retry_base_delay_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="llm_retry_base_delay"):
            LLMConfig(llm_retry_base_delay=0.0)

    def test_llm_retry_base_delay_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="llm_retry_base_delay"):
            LLMConfig(llm_retry_base_delay=-1.0)

    def test_llm_temperature_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="llm_temperature"):
            LLMConfig(llm_temperature=-0.1)

    def test_llm_temperature_above_max_raises(self) -> None:
        with pytest.raises(ValueError, match="llm_temperature"):
            LLMConfig(llm_temperature=2.1)

    def test_llm_temperature_at_max_is_valid(self) -> None:
        cfg = LLMConfig(llm_temperature=2.0)
        assert cfg.llm_temperature == 2.0

    def test_llm_max_tokens_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="llm_max_tokens"):
            LLMConfig(llm_max_tokens=0)

    def test_sse_malformed_retry_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="sse_malformed_retry"):
            LLMConfig(sse_malformed_retry=-1)

    def test_sse_reconnect_max_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="sse_reconnect_max"):
            LLMConfig(sse_reconnect_max=-1)


# ── RAGConfig ─────────────────────────────────────────────────────────────────


class TestRAGConfigValidation:
    def test_defaults_are_valid(self) -> None:
        cfg = RAGConfig()
        assert cfg.web_search_max_results == 5
        assert cfg.embed_url == ""
        assert cfg.use_semantic_cache is False
        assert cfg.semantic_cache_threshold == 0.92
        assert cfg.semantic_cache_max_size == 100
        assert cfg.use_refiner is False
        assert cfg.refiner_max_tokens == 512
        assert cfg.refiner_timeout == 30.0
        assert cfg.refiner_max_chars_per_chunk == 300

    def test_refiner_timeout_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="refiner_timeout"):
            RAGConfig(refiner_timeout=0.0)

    def test_refiner_max_tokens_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="refiner_max_tokens"):
            RAGConfig(refiner_max_tokens=0)

    def test_refiner_max_chars_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="refiner_max_chars_per_chunk"):
            RAGConfig(refiner_max_chars_per_chunk=0)


# ── ToolConfig ────────────────────────────────────────────────────────────────


class TestToolConfigValidation:
    def test_defaults_are_valid(self) -> None:
        cfg = ToolConfig()
        assert cfg.tool_dedup_max_repeats == 3
        assert cfg.plugin_strict is False

    def test_tool_dedup_max_repeats_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="tool_dedup_max_repeats"):
            ToolConfig(tool_dedup_max_repeats=0)

    def test_tool_cycle_detect_window_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="tool_cycle_detect_window"):
            ToolConfig(tool_cycle_detect_window=-1)

    def test_tool_error_max_consecutive_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="tool_error_max_consecutive"):
            ToolConfig(tool_error_max_consecutive=-1)

    def test_tool_cache_max_size_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="tool_cache_max_size"):
            ToolConfig(tool_cache_max_size=-1)

    def test_plugin_tool_override_non_bool_raises(self) -> None:
        with pytest.raises(ValueError, match="plugin_tool_override"):
            ToolConfig(plugin_tool_override="yes")  # type: ignore[arg-type]

    def test_plugin_strict_non_bool_raises(self) -> None:
        with pytest.raises(ValueError, match="plugin_strict"):
            ToolConfig(plugin_strict=1)  # type: ignore[arg-type]


# ── ApprovalConfig ────────────────────────────────────────────────────────────


class TestApprovalConfigValidation:
    def test_defaults_are_valid(self) -> None:
        cfg = ApprovalConfig()
        assert "write_file" in cfg.approval_risk_rules
        assert cfg.gitops_force_push_blocked is True

    def test_invalid_risk_level_raises(self) -> None:
        with pytest.raises(ValueError, match="approval_risk_rules"):
            ApprovalConfig(approval_risk_rules={"write_file": "extreme"})

    def test_invalid_safety_tier_raises(self) -> None:
        with pytest.raises(ValueError, match="tool_safety_tiers"):
            ApprovalConfig(tool_safety_tiers={"write_file": "UNKNOWN"})

    def test_valid_safety_tiers_accepted(self) -> None:
        cfg = ApprovalConfig(
            tool_safety_tiers={
                "write_file": "WRITE_SAFE",
                "shell_run": "ADMIN",
                "read_file": "READ_ONLY",
            }
        )
        assert cfg.tool_safety_tiers["shell_run"] == "ADMIN"

    def test_multiple_invalid_risk_levels_all_reported(self) -> None:
        with pytest.raises(ValueError, match="approval_risk_rules"):
            ApprovalConfig(
                approval_risk_rules={"tool_a": "extreme", "tool_b": "critical"}
            )


# ── AgentConfig cross-field validation ────────────────────────────────────────


class TestAgentConfigValidation:
    def test_defaults_are_valid(self) -> None:
        cfg = AgentConfig()
        assert isinstance(cfg, AgentConfig)

    def test_agent_config_has_no_workflow_mode_field(self) -> None:
        assert not hasattr(AgentConfig(), "workflow_mode")

    def test_agent_config_has_no_workflow_require_approval_field(self) -> None:
        assert not hasattr(AgentConfig(), "workflow_require_approval")

    def test_semantic_cache_without_embed_url_raises(self) -> None:
        rag = RAGConfig(use_semantic_cache=True, embed_url="")
        with pytest.raises(ValueError, match="embed_url"):
            AgentConfig(rag=rag)

    def test_memory_embed_without_embed_url_raises(self) -> None:
        mem = MemoryConfig(memory_embed_enabled=True)
        rag = RAGConfig(embed_url="")
        with pytest.raises(ValueError, match="embed_url"):
            AgentConfig(rag=rag, memory=mem)

    def test_memory_layer_without_jsonl_dir_raises(self) -> None:
        mem = MemoryConfig(use_memory_layer=True, memory_jsonl_dir="")
        with pytest.raises(ValueError, match="memory_jsonl_dir"):
            AgentConfig(memory=mem)


# ── MCPConfig coercion ────────────────────────────────────────────────────────


class TestMCPConfigValidation:
    def test_defaults_are_valid(self) -> None:
        from shared.mcp_config import SecurityProfile

        cfg = MCPConfig()
        assert cfg.security_profile == SecurityProfile.LOCAL

    def test_string_profile_coerced_to_enum(self) -> None:
        from shared.mcp_config import SecurityProfile

        cfg = MCPConfig(security_profile="production")  # type: ignore[arg-type]
        assert cfg.security_profile == SecurityProfile.PRODUCTION
