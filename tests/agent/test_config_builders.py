"""tests/test_config_builders.py
Unit tests for agent/config_builders.py:
_build_llm_config, _build_rag_config, _build_approval_config, _build_memory_config,
_build_tool_config, build_agent_config, and load_config error handling.
"""

from __future__ import annotations

import logging
from unittest.mock import patch

import pytest
from agent.config_builders import (
    ConfigLoadError,
    _build_approval_config,
    _build_diagnostics_config,
    _build_llm_config,
    _build_memory_config,
    _build_rag_config,
    _build_tool_config,
    _validate_dry_run_tools,
    build_agent_config,
    load_config,
)
from agent.config_dataclasses import AgentConfig
from agent.services.exceptions import ConfigReloadValidationError
from shared.mcp_config import SecurityProfile

# Minimal config satisfying _build_mcp_servers (needs at least one HTTP server with url) and
# AgentConfig.__post_init__'s memory_embed_enabled cross-field check (now defaults to True,
# so embed_url must be non-empty — mirrors config/agent.toml always supplying embed_url).
_MIN_CFG: dict = {
    "mcp_servers": {
        "test-server": {"transport": "http", "url": "http://127.0.0.1:9999"}
    },
    "embed_url": "http://127.0.0.1:9999",
}

# ── _build_llm_config ─────────────────────────────────────────────────────────


_LLM_DEFAULTS = {
    "llm_url": "",
    "http_timeout": 30.0,
    "llm_max_retries": 3,
    "llm_retry_base_delay": 1.0,
    "llm_temperature": 0.2,
    "llm_max_tokens": 1024,
    "title_llm_temperature": 0.1,
    "title_llm_max_tokens": 20,
    "sse_heartbeat_timeout": 30.0,
    "sse_malformed_retry": 2,
    "sse_reconnect_max": 1,
    "llm_stream_retry_on_heartbeat_timeout": True,
    "llm_stream_retry_on_malformed_chunk": False,
    "tokenize_url": "",
    "context_token_limit": 0,
    "context_char_limit": 8000,
    "context_compress_turns": 4,
    "history_protect_turns": 2,
    "budget_warn_ratio": 0.8,
}


class TestBuildLLMConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_llm_config({})
        for key, value in _LLM_DEFAULTS.items():
            assert getattr(cfg, key) == value, key

    def test_overrides_are_applied(self) -> None:
        cfg = _build_llm_config({"llm_url": "http://llm.local", "llm_max_tokens": 512})
        assert cfg.llm_url == "http://llm.local"
        assert cfg.llm_max_tokens == 512

    def test_type_coercion_for_numeric_fields(self) -> None:
        with pytest.raises(ConfigReloadValidationError):
            _build_llm_config({"llm_max_retries": "5", "llm_temperature": "0.5"})

    def test_every_field_override_is_independently_reflected(self) -> None:
        # Guards each individual cfg-key -> field mapping (not just a couple of
        # spot-checked fields) so a typo'd key string in the extraction helper
        # calls is caught.
        overrides = {
            "llm_url": "http://override",
            "http_timeout": 99.0,
            "llm_max_retries": 9,
            "llm_retry_base_delay": 9.0,
            "llm_temperature": 0.9,
            "llm_max_tokens": 999,
            "title_llm_temperature": 0.9,
            "title_llm_max_tokens": 99,
            "sse_heartbeat_timeout": 99.0,
            "sse_malformed_retry": 9,
            "sse_reconnect_max": 9,
            "llm_stream_retry_on_heartbeat_timeout": False,
            "llm_stream_retry_on_malformed_chunk": True,
            "tokenize_url": "http://tok",
            "context_token_limit": 99,
            "context_char_limit": 99,
            "context_compress_turns": 9,
            "history_protect_turns": 9,
            "budget_warn_ratio": 0.5,
        }
        cfg = _build_llm_config(overrides)
        for key, value in overrides.items():
            assert getattr(cfg, key) == value, key


# ── _build_rag_config ─────────────────────────────────────────────────────────


class TestBuildRAGConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_rag_config({})
        assert cfg.embed_url == ""
        assert cfg.use_semantic_cache is False
        assert cfg.semantic_cache_threshold == 0.92
        assert cfg.semantic_cache_max_size == 100
        assert cfg.use_refiner is False
        assert cfg.refiner_max_tokens == 512
        assert cfg.refiner_timeout == 30.0
        assert cfg.refiner_max_chars_per_chunk == 300

    def test_overrides_are_applied(self) -> None:
        cfg = _build_rag_config({"use_semantic_cache": True})
        assert cfg.use_semantic_cache is True

    def test_every_field_override_is_independently_reflected(self) -> None:
        overrides = {
            "embed_url": "http://embed",
            "use_semantic_cache": True,
            "semantic_cache_threshold": 0.5,
            "semantic_cache_max_size": 9,
            "use_refiner": True,
            "refiner_max_tokens": 9,
            "refiner_timeout": 9.0,
            "refiner_max_chars_per_chunk": 9,
        }
        cfg = _build_rag_config(overrides)
        for key, value in overrides.items():
            assert getattr(cfg, key) == value, key


# ── _build_tool_config ────────────────────────────────────────────────────────


_TOOL_DEFAULTS = {
    "tool_cache_ttl": 300,
    "tool_cache_max_size": 200,
    "serial_tool_calls": False,
    "tool_definitions_strict": False,
    "routing_drift_strict": False,
    "tool_dedup_max_repeats": 3,
    "tool_cycle_detect_window": 2,
    "tool_error_max_consecutive": 3,
    "tool_error_retry_max": 1,
    "tool_concurrency_limits": {},
    "masked_fields": ["file_content"],
    "plan_blocked_tools": [
        "write_file",
        "create_directory",
        "delete_file",
        "delete_directory",
    ],
    "max_tool_turns": 5,
    "tool_result_max_llm_chars": 8000,
    "tool_results_turn_max_chars": 50000,
    "tool_definitions": [],
    "allowed_tools": [],
}


class TestBuildToolConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_tool_config({}, system_prompt_tool="")
        for key, value in _TOOL_DEFAULTS.items():
            assert getattr(cfg, key) == value, key
        assert cfg.system_prompts == {"default": ""}
        assert cfg.system_prompt_tool == ""

    def test_system_prompt_tool_is_set(self) -> None:
        cfg = _build_tool_config({}, system_prompt_tool="You are an assistant.")
        assert cfg.system_prompt_tool == "You are an assistant."

    def test_every_field_override_is_independently_reflected(self) -> None:
        overrides = {
            "tool_cache_ttl": 9.0,
            "tool_cache_max_size": 9,
            "serial_tool_calls": True,
            "tool_definitions_strict": True,
            "routing_drift_strict": True,
            "tool_dedup_max_repeats": 9,
            "tool_cycle_detect_window": 9,
            "tool_error_max_consecutive": 9,
            "tool_error_retry_max": 9,
            "tool_concurrency_limits": {"srv": 2},
            "masked_fields": ["custom_field"],
            "plan_blocked_tools": ["custom_tool"],
            "max_tool_turns": 9,
            "tool_result_max_llm_chars": 9,
            "tool_results_turn_max_chars": 9,
            "tool_definitions": [{"name": "x"}],
            "system_prompts": {"default": "custom"},
            "allowed_tools": ["tool_a"],
        }
        cfg = _build_tool_config(overrides, system_prompt_tool="base-prompt")
        for key, value in overrides.items():
            assert getattr(cfg, key) == value, key
        assert cfg.system_prompt_tool == "base-prompt"


# ── _build_memory_config ──────────────────────────────────────────────────────


