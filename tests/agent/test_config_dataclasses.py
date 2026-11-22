"""tests/test_config_dataclasses.py
Unit tests for validation logic in agent/config_dataclasses.py:
LLMConfig, ToolConfig, ApprovalConfig, AgentConfig.
"""

from __future__ import annotations

import dataclasses
import re
from typing import Any

import pytest
from agent.config_dataclasses import (
    AgentConfig,
    ApprovalConfig,
    DiagnosticsConfig,
    LLMConfig,
    MCPConfig,
    MemoryConfig,
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

from tests.agent._config_test_defaults import MIN_DB_CONFIG, MIN_MAINTENANCE_CONFIG


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
    """Agentcfg003 REQ-005: the four removed per-tool maps have no fields and no
    validators; the operational-exception fields remain asserted."""

    def test_defaults_are_valid(self) -> None:
        cfg = ApprovalConfig()
        assert "write_file" not in getattr(cfg, "approval_protected_paths", [])
        assert cfg.approval_high_risk_branches == ["main", "master"]

    @pytest.mark.parametrize(
        "removed_field",
        [
            "approval_risk_rules",
            "tool_safety_tiers",
            "approval_resource_keys",
            "approval_dry_run_tools",
        ],
    )
    def test_removed_map_fields_are_gone(self, removed_field: str) -> None:
        """REQ-005: the dataclass no longer carries the removed maps (REQ-011:
        no compatibility field)."""
        assert not hasattr(ApprovalConfig(), removed_field)
        with pytest.raises(TypeError, match="unexpected keyword argument"):
            ApprovalConfig(**{removed_field: {}})

    def test_operational_exception_fields_accepted(self) -> None:
        cfg = ApprovalConfig(
            approval_protected_paths=["/opt/"],
            approval_shell_safe_prefixes=["ls"],
            approval_github_allowed_repos=[],
        )
        assert cfg.approval_protected_paths == ["/opt/"]
        assert cfg.approval_shell_safe_prefixes == ["ls"]


# ── AgentConfig cross-field validation ────────────────────────────────────────


def _agent_config(**kwargs: Any) -> AgentConfig:
    """Build AgentConfig with the typed configuration its required fields now take."""
    return AgentConfig(db=MIN_DB_CONFIG, maintenance=MIN_MAINTENANCE_CONFIG, **kwargs)


class TestAgentConfigValidation:
    def test_defaults_are_valid(self) -> None:
        # memory_embed_enabled defaults to True, so memory_embed_url must be
        # non-empty (mirrors config/agent.toml always supplying it in practice).
        cfg = _agent_config(
            memory=MemoryConfig(memory_embed_url="http://localhost:8080")
        )
        assert isinstance(cfg, AgentConfig)

    def test_agent_config_has_no_workflow_mode_field(self) -> None:
        assert not hasattr(
            _agent_config(
                memory=MemoryConfig(memory_embed_url="http://localhost:8080")
            ),
            "workflow_mode",
        )

    def test_agent_config_has_no_workflow_require_approval_field(self) -> None:
        assert not hasattr(
            _agent_config(
                memory=MemoryConfig(memory_embed_url="http://localhost:8080")
            ),
            "workflow_require_approval",
        )

    def test_memory_layer_without_jsonl_dir_raises(self) -> None:
        mem = MemoryConfig(
            use_memory_layer=True,
            memory_jsonl_dir="",
            memory_embed_enabled=False,
        )
        with pytest.raises(ValueError, match="memory_jsonl_dir"):
            _agent_config(memory=mem)

    def test_default_diagnostics_config(self) -> None:
        cfg = _agent_config(
            memory=MemoryConfig(memory_embed_url="http://localhost:8080")
        )
        assert cfg.diagnostics.encryption_key == ""
        assert cfg.diagnostics.retention_days == 30

    def test_agent_config_max_startup_snippets_zero_raises(self) -> None:
        with pytest.raises(ValueError, match="agent_memory_max_startup_snippets"):
            _agent_config(
                agent_memory_max_startup_snippets=0,
                memory=MemoryConfig(memory_embed_url="http://localhost:8080"),
            )

    def test_agent_config_max_startup_snippets_negative_raises(self) -> None:
        with pytest.raises(ValueError, match="agent_memory_max_startup_snippets"):
            _agent_config(
                agent_memory_max_startup_snippets=-1,
                memory=MemoryConfig(memory_embed_url="http://localhost:8080"),
            )

    def test_agent_config_max_startup_snippets_positive_values_pass(self) -> None:
        for value in (1, 5):
            cfg = _agent_config(
                agent_memory_max_startup_snippets=value,
                memory=MemoryConfig(memory_embed_url="http://localhost:8080"),
            )
            assert cfg.agent_memory_max_startup_snippets == value

    def test_agent_config_max_startup_snippets_default_is_ten(self) -> None:
        cfg = _agent_config(
            memory=MemoryConfig(memory_embed_url="http://localhost:8080")
        )
        assert cfg.agent_memory_max_startup_snippets == 10

    def test_approval_grant_ttl_seconds_default_and_declared_field(self) -> None:
        # mcpdl003 REQ-002: grant horizon is a config field, default equal to
        # the retired tool_approval._GRANT_TTL_SECONDS constant.
        cfg = _agent_config(
            memory=MemoryConfig(memory_embed_url="http://localhost:8080")
        )
        assert cfg.approval_grant_ttl_seconds == 300.0
        assert "approval_grant_ttl_seconds" in {
            f.name for f in dataclasses.fields(AgentConfig)
        }


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
    def test_enabled_without_embed_url_raises(self) -> None:
        with pytest.raises(
            match=re.escape(
                "memory_embed_enabled=True requires memory_embed_url to be non-empty",
            ),
        ):
            MemoryConfig(memory_embed_enabled=True)

    def test_enabled_with_embed_url_passes(self) -> None:
        cfg = MemoryConfig(memory_embed_url="http://localhost:8080")
        assert cfg.memory_embed_url == "http://localhost:8080"

    def test_disabled_without_embed_url_passes(self) -> None:
        cfg = MemoryConfig(memory_embed_enabled=False)
        assert cfg.memory_embed_url == ""

    def test_defaults_valid(self) -> None:
        # memory_embed_enabled defaults to True, so the enabled-gated check runs;
        # construct with a non-empty url, as config/agent.toml always supplies one.
        cfg = MemoryConfig(memory_embed_url="http://localhost:8080")
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
            match=re.escape("memory_max_inject_semantic must be >= 0, got -1"),
        ):
            MemoryConfig(memory_max_inject_semantic=-1)

    def test_memory_max_inject_episodic_negative_raises(self) -> None:
        with pytest.raises(
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
        # memory_embed_enabled defaults to True, so the enabled-gated check runs;
        # disable it to test the max_pinned default in isolation.
        cfg = MemoryConfig(memory_embed_enabled=False)
        assert cfg.memory_max_pinned == 10
        MemoryConfig(memory_max_pinned=1, memory_embed_enabled=False)
