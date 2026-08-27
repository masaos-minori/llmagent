"""tests/test_config_dataclasses.py
Unit tests for validation logic in agent/config_dataclasses.py:
LLMConfig, RAGConfig, ToolConfig, ApprovalConfig, AgentConfig.
"""

from __future__ import annotations

import re

import pytest
from agent.config_dataclasses import (
    AgentConfig,
    ApprovalConfig,
    DiagnosticsConfig,
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

    def test_llm_context_char_limit_negative_raises(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("context_char_limit must be >= 0, got -1")
        ):
            LLMConfig(context_char_limit=-1)

    def test_sse_heartbeat_timeout_negative_raises(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("sse_heartbeat_timeout must be >= 0, got -1")
        ):
            LLMConfig(sse_heartbeat_timeout=-1)

    def test_llm_max_retries_full_message(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("llm_max_retries must be >= 0, got -1")
        ):
            LLMConfig(llm_max_retries=-1)

    def test_llm_retry_base_delay_full_message(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("llm_retry_base_delay must be > 0, got 0.0")
        ):
            LLMConfig(llm_retry_base_delay=0.0)

    def test_llm_max_tokens_full_message(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("llm_max_tokens must be >= 1, got 0")
        ):
            LLMConfig(llm_max_tokens=0)

    def test_sse_malformed_retry_full_message(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("sse_malformed_retry must be >= 0, got -1")
        ):
            LLMConfig(sse_malformed_retry=-1)

    def test_sse_reconnect_max_full_message(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("sse_reconnect_max must be >= 0, got -1")
        ):
            LLMConfig(sse_reconnect_max=-1)

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
        with pytest.raises(
            ValueError, match=re.escape("refiner_max_tokens must be >= 1, got 0")
        ):
            RAGConfig(refiner_max_tokens=0)

    def test_refiner_timeout_full_message(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("refiner_timeout must be > 0, got 0.0")
        ):
            RAGConfig(refiner_timeout=0.0)

    def test_refiner_max_chars_per_chunk_full_message(self) -> None:
        with pytest.raises(
            ValueError,
            match=re.escape("refiner_max_chars_per_chunk must be >= 1, got 0"),
        ):
            RAGConfig(refiner_max_chars_per_chunk=0)


# ── ToolConfig ────────────────────────────────────────────────────────────────


class TestToolConfigValidation:
    def test_defaults_are_valid(self) -> None:
        cfg = ToolConfig()
        assert cfg.tool_dedup_max_repeats == 3

    def test_tool_dedup_max_repeats_zero_raises(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("tool_dedup_max_repeats must be >= 1, got 0")
        ):
            ToolConfig(tool_dedup_max_repeats=0)

    def test_tool_cycle_detect_window_full_message(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("tool_cycle_detect_window must be >= 0, got -1")
        ):
            ToolConfig(tool_cycle_detect_window=-1)

    def test_tool_error_max_consecutive_full_message(self) -> None:
        with pytest.raises(
            ValueError,
            match=re.escape("tool_error_max_consecutive must be >= 0, got -1"),
        ):
            ToolConfig(tool_error_max_consecutive=-1)

    def test_tool_error_retry_max_negative_raises(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("tool_error_retry_max must be >= 0, got -1")
        ):
            ToolConfig(tool_error_retry_max=-1)

    def test_progress_stagnation_window_negative_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match=re.escape("progress_stagnation_window must be >= 0, got -1"),
        ):
            ToolConfig(progress_stagnation_window=-1)


# ── ApprovalConfig ────────────────────────────────────────────────────────────


class TestApprovalConfigValidation:
    def test_defaults_are_valid(self) -> None:
        cfg = ApprovalConfig()
        assert "write_file" in cfg.approval_risk_rules

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
        # memory_embed_enabled now defaults to True, so embed_url must be non-empty
        # (mirrors config/agent.toml always supplying embed_url in practice).
        cfg = AgentConfig(rag=RAGConfig(embed_url="http://localhost:8080"))
        assert isinstance(cfg, AgentConfig)

    def test_agent_config_has_no_workflow_mode_field(self) -> None:
        assert not hasattr(
            AgentConfig(rag=RAGConfig(embed_url="http://localhost:8080")),
            "workflow_mode",
        )

    def test_agent_config_has_no_workflow_require_approval_field(self) -> None:
        assert not hasattr(
            AgentConfig(rag=RAGConfig(embed_url="http://localhost:8080")),
            "workflow_require_approval",
        )

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

    def test_default_diagnostics_config(self) -> None:
        cfg = AgentConfig(rag=RAGConfig(embed_url="http://localhost:8080"))
        assert cfg.diagnostics.encryption_key == ""
        assert cfg.diagnostics.retention_days == 30


# ── DiagnosticsConfig ─────────────────────────────────────────────────────────


class TestDiagnosticsConfigValidation:
    def test_defaults(self) -> None:
        cfg = DiagnosticsConfig()
        assert cfg.encryption_key == ""
        assert cfg.retention_days == 30

    def test_custom_values(self) -> None:
        cfg = DiagnosticsConfig(encryption_key="some-key", retention_days=7)
        assert cfg.encryption_key == "some-key"
        assert cfg.retention_days == 7


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


# ── MemoryConfig ──────────────────────────────────────────────────────────────


class TestMemoryConfigValidation:
    def test_defaults_valid(self) -> None:
        cfg = MemoryConfig()
        assert cfg.memory_fts_limit == 50
        assert cfg.memory_rrf_k == 60
        assert cfg.memory_recency_days == 7.0

    def test_fts_limit_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="memory_fts_limit must be >= 1"):
            MemoryConfig(memory_fts_limit=0)

    def test_rrf_k_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="memory_rrf_k must be >= 1"):
            MemoryConfig(memory_rrf_k=0)

    def test_recency_days_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="memory_recency_days must be > 0"):
            MemoryConfig(memory_recency_days=0.0)

    def test_recency_days_negative_raises(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("memory_recency_days must be > 0, got -1.0")
        ):
            MemoryConfig(memory_recency_days=-1.0)

    def test_memory_max_inject_semantic_negative_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match=re.escape("memory_max_inject_semantic must be >= 0, got -1"),
        ):
            MemoryConfig(memory_max_inject_semantic=-1)

    def test_memory_max_inject_episodic_negative_raises(self) -> None:
        with pytest.raises(
            ValueError,
            match=re.escape("memory_max_inject_episodic must be >= 0, got -1"),
        ):
            MemoryConfig(memory_max_inject_episodic=-1)

    def test_memory_embed_timeout_sec_zero_raises(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("memory_embed_timeout_sec must be > 0, got 0.0")
        ):
            MemoryConfig(memory_embed_timeout_sec=0.0)

    def test_memory_retention_days_zero_raises(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("memory_retention_days must be >= 1, got 0")
        ):
            MemoryConfig(memory_retention_days=0)