_MEMORY_DEFAULTS = {
    "use_memory_layer": True,
    "memory_jsonl_dir": "/opt/llm/memory",
    "memory_max_inject_semantic": 5,
    "memory_max_inject_episodic": 3,
    "memory_min_importance": 0.3,
    "memory_embed_enabled": True,
    "memory_dedup_threshold": 0.3,
    "memory_max_content_chars": 500,
    "memory_embed_timeout_sec": 5.0,
    "memory_retention_days": 90,
    "memory_fts_limit": 50,
    "memory_rrf_k": 60,
    "memory_recency_days": 7.0,
    "memory_local_only": False,
}


class TestBuildMemoryConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_memory_config({})
        for key, value in _MEMORY_DEFAULTS.items():
            assert getattr(cfg, key) == value, key

    def test_overrides_are_applied(self) -> None:
        cfg = _build_memory_config(
            {
                "use_memory_layer": False,
                "memory_embed_enabled": False,
                "memory_jsonl_dir": "/tmp/custom_memory_dir",
            }
        )
        assert cfg.use_memory_layer is False
        assert cfg.memory_embed_enabled is False
        assert cfg.memory_jsonl_dir == "/tmp/custom_memory_dir"

    def test_every_field_override_is_independently_reflected(self) -> None:
        overrides = {
            "use_memory_layer": False,
            "memory_jsonl_dir": "/tmp/custom_memory_dir",
            "memory_max_inject_semantic": 9,
            "memory_max_inject_episodic": 9,
            "memory_min_importance": 0.9,
            "memory_embed_enabled": False,
            "memory_dedup_threshold": 0.9,
            "memory_max_content_chars": 9,
            "memory_embed_timeout_sec": 9.0,
            "memory_retention_days": 9,
            "memory_fts_limit": 9,
            "memory_rrf_k": 9,
            "memory_recency_days": 9.0,
            "memory_local_only": True,
        }
        cfg = _build_memory_config(overrides)
        for key, value in overrides.items():
            assert getattr(cfg, key) == value, key


# ── _build_approval_config ────────────────────────────────────────────────────


class TestBuildApprovalConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_approval_config({})
        assert "write_file" in cfg.approval_risk_rules
        assert cfg.approval_risk_rules["delete_file"] == "high"
        assert cfg.approval_protected_paths == [
            "/opt/",
            "/etc/",
            "/boot/",
            "/usr/",
            "/bin/",
            "/sbin/",
        ]
        assert cfg.approval_high_risk_branches == ["main", "master"]
        assert cfg.approval_shell_safe_prefixes == [
            "ls",
            "cat",
            "echo",
            "git log",
            "git status",
            "git diff",
            "git show",
            "git branch",
            "pwd",
            "find",
            "grep",
        ]
        assert cfg.approval_resource_keys == {
            "path_keys": ["path", "file_path", "directory_path", "source", "destination"],
            "branch_keys": ["branch", "base", "head"],
        }
        assert cfg.approval_dry_run_tools == [
            "write_file",
            "edit_file",
            "create_directory",
            "delete_file",
            "delete_directory",
            "move_file",
        ]
        assert cfg.tool_safety_tiers == {}
        assert cfg.allowed_root == ""
        assert cfg.approval_github_allowed_repos == []
        assert cfg.gitops_push_blocked is False

    def test_invalid_risk_level_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="invalid levels"):
            _build_approval_config({"approval_risk_rules": {"write_file": "extreme"}})

    def test_every_field_override_is_independently_reflected(self) -> None:
        overrides: dict = {
            "approval_risk_rules": {"write_file": "none"},
            "approval_protected_paths": ["/custom/"],
            "approval_high_risk_branches": ["custom-branch"],
            "approval_shell_safe_prefixes": ["custom-cmd"],
            "approval_resource_keys": {"path_keys": ["p"], "branch_keys": ["b"]},
            "approval_dry_run_tools": ["write_file"],
            "tool_safety_tiers": {"some_tool": "READ_ONLY"},
            "allowed_root": "/custom/root",
            "approval_github_allowed_repos": ["org/repo"],
            "gitops_push_blocked": True,
        }
        cfg = _build_approval_config(overrides)
        for key, value in overrides.items():
            assert getattr(cfg, key) == value, key


# ── _build_diagnostics_config ─────────────────────────────────────────────────


