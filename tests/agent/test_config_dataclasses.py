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
from agent.services.config_validators import (
    validate_diagnostics_encryption_key,
    validate_diagnostics_retention_days,
    validate_diagnostics_sensitive_fields,
    validate_disabled_tools,
    validate_tool_policy_mode,
)
from cryptography.fernet import Fernet
from shared.tool_registry import ToolDefinition, get_registry

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

    def test_has_no_refiner_attributes(self) -> None:
        """The refiner is configured only in the rag-pipeline MCP server (ADR-002)."""
        cfg = RAGConfig()
        for name in (
            "use_refiner",
            "refiner_max_tokens",
            "refiner_timeout",
            "refiner_max_chars_per_chunk",
        ):
            assert not hasattr(cfg, name), name


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

    def test_tool_policy_mode_defaults_to_explicit_allowlist(self) -> None:
        """REQ-001: an absent config key resolves to explicit_allowlist without
        special-casing."""
        cfg = ToolConfig()
        assert cfg.tool_policy_mode == "explicit_allowlist"

    def test_disabled_tools_defaults_to_empty_list(self) -> None:
        """REQ-001: disabled_tools is a hard denylist defaulting to empty."""
        cfg = ToolConfig()
        assert cfg.disabled_tools == []

    def test_exposure_fields_populate_from_kwargs(self) -> None:
        """The two new fields populate from raw config values."""
        cfg = ToolConfig(tool_policy_mode="discovered", disabled_tools=["shell_run"])
        assert cfg.tool_policy_mode == "discovered"
        assert cfg.disabled_tools == ["shell_run"]


# ── config_validators tool-field validators ─────────────────────────────────--


class TestConfigValidatorsToolFields:
    def test_tool_policy_mode_accepts_known_values(self) -> None:
        for mode in ("discovered", "explicit_allowlist"):
            validate_tool_policy_mode(ToolConfig(tool_policy_mode=mode))

    def test_tool_policy_mode_rejects_unknown(self) -> None:
        with pytest.raises(ValueError, match="tool_policy_mode must be"):
            validate_tool_policy_mode(ToolConfig(tool_policy_mode="bogus"))

    def test_disabled_tools_accepts_registered_name(self) -> None:
        get_registry().register(
            ToolDefinition(name="zzz_fixture_tool", server_key="fixture")
        )
        validate_disabled_tools(ToolConfig(disabled_tools=["zzz_fixture_tool"]))

    def test_disabled_tools_rejects_unregistered_name(self) -> None:
        with pytest.raises(ValueError, match="unregistered tool names"):
            validate_disabled_tools(ToolConfig(disabled_tools=["not_a_real_tool"]))

    def test_disabled_tools_empty_is_valid(self) -> None:
        validate_disabled_tools(ToolConfig(disabled_tools=[]))


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

    def test_agent_config_max_startup_snippets_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="agent_memory_max_startup_snippets"):
            AgentConfig(
                agent_memory_max_startup_snippets=0,
                rag=RAGConfig(embed_url="http://localhost:8080"),
            )

    def test_agent_config_max_startup_snippets_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="agent_memory_max_startup_snippets"):
            AgentConfig(
                agent_memory_max_startup_snippets=-1,
                rag=RAGConfig(embed_url="http://localhost:8080"),
            )

    def test_agent_config_max_startup_snippets_positive_values_pass(self) -> None:
        for value in (1, 5):
            cfg = AgentConfig(
                agent_memory_max_startup_snippets=value,
                rag=RAGConfig(embed_url="http://localhost:8080"),
            )
            assert cfg.agent_memory_max_startup_snippets == value

    def test_agent_config_max_startup_snippets_default_is_ten(self) -> None:
        cfg = AgentConfig(rag=RAGConfig(embed_url="http://localhost:8080"))
        assert cfg.agent_memory_max_startup_snippets == 10


# ── DiagnosticsConfig ─────────────────────────────────────────────────────────


