"""tests/test_config_builders.py
Unit tests for agent/config_builders.py and agent/config_section_builders.py:
_build_llm_config, _build_approval_config, _build_memory_config,
_build_tool_config, build_agent_config, and load_config error handling.
"""

from __future__ import annotations

import logging
from unittest.mock import MagicMock, patch

import pytest
from agent.config_builders import (
    ConfigLoadError,
    build_agent_config,
    load_config,
)
from agent.config_dataclasses import AgentConfig
from agent.config_section_builders import (
    _build_approval_config,
    _build_diagnostics_config,
    _build_llm_config,
    _build_memory_config,
    _build_tool_config,
    _get_or_default,
    _get_str_or_default,
)
from agent.services.exceptions import ConfigReloadValidationError
from agent.services.typed_validators import _get_int, _get_str
from cryptography.fernet import Fernet

from tests.agent._config_test_defaults import SHIPPED_DB_PATH_KEYS

# Minimal config satisfying _build_mcp_servers (needs at least one HTTP server with url) and
# build_agent_config(): the typed DB configuration is built from the mapping, so the shipped
# path keys come from the shared mirror, and memory_embed_enabled defaults to True, so
# memory_embed_url must be non-empty.
_MIN_CFG: dict = {
    "mcp_servers": {
        "test-server": {
            "transport": "http",
            "url": "http://127.0.0.1:9999",
            "auth_token": "test-token",
        }
    },
    **SHIPPED_DB_PATH_KEYS,
    "memory_embed_url": "http://127.0.0.1:9999",
    "allowed_root": "/opt/llm",
}