class TestValidateDryRunTools:
    def test_unsupported_tool_is_dropped_with_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        with caplog.at_level(logging.WARNING, logger="agent.config_builders"):
            result = _validate_dry_run_tools(["write_file", "totally_unknown_tool"])
        assert result == ["write_file"]
        assert any(
            "totally_unknown_tool" in r.message and r.levelno == logging.WARNING
            for r in caplog.records
        )

    def test_all_supported_tools_pass_through_unchanged(self) -> None:
        result = _validate_dry_run_tools(["write_file", "delete_file"])
        assert result == ["write_file", "delete_file"]


class TestBuildDiagnosticsConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_diagnostics_config({})
        assert cfg.encryption_key == ""
        assert cfg.retention_days == 30

    def test_overrides_are_applied(self) -> None:
        cfg = _build_diagnostics_config(
            {"diagnostics": {"encryption_key": "abc123", "retention_days": 7}}
        )
        assert cfg.encryption_key == "abc123"
        assert cfg.retention_days == 7

    def test_missing_diagnostics_table_returns_defaults(self) -> None:
        cfg = _build_diagnostics_config({"llm_url": "http://llm.local"})
        assert cfg.encryption_key == ""
        assert cfg.retention_days == 30


# ── build_agent_config ────────────────────────────────────────────────────────