class TestDiagnosticsConfigValidation:
    def test_defaults(self) -> None:
        cfg = DiagnosticsConfig()
        assert cfg.encryption_key == ""
        assert cfg.retention_days == 30

    def test_custom_values(self) -> None:
        cfg = DiagnosticsConfig(
            encryption_key=Fernet.generate_key().decode(), retention_days=7
        )
        assert cfg.encryption_key != ""
        assert cfg.retention_days == 7

    def test_construction_non_fernet_key_raises(self) -> None:
        with pytest.raises(
            ValueError, match="encryption_key is not a valid Fernet key"
        ):
            DiagnosticsConfig(encryption_key="not-a-valid-fernet-key")

    def test_construction_wrong_typed_retention_raises(self) -> None:
        with pytest.raises(
            ValueError, match="retention_days must be an int, got float"
        ):
            DiagnosticsConfig(retention_days=30.0)

    def test_construction_non_frozenset_fields_raises(self) -> None:
        with pytest.raises(ValueError, match="sensitive_fields must be a frozenset"):
            DiagnosticsConfig(sensitive_fields=["artifacts"])

    def test_encryption_key_empty_passes(self) -> None:
        cfg = DiagnosticsConfig(encryption_key="")
        validate_diagnostics_encryption_key(cfg)

    def test_encryption_key_valid_fernet_passes(self) -> None:
        cfg = DiagnosticsConfig(encryption_key=Fernet.generate_key().decode())
        validate_diagnostics_encryption_key(cfg)

    def test_encryption_key_non_fernet_raises(self) -> None:
        cfg = DiagnosticsConfig.__new__(DiagnosticsConfig)
        cfg.encryption_key = "not-a-valid-fernet-key"
        with pytest.raises(
            ValueError, match="encryption_key is not a valid Fernet key"
        ):
            validate_diagnostics_encryption_key(cfg)

    def test_retention_days_int_passes(self) -> None:
        cfg = DiagnosticsConfig(retention_days=30)
        validate_diagnostics_retention_days(cfg)

    def test_retention_days_float_raises(self) -> None:
        cfg = DiagnosticsConfig.__new__(DiagnosticsConfig)
        cfg.retention_days = 30.0
        with pytest.raises(
            ValueError, match="retention_days must be an int, got float"
        ):
            validate_diagnostics_retention_days(cfg)

    def test_retention_days_bool_raises(self) -> None:
        cfg = DiagnosticsConfig.__new__(DiagnosticsConfig)
        cfg.retention_days = True
        with pytest.raises(ValueError, match="retention_days must be an int, got bool"):
            validate_diagnostics_retention_days(cfg)

    def test_sensitive_fields_frozenset_of_strings_passes(self) -> None:
        cfg = DiagnosticsConfig(sensitive_fields=frozenset(("artifacts",)))
        validate_diagnostics_sensitive_fields(cfg)

    def test_sensitive_fields_non_frozenset_raises(self) -> None:
        cfg = DiagnosticsConfig.__new__(DiagnosticsConfig)
        cfg.sensitive_fields = ["artifacts"]
        with pytest.raises(ValueError, match="sensitive_fields must be a frozenset"):
            validate_diagnostics_sensitive_fields(cfg)

    def test_sensitive_fields_non_string_members_raises(self) -> None:
        cfg = DiagnosticsConfig.__new__(DiagnosticsConfig)
        cfg.sensitive_fields = frozenset((1, 2))
        with pytest.raises(ValueError, match="sensitive_fields must be a frozenset"):
            validate_diagnostics_sensitive_fields(cfg)


# ── MCPConfig removed-mode fields stay absent ─────────────────────────────────


class TestMCPConfigValidation:
    def test_removed_fields_are_absent(self) -> None:
        cfg = MCPConfig()
        assert not hasattr(cfg, "security_profile")
        tool = ToolConfig()
        assert not hasattr(tool, "tool_definitions_strict")
        assert not hasattr(tool, "routing_drift_strict")


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

    def test_memory_max_pinned_zero_raises(self) -> None:
        with pytest.raises(
            ValueError, match=re.escape("memory_max_pinned must be >= 1, got 0")
        ):
            MemoryConfig(memory_max_pinned=0)

    def test_memory_max_pinned_default_and_one_passes(self) -> None:
        assert MemoryConfig().memory_max_pinned == 10
        MemoryConfig(memory_max_pinned=1)