_LLM_DEFAULTS = {
    "llm_url": "",
    "http_timeout": 30.0,
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
            _build_llm_config({"llm_max_tokens": "5", "llm_temperature": "0.5"})

    def test_every_field_override_is_independently_reflected(self) -> None:
        # Guards each individual cfg-key -> field mapping (not just a couple of
        # spot-checked fields) so a typo'd key string in the extraction helper
        # calls is caught.
        overrides = {
            "llm_url": "http://override",
            "http_timeout": 99.0,
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


# ── _build_tool_config ────────────────────────────────────────────────────────


_TOOL_DEFAULTS = {
    "serial_tool_calls": False,
    "tool_dedup_max_repeats": 3,
    "tool_cycle_detect_window": 2,
    "tool_error_max_consecutive": 3,
    "tool_error_retry_max": 1,
    "tool_unavailable_repeat_max_repeats": 0,
    "tool_concurrency_limits": {},
    "masked_fields": ["content", "old_text", "new_text"],
    "plan_blocked_tools": [
        "write_file",
        "create_directory",
        "delete_file",
        "delete_directory",
    ],
    "max_tool_turns": 5,
    "tool_result_max_llm_chars": 8000,
    "tool_results_turn_max_chars": 50000,
    "allowed_tools": [],
}


class TestBuildToolConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_tool_config({})
        for key, value in _TOOL_DEFAULTS.items():
            assert getattr(cfg, key) == value, key

    def test_every_field_override_is_independently_reflected(self) -> None:
        overrides = {
            "serial_tool_calls": True,
            "tool_dedup_max_repeats": 9,
            "tool_cycle_detect_window": 9,
            "tool_error_max_consecutive": 9,
            "tool_error_retry_max": 9,
            "tool_unavailable_repeat_max_repeats": 9,
            "tool_concurrency_limits": {"srv": 2},
            "masked_fields": ["custom_field"],
            "plan_blocked_tools": ["custom_tool"],
            "max_tool_turns": 9,
            "tool_result_max_llm_chars": 9,
            "tool_results_turn_max_chars": 9,
            "allowed_tools": ["tool_a"],
        }
        cfg = _build_tool_config(overrides)
        for key, value in overrides.items():
            assert getattr(cfg, key) == value, key


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
    "memory_embed_url": "",
}


class TestBuildMemoryConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        # The enabled-gated URL check now lives in MemoryConfig with the key (Plan
        # row 1), so the URL must be supplied for the defaults to be reachable; its
        # default is asserted by the disabled case below.
        cfg = _build_memory_config({"memory_embed_url": "http://localhost:8080"})
        for key, value in _MEMORY_DEFAULTS.items():
            if key == "memory_embed_url":
                continue
            assert getattr(cfg, key) == value, key

    def test_memory_embed_url_defaults_to_empty(self) -> None:
        # Read with embedding disabled: the default alone is what is being asserted.
        cfg = _build_memory_config({"memory_embed_enabled": False})
        assert cfg.memory_embed_url == ""

    def test_memory_embed_url_reflects_a_supplied_value(self) -> None:
        cfg = _build_memory_config({"memory_embed_url": "http://embed"})
        assert cfg.memory_embed_url == "http://embed"

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
    """agentcfg003 REQ-005: the builder produces only the kept operational
    fields; the removed per-tool maps are rejected upstream as unknown keys."""

    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_approval_config({"allowed_root": "/opt/llm"})
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
        assert cfg.allowed_root == "/opt/llm"
        assert cfg.approval_github_allowed_repos == []
        assert cfg.gitops_push_blocked is False

    def test_removed_map_fields_are_not_built(self) -> None:
        cfg = _build_approval_config({"allowed_root": "/opt/llm"})
        for removed in (
            "approval_risk_rules",
            "approval_resource_keys",
            "approval_dry_run_tools",
            "tool_safety_tiers",
        ):
            assert not hasattr(cfg, removed), removed

    @pytest.mark.parametrize(
        "key",
        [
            "tool_safety_tiers",
            "approval_risk_rules",
            "approval_resource_keys",
            "approval_dry_run_tools",
        ],
    )
    def test_removed_key_is_rejected_as_unknown_key(self, key: str) -> None:
        """REQ-011: a stale deployed config still naming a removed map is
        rejected with the key named, not silently ignored."""
        from agent.production_config_validator import ProductionConfigValidator

        result = ProductionConfigValidator().validate({**_MIN_CFG, key: {}})
        assert any(key in e for e in result.errors), result.errors

    def test_empty_allowed_root_rejected(self) -> None:
        with pytest.raises(ValueError, match="allowed_root"):
            _build_approval_config({"allowed_root": ""})

    def test_absent_allowed_root_rejected(self) -> None:
        with pytest.raises(ValueError, match="allowed_root"):
            _build_approval_config({})

    def test_every_field_override_is_independently_reflected(self) -> None:
        overrides: dict = {
            "approval_protected_paths": ["/custom/"],
            "approval_high_risk_branches": ["custom-branch"],
            "approval_shell_safe_prefixes": ["custom-cmd"],
            "allowed_root": "/custom/root",
            "approval_github_allowed_repos": ["org/repo"],
            "gitops_push_blocked": True,
        }
        cfg = _build_approval_config(overrides)
        for key, value in overrides.items():
            assert getattr(cfg, key) == value, key


# ── _build_diagnostics_config ─────────────────────────────────────────────────


class TestBuildDiagnosticsConfig:
    def test_empty_dict_returns_defaults(self) -> None:
        cfg = _build_diagnostics_config({})
        assert cfg.encryption_key == ""
        assert cfg.retention_days == 30

    def test_overrides_are_applied(self) -> None:
        key = Fernet.generate_key().decode("utf-8")
        cfg = _build_diagnostics_config(
            {"diagnostics": {"encryption_key": key, "retention_days": 7}}
        )
        assert cfg.encryption_key == key
        assert cfg.retention_days == 7

    def test_missing_diagnostics_table_returns_defaults(self) -> None:
        cfg = _build_diagnostics_config({"llm_url": "http://llm.local"})
        assert cfg.encryption_key == ""
        assert cfg.retention_days == 30

    def test_sensitive_fields_override_is_reflected(self) -> None:
        cfg = _build_diagnostics_config(
            {"diagnostics": {"sensitive_fields": ["custom_field", "another_field"]}}
        )
        # Union with defaults happens in _filter_sensitive_fields() at use time,
        # not in _build_diagnostics_config(). Assert raw configured value.
        assert cfg.sensitive_fields == frozenset(["custom_field", "another_field"])

    def test_invalid_fernet_key_raises_config_reload_validation_error(self) -> None:
        # REQ-002 / AC-3: a malformed DiagnosticsConfig value fails the build path
        # with a named error (via _build_model wrapping __post_init__'s ValueError).
        with pytest.raises(ConfigReloadValidationError, match="encryption_key"):
            _build_diagnostics_config(
                {"diagnostics": {"encryption_key": "not-a-valid-fernet-key"}}
            )

    def test_wrong_typed_retention_raises_config_reload_validation_error(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="retention_days"):
            _build_diagnostics_config({"diagnostics": {"retention_days": 30.0}})


# ── build_agent_config ────────────────────────────────────────────────────────


class TestBuildAgentConfig:
    def test_returns_agent_config_instance(self) -> None:
        cfg = build_agent_config(
            {
                **_MIN_CFG,
            }
        )
        assert isinstance(cfg, AgentConfig)

    @pytest.mark.parametrize(
        "key",
        ["tool_definitions_strict", "routing_drift_strict", "security_profile"],
    )
    def test_removed_keys_rejected_by_build_agent_config(self, key: str) -> None:
        # Removed keys are no longer in the allowed set: the production
        # validator rejects them and the build raises.
        with pytest.raises(ConfigReloadValidationError, match="Unknown config keys"):
            build_agent_config({**_MIN_CFG, key: True})

    def test_top_level_bool_and_observability_overrides_reflected(self) -> None:
        cfg = build_agent_config(
            {
                **_MIN_CFG,
                "otel_enabled": True,
                "structured_log": True,
                "otel_endpoint": "http://otel",
                "otel_service_name": "custom-svc",
                "audit_log_file": "/custom/audit.log",
            }
        )
        assert cfg.obs.otel_enabled is True
        assert cfg.obs.structured_log is True
        assert cfg.obs.otel_endpoint == "http://otel"
        assert cfg.obs.otel_service_name == "custom-svc"
        assert cfg.obs.audit_log_file == "/custom/audit.log"

    def test_removed_security_lockdown_field_is_absent(self) -> None:
        """The deny-all suppression knob was removed together with its only consumer,
        agent/services/security_audit.py (ADR-004: no configuration can downgrade a
        Safety/Integrity posture failure)."""
        from dataclasses import fields

        from agent.config_dataclasses import MCPConfig

        assert "security_lockdown_enabled" not in {f.name for f in fields(MCPConfig)}

    def test_production_validation_passes_without_exit(self) -> None:
        # Companion to test_production_validation_errors_raises: proves the
        # ConfigReloadValidationError path is specifically gated on results.errors.
        build_agent_config(
            {
                **_MIN_CFG,
                "allowed_tools": ["some_tool"],
            }
        )

    def test_llm_defaults_reflected(self) -> None:
        cfg = build_agent_config(
            {
                **_MIN_CFG,
            }
        )
        assert cfg.llm.llm_url == ""

    def test_diagnostics_defaults_reflected(self) -> None:
        cfg = build_agent_config(
            {
                **_MIN_CFG,
            }
        )
        assert cfg.diagnostics.encryption_key == ""
        assert cfg.diagnostics.retention_days == 30

    def test_none_cfg_override_calls_load_config(self) -> None:
        with patch("agent.config_builders.ConfigLoader") as MockLoader:
            MockLoader.return_value.load_all.return_value = {
                **_MIN_CFG,
            }
            cfg = build_agent_config(None)
        assert isinstance(cfg, AgentConfig)

    def test_production_validation_errors_raises(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        # A validator stub returning errors makes build_agent_config log and
        # raise ConfigReloadValidationError.
        cfg = {**_MIN_CFG}
        with (
            caplog.at_level(logging.ERROR, logger="agent.config_builders"),
            patch(
                "agent.production_config_validator.ProductionConfigValidator.validate"
            ) as mock_validate,
        ):
            mock_validate.return_value = MagicMock(errors=["error1"], warnings=[])
            with pytest.raises(ConfigReloadValidationError):
                build_agent_config(cfg)
        assert any(
            "Production config validation failed" in r.message for r in caplog.records
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

    def test_raises_on_missing_required_config_file(self) -> None:
        """REQ-002 regression: after REQ-001 makes load_all() strict by default,
        build_agent_config(None) must fail fast when agent.toml is missing,
        preventing the config build from ever running on a stale
        fallback path."""
        from shared.config_errors import ConfigMissingError

        with patch("agent.config_builders.ConfigLoader") as MockLoader:
            MockLoader.return_value.load_all.side_effect = ConfigMissingError(
                "Config file not found: /opt/llm/config/agent.toml"
            )
            with pytest.raises(
                ConfigLoadError, match=r"Config load failed \(ConfigMissingError"
            ):
                build_agent_config(None)


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


# ── Resolver wiring + PyYAML dependency (REQ-002 / REQ-005) ───────────────────


class TestResolvedConfigDir:
    """REQ-002: resolved_config_dir() delegates to the shared resolver."""

    def test_resolved_config_dir_is_resolver_derived(self) -> None:
        """resolved_config_dir() returns resolve_config_dir() (no stale scripts/config)."""
        from pathlib import Path

        from agent.config_builders import resolved_config_dir
        from shared.runtime_paths import resolve_config_dir

        resolved = resolved_config_dir()
        assert resolved == resolve_config_dir()
        assert isinstance(resolved, Path)


class TestPyYAMLImport:
    """REQ-005: PyYAML is a declared dependency and importable."""

    def test_import_yaml_resolves(self) -> None:
        """import yaml resolves (PyYAML>=6.0 is a direct dependency of llmagent)."""
        import yaml

        assert hasattr(yaml, "safe_load")
        assert hasattr(yaml, "dump")


# ── Characterization tests for the paths the suite left uncovered ─────────────
#
# These lock behavior the refactor of scripts/agent/config_builders.py must
# preserve: the diagnostics sensitive_fields fallback, the tool-registry failure
# conversion, the production-validation warning path, and the single empty-string
# fallback rule (`_or_default`: an absent key and an explicit "" both fall back to
# the default).


class TestDiagnosticsSensitiveFieldsFallback:
    """Characterization: a non-list sensitive_fields becomes an empty frozenset."""

    def test_list_becomes_a_frozenset(self) -> None:
        cfg = _build_diagnostics_config(
            {"diagnostics": {"sensitive_fields": ["api_key", "token"]}}
        )

        assert cfg.sensitive_fields == frozenset({"api_key", "token"})

    def test_non_list_becomes_an_empty_frozenset(self) -> None:
        cfg = _build_diagnostics_config(
            {"diagnostics": {"sensitive_fields": "api_key"}}
        )

        assert cfg.sensitive_fields == frozenset()

    def test_absent_key_becomes_an_empty_frozenset(self) -> None:
        assert _build_diagnostics_config({}).sensitive_fields == frozenset()


class TestToolRegistryFailureConversion:
    """Characterization: both registry failure modes become ConfigReloadValidationError."""

    def test_value_error_is_rewrapped_with_the_registry_prefix(self) -> None:
        with patch("agent.config_builders.get_registry") as mock_registry:
            mock_registry.return_value.get_all_tool_names.side_effect = ValueError(
                "duplicate tool name"
            )

            with pytest.raises(
                match="Tool registry resolution failed during config build: duplicate tool name",
            ):
                build_agent_config({**_MIN_CFG})

    def test_import_error_is_rewrapped_with_the_registry_prefix(self) -> None:
        with patch("agent.config_builders.get_registry") as mock_registry:
            mock_registry.return_value.get_all_tool_names.side_effect = ImportError(
                "registry module missing"
            )

            with pytest.raises(
                match="Tool registry module unavailable during config build: registry module missing",
            ):
                build_agent_config({**_MIN_CFG})


class TestProductionValidationWarningPath:
    """Characterization: warnings are logged and never abort the build."""

    def test_warnings_are_logged_and_the_build_completes(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        cfg = {
            **_MIN_CFG,
        }
        with (
            caplog.at_level(logging.WARNING, logger="agent.config_builders"),
            patch(
                "agent.production_config_validator.ProductionConfigValidator.validate"
            ) as mock_validate,
        ):
            mock_validate.return_value = MagicMock(errors=[], warnings=["warn one"])
            result = build_agent_config(cfg)

        assert isinstance(result, AgentConfig)
        assert any("warn one" in r.message for r in caplog.records)


class TestEmptyStringFallbackIdioms:
    """Characterization: one fallback rule — absent key and explicit "" both fall back."""

    def test_empty_string_and_absent_key_both_yield_the_default(self) -> None:
        assert _build_llm_config({"llm_url": ""}).llm_url == ""
        assert _build_llm_config({"llm_url": None}).llm_url == ""

    def test_non_empty_default_replaces_an_explicit_empty_string(self) -> None:
        """A builder default wins over an explicit "" in the config."""
        cfg = build_agent_config(
            {
                **_MIN_CFG,
                "otel_service_name": "",
                "audit_log_file": "",
                "memory_jsonl_dir": "",
            }
        )

        assert cfg.obs.otel_service_name == "llm-agent"
        assert cfg.obs.audit_log_file == "/opt/llm/logs/audit.log"
        assert cfg.memory.memory_jsonl_dir == "/opt/llm/memory"

    def test_get_str_or_default_treats_empty_string_as_unset(self) -> None:
        assert _get_str_or_default({"k": ""}, "k", "fallback") == "fallback"

    def test_get_or_default_treats_empty_string_as_unset(self) -> None:
        assert _get_or_default({"k": ""}, "k", _get_str, "fallback") == "fallback"

    def test_get_or_default_keeps_a_present_value(self) -> None:
        assert _get_or_default({"k": 7}, "k", _get_int, 3) == 7


# ── Builder exception type (P22) ──────────────────────────────────────────────


class TestBuilderExceptionTypeUniformity:
    """Every builder reports a rejected value as ConfigReloadValidationError.

    Before `_build_model()` only the memory and approval builders wrapped the failure,
    so `context_char_limit=-1` reached the caller as a bare dataclass ValueError while
    `memory_fts_limit=0` arrived as a ConfigReloadValidationError.
    """

    def test_llm_builder_wraps_a_negative_char_limit(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="context_char_limit"):
            _build_llm_config({"context_char_limit": -1})

    def test_tool_builder_wraps_a_zero_dedup_limit(self) -> None:
        with pytest.raises(ConfigReloadValidationError, match="tool_dedup_max_repeats"):
            _build_tool_config({"tool_dedup_max_repeats": 0})