class TestBuildAgentConfig:
    def test_returns_agent_config_instance(self) -> None:
        cfg = build_agent_config(_MIN_CFG)
        assert isinstance(cfg, AgentConfig)

    def test_top_level_bool_and_observability_overrides_reflected(self) -> None:
        cfg = build_agent_config(
            {
                **_MIN_CFG,
                "security_lockdown_enabled": True,
                "otel_enabled": True,
                "structured_log": True,
                "otel_endpoint": "http://otel",
                "otel_service_name": "custom-svc",
                "audit_log_file": "/custom/audit.log",
            }
        )
        assert cfg.mcp.security_lockdown_enabled is True
        assert cfg.obs.otel_enabled is True
        assert cfg.obs.structured_log is True
        assert cfg.obs.otel_endpoint == "http://otel"
        assert cfg.obs.otel_service_name == "custom-svc"
        assert cfg.obs.audit_log_file == "/custom/audit.log"

    def test_system_prompt_tool_and_security_profile_propagate(self) -> None:
        cfg = build_agent_config(
            {
                **_MIN_CFG,
                "system_prompt_tool": "You are a helpful agent.",
                "security_profile": "production",
                "tool_definitions_strict": True,
                "routing_drift_strict": True,
                "allowed_tools": ["some_tool"],
            }
        )
        assert cfg.tool.system_prompt_tool == "You are a helpful agent."
        assert cfg.mcp.security_profile == SecurityProfile.PRODUCTION

    def test_production_validation_passes_without_exit_when_strict_flags_set(
        self,
    ) -> None:
        # Companion to test_production_validation_errors_exit_process: proves the
        # sys.exit(1) path is specifically gated on results.errors, not on
        # security_profile=="production" alone.
        with patch("agent.config_builders.sys.exit") as mock_exit:
            build_agent_config(
                {
                    **_MIN_CFG,
                    "security_profile": "production",
                    "tool_definitions_strict": True,
                    "routing_drift_strict": True,
                    "allowed_tools": ["some_tool"],
                }
            )
        mock_exit.assert_not_called()

    def test_llm_defaults_reflected(self) -> None:
        cfg = build_agent_config(_MIN_CFG)
        assert cfg.llm.llm_url == ""

    def test_diagnostics_defaults_reflected(self) -> None:
        cfg = build_agent_config(_MIN_CFG)
        assert cfg.diagnostics.encryption_key == ""
        assert cfg.diagnostics.retention_days == 30

    def test_none_cfg_override_calls_load_config(self) -> None:
        with patch("agent.config_builders.ConfigLoader") as MockLoader:
            MockLoader.return_value.load_all.return_value = _MIN_CFG
            cfg = build_agent_config(None)
        assert isinstance(cfg, AgentConfig)

    def test_production_validation_errors_exit_process(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # security_profile="production" without tool_definitions_strict/
        # routing_drift_strict set to True produces ProductionConfigValidator
        # errors, which build_agent_config logs and turns into sys.exit(1).
        cfg = {**_MIN_CFG, "security_profile": "production"}
        with (
            caplog.at_level(logging.ERROR, logger="agent.config_builders"),
            patch("agent.config_builders.sys.exit") as mock_exit,
        ):
            build_agent_config(cfg)
        mock_exit.assert_called_once_with(1)
        assert any(
            "Production config validation failed" in r.message
            for r in caplog.records
        )


# ── load_config ───────────────────────────────────────────────────────────────


class TestLoadConfig:
    def test_raises_on_os_error(self) -> None:
        with patch("agent.config_builders.ConfigLoader") as MockLoader:
            MockLoader.return_value.load_all.side_effect = OSError("no config file")
            with pytest.raises(ConfigLoadError, match="Config load failed"):
                load_config()

    def test_raises_on_value_error(self) -> None:
        with patch("agent.config_builders.ConfigLoader") as MockLoader:
            MockLoader.return_value.load_all.side_effect = ValueError("bad TOML")
            with pytest.raises(ConfigLoadError, match="Config load failed"):
                load_config()

    def test_raises_on_type_error(self) -> None:
        with patch("agent.config_builders.ConfigLoader") as MockLoader:
            MockLoader.return_value.load_all.side_effect = TypeError("wrong type")
            with pytest.raises(ConfigLoadError, match="Config load failed"):
                load_config()


# ── Business Rule Validations ─────────────────────────────────────────────────


class TestBusinessRuleValidations:
    """Tests for business rule validations added via typed validators."""

    def test_memory_retention_days_zero_rejected(self) -> None:
        cfg = {**_MIN_CFG, "memory_retention_days": 0}
        with pytest.raises(ConfigReloadValidationError, match="memory_retention_days"):
            _build_memory_config(cfg)

    def test_memory_retention_days_negative_rejected(self) -> None:
        cfg = {**_MIN_CFG, "memory_retention_days": -1}
        with pytest.raises(ConfigReloadValidationError, match="memory_retention_days"):
            _build_memory_config(cfg)

    def test_memory_embed_timeout_sec_zero_rejected(self) -> None:
        cfg = {**_MIN_CFG, "memory_embed_timeout_sec": 0}
        with pytest.raises(
            ConfigReloadValidationError, match="memory_embed_timeout_sec"
        ):
            _build_memory_config(cfg)

    def test_memory_max_inject_semantic_negative_rejected(self) -> None:
        cfg = {**_MIN_CFG, "memory_max_inject_semantic": -1}
        with pytest.raises(
            ConfigReloadValidationError, match="memory_max_inject_semantic"
        ):
            _build_memory_config(cfg)

    def test_memory_max_inject_episodic_negative_rejected(self) -> None:
        cfg = {**_MIN_CFG, "memory_max_inject_episodic": -1}
        with pytest.raises(
            ConfigReloadValidationError, match="memory_max_inject_episodic"
        ):
            _build_memory_config(cfg)

    def test_tool_safety_tiers_invalid_value_rejected(self) -> None:
        cfg = {**_MIN_CFG, "tool_safety_tiers": {"test_key": "INVALID_TIER"}}
        with pytest.raises(ConfigReloadValidationError, match="tool_safety_tiers"):
            _build_approval_config(cfg)

    def test_tool_safety_tiers_valid_values_accepted(self) -> None:
        cfg = {
            **_MIN_CFG,
            "tool_safety_tiers": {
                "read_op": "READ_ONLY",
                "write_op": "WRITE_SAFE",
                "danger_op": "WRITE_DANGEROUS",
                "admin_op": "ADMIN",
            },
        }
        result = _build_approval_config(cfg)
        assert result.tool_safety_tiers == cfg["tool_safety_tiers"]
