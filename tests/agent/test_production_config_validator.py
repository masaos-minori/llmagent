from __future__ import annotations

import pytest
from agent.production_config_validator import ProductionConfigValidator
from shared.component_mandatoriness import (
    ComponentClassification,
    load_component_mandatoriness,
)


class TestProductionConfigValidatorSafetyTiers:
    """Tests for bidirectional tool_safety_tiers validation."""

    def test_missing_safety_tier_produces_error_in_production(self) -> None:
        known_tools = {"shell_execute", "file_read"}
        config = {
            "tool_safety_tiers": {"shell_execute": "low"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(config, known_tools=known_tools)
        assert any("'file_read'" in err for err in result.errors)
        assert result.warnings == []

    def test_unknown_safety_tier_key_produces_error_in_production(self) -> None:
        known_tools = {"shell_execute", "file_read"}
        config = {
            "tool_safety_tiers": {"unknown_tool": "high"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(config, known_tools=known_tools)
        assert any("unknown_tool" in err for err in result.errors)
        assert result.warnings == []

    def test_both_missing_and_unknown_produce_errors_in_production(self) -> None:
        known_tools = {"shell_execute", "file_read", "github_search"}
        config = {
            "tool_safety_tiers": {"unknown_tool": "high"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(config, known_tools=known_tools)
        assert any(
            "missing" in err.lower() or "'file_read'" in err for err in result.errors
        )
        assert any(
            "unknown" in err.lower() or "unknown_tool" in err for err in result.errors
        )

    def test_no_safety_tiers_config_no_tier_errors(self) -> None:
        config: dict[str, object] = {}
        result = ProductionConfigValidator().validate(config)
        assert not any("safety tier" in err.lower() for err in result.errors)

    def test_empty_safety_tiers_dict_no_tier_errors(self) -> None:
        config: dict[str, object] = {"tool_safety_tiers": {}, "known_tools": set()}
        result = ProductionConfigValidator().validate(config, known_tools=set())
        assert not any("safety tier" in err.lower() for err in result.errors)

    def test_all_tiers_present_no_errors(self) -> None:
        known_tools = {"shell_execute", "file_read"}
        config = {
            "tool_safety_tiers": {"shell_execute": "low", "file_read": "medium"},
            "known_tools": known_tools,
        }
        result = ProductionConfigValidator().validate(config, known_tools=known_tools)
        assert not any("safety tier" in err.lower() for err in result.errors)


class TestProductionConfigValidatorRegistryLookupFailClosed:
    """Tests for the fail-closed tool registry lookup (REQ-001)."""

    @pytest.mark.parametrize(
        "exception_type",
        [ValueError, ImportError],
    )
    def test_registry_lookup_failure_records_error_not_skip(
        self, monkeypatch: pytest.MonkeyPatch, exception_type: type[Exception]
    ) -> None:
        """When resolving known_tools from the registry raises, a validation
        error is recorded rather than the checks being silently skipped."""

        def _raise() -> None:
            raise exception_type("registry unavailable")

        monkeypatch.setattr("shared.tool_registry.get_registry", _raise)
        config = {"tool_safety_tiers": {"mystery_tool": "low"}}
        result = ProductionConfigValidator().validate(config)
        assert any("Tool registry resolution failed" in err for err in result.errors)
        # Safety tier checks should NOT produce additional errors since they were
        # short-circuited by the registry failure error already recorded
        assert not any("safety tier" in err.lower() for err in result.errors)


class TestProductionConfigValidatorAllowedTools:
    """Tests for allowed_tools=[] visibility check."""

    def test_allowed_tools_empty_produces_error_in_production(self) -> None:
        config: dict[str, object] = {"allowed_tools": []}
        result = ProductionConfigValidator().validate(config)
        assert any("allowed_tools" in err and "[]" in err for err in result.errors)
        assert result.warnings == []

    def test_allowed_tools_nonempty_no_issue(self) -> None:
        config = {"allowed_tools": ["shell_execute"]}
        result = ProductionConfigValidator().validate(config)
        assert not any("allowed_tools" in err for err in result.errors)
        assert not any("allowed_tools" in warn for warn in result.warnings)

    def test_allowed_tools_none_no_issue(self) -> None:
        config: dict[str, object] = {}
        result = ProductionConfigValidator().validate(config)
        assert not any("allowed_tools" in err for err in result.errors)


class TestProductionConfigValidatorApprovalRiskFloor:
    """Tests for the git write-tool approval risk floor check (REQ-001)."""

    GIT_TOOLS = {"git_checkout", "git_pull", "git_push"}

    def test_all_git_tools_high_no_issue(self) -> None:
        config = {
            "approval_risk_rules": {
                "git_checkout": "high",
                "git_pull": "high",
                "git_push": "high",
            },
        }
        result = ProductionConfigValidator().validate(
            config, known_tools=self.GIT_TOOLS
        )
        assert not any("Effective risk below HIGH" in err for err in result.errors)

    def test_one_git_tool_medium_produces_error_in_production(self) -> None:
        config = {
            "approval_risk_rules": {
                "git_checkout": "medium",
                "git_pull": "high",
                "git_push": "high",
            },
        }
        result = ProductionConfigValidator().validate(
            config, known_tools=self.GIT_TOOLS
        )
        assert any(
            "Effective risk below HIGH" in err and "git_checkout" in err
            for err in result.errors
        )
        assert result.warnings == []

    def test_one_git_tool_invalid_value_produces_error_in_production(self) -> None:
        """'low' is not a valid RiskLevel — classify_risk() would raise ValueError
        at call time in production, so the floor check must flag it rather than
        silently skip it."""
        config = {
            "approval_risk_rules": {
                "git_checkout": "low",
                "git_pull": "high",
                "git_push": "high",
            },
        }
        result = ProductionConfigValidator().validate(
            config, known_tools=self.GIT_TOOLS
        )
        assert any(
            "Effective risk below HIGH" in err and "git_checkout" in err
            for err in result.errors
        )

    def test_git_tool_absent_from_rules_falls_back_to_tier_default(self) -> None:
        """No approval_risk_rules entry but tool_safety_tiers=WRITE_DANGEROUS
        implicitly resolves to MEDIUM and must still be flagged."""
        config = {
            "approval_risk_rules": {"git_pull": "high", "git_push": "high"},
            "tool_safety_tiers": {"git_checkout": "WRITE_DANGEROUS"},
        }
        result = ProductionConfigValidator().validate(
            config, known_tools=self.GIT_TOOLS
        )
        assert any(
            "Effective risk below HIGH" in err and "git_checkout" in err
            for err in result.errors
        )

    def test_git_tools_absent_from_both_no_issue(self) -> None:
        """No override anywhere: classify_risk()'s UNKNOWN path treats this as
        HIGH, so the floor check must not flag it."""
        config: dict[str, object] = {}
        result = ProductionConfigValidator().validate(
            config, known_tools=self.GIT_TOOLS
        )
        assert not any("Effective risk below HIGH" in err for err in result.errors)

    def test_approval_risk_rules_absent_still_checks_tier_fallback(self) -> None:
        """The floor check must run even when approval_risk_rules is entirely
        absent from config, not only when it is an empty/partial Mapping."""
        config = {"tool_safety_tiers": {"git_checkout": "WRITE_DANGEROUS"}}
        result = ProductionConfigValidator().validate(
            config, known_tools=self.GIT_TOOLS
        )
        assert any(
            "Effective risk below HIGH" in err and "git_checkout" in err
            for err in result.errors
        )


class TestProductionConfigValidatorValidateUnknownToolSafetyTiers:
    """Tests for standalone validate_unknown_tool_safety_tiers method."""

    def test_empty_list_returns_no_errors(self) -> None:
        result = ProductionConfigValidator().validate_unknown_tool_safety_tiers([])
        assert result.errors == []

    def test_single_unknown_key(self) -> None:
        result = ProductionConfigValidator().validate_unknown_tool_safety_tiers(["mdq"])
        assert len(result.errors) == 1
        assert "mdq" in result.errors[0]

    def test_multiple_unknown_keys(self) -> None:
        result = ProductionConfigValidator().validate_unknown_tool_safety_tiers(
            ["mdq", "unknown_tool"]
        )
        assert len(result.errors) == 2
        assert "mdq" in result.errors[0] or "mdq" in result.errors[1]
        assert "unknown_tool" in result.errors[0] or "unknown_tool" in result.errors[1]


class TestProductionConfigValidatorUnknownTopLevelKeys:
    """Tests for general unknown top-level key rejection (REQ-004)."""

    def test_valid_keys_only_no_errors(self) -> None:
        config = {
            "system_prompt_tool": "",
        }
        result = ProductionConfigValidator().validate(config)
        assert not any("Unknown config keys" in err for err in result.errors)

    def test_single_unknown_key_produces_error(self) -> None:
        config = {"unknown_mistyped_key": True}
        result = ProductionConfigValidator().validate(config)
        assert any(
            "Unknown config keys" in err and "unknown_mistyped_key" in err
            for err in result.errors
        )

    def test_eventbus_db_path_key_is_rejected(self) -> None:
        """eventbus.sqlite belongs to the EventBus service: agent.toml must not
        carry its path, so the removed key is reported as unknown."""
        config = {
            "eventbus_db_path": "/opt/llm/db/eventbus.sqlite",
        }
        result = ProductionConfigValidator().validate(config)
        assert any(
            "Unknown config keys" in err and "eventbus_db_path" in err
            for err in result.errors
        )

    def test_rag_identity_mismatch_policy_key_is_rejected(self) -> None:
        """The fallback identity gate was removed with the remote RAG delegation
        path: agent.toml must not carry its policy key, so it is reported as unknown."""
        config = {
            "rag_identity_mismatch_policy": "reject",
        }
        result = ProductionConfigValidator().validate(config)
        assert any(
            "Unknown config keys" in err and "rag_identity_mismatch_policy" in err
            for err in result.errors
        )

    def test_multiple_unknown_keys_produce_errors(self) -> None:
        config = {
            "unknown_key_1": True,
            "unknown_key_2": True,
        }
        result = ProductionConfigValidator().validate(config)
        assert any("Unknown config keys" in err for err in result.errors)
        assert any("unknown_key_1" in err for err in result.errors)
        assert any("unknown_key_2" in err for err in result.errors)

    def test_empty_config_no_unknown_key_errors(self) -> None:
        config: dict[str, object] = {}
        result = ProductionConfigValidator().validate(config)
        assert not any("Unknown config keys" in err for err in result.errors)

    def test_removed_security_lockdown_key_is_rejected(self) -> None:
        """The deny-all suppression knob was removed with its only consumer,
        agent/services/security_audit.py; a stale key left in agent.toml is a hard error."""
        config = {"security_lockdown_enabled": True}
        result = ProductionConfigValidator().validate(config)
        assert any(
            "Unknown config keys" in err and "security_lockdown_enabled" in err
            for err in result.errors
        )


class TestProductionConfigValidatorConfigValidationResultIdentity:
    """Tests for ConfigValidationResult identity after REQ-004 consolidation."""

    def test_config_validation_result_identity(self) -> None:
        """REQ-004: production_config_validator.ConfigValidationResult IS shared.config_validator.ConfigValidationResult."""
        from agent.production_config_validator import (
            ConfigValidationResult as PCVResult,
        )
        from shared.config_validator import ConfigValidationResult as CVResult

        assert PCVResult is CVResult

    def test_validate_unknown_tool_safety_tiers_single_arg_construction(self) -> None:
        """REQ-004: validate_unknown_tool_safety_tiers()'s single-arg construction still works."""
        validator = ProductionConfigValidator()
        result = validator.validate_unknown_tool_safety_tiers(["unknown_tool"])
        assert isinstance(result, object)
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")


class TestProductionConfigValidatorValidKeySetUnchanged:
    """Tests for valid-key set stability after REQ-006 schema consolidation."""

    def test_valid_key_set_unchanged_after_schema_consolidation(self) -> None:
        """REQ-006: the valid-key set is unchanged after consolidating _get_valid_production_keys()."""
        from agent.production_config_validator import _get_valid_production_keys

        keys = _get_valid_production_keys()
        assert "agent_memory_max_startup_snippets" in keys
        assert "system_prompt_tool" in keys
        assert "security_profile" not in keys
        assert "tool_definitions_strict" not in keys
        assert "routing_drift_strict" not in keys
        assert "embed_url" in keys
        assert "refiner_max_tokens" not in keys


@pytest.mark.integration
def test_integration_real_config_agent_toml() -> None:
    """REQ-007: real config/agent.toml passes both validators with zero errors."""
    from pathlib import Path

    # Load the real config/agent.toml
    config_dir = Path(__file__).resolve().parent.parent.parent / "config"
    from shared.config_loader import ConfigLoader

    loader = ConfigLoader(config_dir=config_dir)
    cfg = loader.load_all(strict=True)

    # Validate with RagConfigValidator
    from shared.config_validator import RagConfigValidator

    rag_result = RagConfigValidator().validate(cfg)
    assert rag_result.ok is True
    assert len(rag_result.errors) == 0

    # Validate with ProductionConfigValidator
    prod_result = ProductionConfigValidator().validate(cfg)
    assert prod_result.ok is True
    assert len(prod_result.errors) == 0


def _mandatoriness_entry(
    component_id: str, classification: str
) -> ComponentClassification:
    """A structurally complete ComponentClassification for synthetic registries."""

    return ComponentClassification(
        component_id=component_id,
        classification=classification,
        failure_category="safety-integrity",
        safety_role="Baseline safety role.",
        safely_disableable_functions=frozenset(),
        startup_consequence="abort_startup",
        observability=frozenset(),
        owner="agent-architecture-owner",
        authority_adr="ADR-004",
        rationale="Baseline rationale text.",
    )


class TestComponentMandatorinessCrossCheck:
    """REQ-004 / AC-3: validate_against_registry fail-closed regressions."""

    def test_required_false_conflicts_with_registry_required(self) -> None:
        registry = {"cicd": _mandatoriness_entry("cicd", "required")}
        errors = ProductionConfigValidator().validate_against_registry(
            registry, {"cicd": False}
        )

        assert len(errors) == 1
        err = errors[0]
        assert "cicd" in err
        assert "classification 'required'" in err
        assert "required=False" in err
        assert "registry/component_mandatoriness.yaml" in err

    def test_configured_server_absent_from_registry_is_error(self) -> None:
        registry: dict[str, ComponentClassification] = {}
        errors = ProductionConfigValidator().validate_against_registry(
            registry, {"ghost_server": True}
        )

        assert len(errors) == 1
        assert "ghost_server" in errors[0]
        assert "absent from the mandatoriness registry" in errors[0]
        assert "registry/component_mandatoriness.yaml" in errors[0]

    def test_non_required_server_configured_false_is_no_error(self) -> None:
        registry = {"web_search": _mandatoriness_entry("web_search", "non_required")}
        errors = ProductionConfigValidator().validate_against_registry(
            registry, {"web_search": False}
        )

        assert errors == []

    def test_orphan_registry_entry_is_not_an_error(self) -> None:
        registry = {
            "cicd": _mandatoriness_entry("cicd", "required"),
            "ghost": _mandatoriness_entry("ghost", "required"),
        }
        errors = ProductionConfigValidator().validate_against_registry(
            registry, {"cicd": True}
        )

        # 'ghost' is classified but has no configured server -> warning, not error.
        assert errors == []

    def test_live_registry_agrees_with_all_required_config(self) -> None:
        registry = load_component_mandatoriness()
        mcp_required = {component_id: True for component_id in registry}
        errors = ProductionConfigValidator().validate_against_registry(
            registry, mcp_required
        )

        # AC-6 guard: the shipped registry and shipped config actually agree.
        assert errors == []


class TestRemovedKeysRejected:
    """ADR-004 Revision 004: the bypass switches have no meaning anymore.

    A config that still sets a removed key is fatal rather than silently
    accepted: the key is no longer in the allowed set.
    """

    @pytest.mark.parametrize(
        "key",
        ["tool_definitions_strict", "routing_drift_strict", "security_profile"],
    )
    def test_removed_key_is_fatal(self, key: str) -> None:
        result = ProductionConfigValidator().validate({key: True})
        assert any("Unknown config keys" in err and key in err for err in result.errors)

    def test_empty_allowed_root_is_fatal(self) -> None:
        # An empty root would disable the approval path jail.
        result = ProductionConfigValidator().validate({"allowed_root": ""})
        assert any("allowed_root" in err for err in result.errors)

    def test_clean_production_config_has_no_errors(self) -> None:
        # The canonical production shape validates without errors.
        result = ProductionConfigValidator().validate(
            {"allowed_root": "/opt/llm", "sqlite_vec_so": "/opt/llm/sqlite-vec/vec0.so"}
        )
        assert result.errors == []


class TestProductionConfigValidatorVecSoRequirement:
    """REQ-005: validate() reports an empty or absent sqlite_vec_so.

    Written first and shown failing before
    scripts/agent/production_config_validator.py gains the check.
    """

    def test_empty_vec_so_reports_error(self) -> None:
        result = ProductionConfigValidator().validate({"sqlite_vec_so": ""})
        assert any("sqlite_vec_so" in err for err in result.errors)

    def test_absent_key_reports_error(self) -> None:
        result = ProductionConfigValidator().validate({})
        assert any("sqlite_vec_so" in err for err in result.errors)

    def test_non_empty_missing_file_reports_none(self) -> None:
        result = ProductionConfigValidator().validate(
            {"allowed_root": "/opt/llm", "sqlite_vec_so": "/nonexistent/vec0.so"}
        )
        assert result.errors == []
