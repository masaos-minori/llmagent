from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest
from agent.production_config_validator import ProductionConfigValidator
from shared.component_mandatoriness import (
    ComponentClassification,
    load_component_mandatoriness,
)
from shared.runtime_tool_registry import RuntimeToolRegistry

from tests.shared.runtime_tool_factory import build_fixture_runtime_tool


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
        config: dict[str, object] = {}
        result = ProductionConfigValidator().validate(config)
        assert any("Tool registry resolution failed" in err for err in result.errors)


class TestProductionConfigValidatorAllowedTools:
    """allowed_tools shape checks. The unconditional empty-list rejection was
    removed (REQ-003): emptiness is now mode-dependent and owned by the
    mode-aware typed validators, so production validation records no error for
    an empty list here.

    REQ-003: an empty allowed_tools is no longer fatal unconditionally at
    production validation; emptiness is valid in discovered mode and owned by
    the mode-aware typed validators.
    """

    def test_allowed_tools_empty_no_production_error(self) -> None:
        """REQ-003: an empty allowed_tools is NOT recorded as an error here
        (the blanket rejection was removed); enforcement is mode-aware."""
        config: dict[str, object] = {"allowed_tools": []}
        result = ProductionConfigValidator().validate(config)
        assert not any("allowed_tools" in err for err in result.errors)

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
    """Git write-tool risk floor read from declared metadata (REQ-004, REQ-011).

    The floor is a lower bound on the declared tier's mapped risk: the named git
    write tools must not declare a tier that maps to NONE, and a registered tool
    with no usable declaration is reported fail-closed. The removed config maps
    no longer feed the check.
    """

    GIT_TOOLS = {"git_checkout", "git_pull", "git_push"}

    @staticmethod
    def _registry(entries: dict[str, Any]) -> RuntimeToolRegistry:
        return RuntimeToolRegistry(
            tools=dict(entries), allowed_servers=frozenset({"git"})
        )

    def _floor(self, tiers: dict[str, str]):
        registry = self._registry(
            {
                name: build_fixture_runtime_tool(name, "git", agent_safety_tier=tier)
                for name, tier in tiers.items()
            }
        )
        return ProductionConfigValidator().validate(
            {}, known_tools=self.GIT_TOOLS, runtime_tools=registry
        )

    def _floor_errors(self, result) -> list[str]:
        return [err for err in result.errors if "below floor" in err]

    def test_all_git_tools_declare_write_dangerous_no_issue(self) -> None:
        """The shipped declaration (WRITE_DANGEROUS -> MEDIUM) clears the floor."""
        result = self._floor({tool: "WRITE_DANGEROUS" for tool in self.GIT_TOOLS})
        assert self._floor_errors(result) == []

    def test_admin_tier_no_issue(self) -> None:
        result = self._floor({tool: "ADMIN" for tool in self.GIT_TOOLS})
        assert self._floor_errors(result) == []

    def test_none_risk_declared_tier_produces_error_in_production(self) -> None:
        """A git write tool declaring a NONE-risk tier breaks the floor."""
        tiers = {tool: "WRITE_DANGEROUS" for tool in self.GIT_TOOLS}
        tiers["git_checkout"] = "WRITE_SAFE"
        result = self._floor(tiers)
        floor_errors = self._floor_errors(result)
        assert any("git_checkout" in err for err in floor_errors)

    def test_missing_declared_tier_fail_closed(self) -> None:
        """A registered git tool without the declared field is reported, not skipped."""
        entries: dict[str, object] = {
            name: build_fixture_runtime_tool(name, "git")
            for name in ("git_pull", "git_push")
        }
        entries["git_checkout"] = SimpleNamespace(name="git_checkout", server_key="git")
        result = ProductionConfigValidator().validate(
            {}, known_tools=self.GIT_TOOLS, runtime_tools=self._registry(entries)
        )
        floor_errors = self._floor_errors(result)
        assert any(
            "git_checkout" in err and "missing declared agent_safety_tier" in err
            for err in floor_errors
        )

    def test_unrecognized_declared_tier_produces_error(self) -> None:
        """A tier value outside the closed set is reported rather than defaulted."""
        entries: dict[str, object] = {
            name: build_fixture_runtime_tool(name, "git")
            for name in ("git_pull", "git_push")
        }
        entries["git_checkout"] = SimpleNamespace(
            name="git_checkout", server_key="git", agent_safety_tier="BOGUS"
        )
        result = ProductionConfigValidator().validate(
            {}, known_tools=self.GIT_TOOLS, runtime_tools=self._registry(entries)
        )
        floor_errors = self._floor_errors(result)
        assert any(
            "git_checkout" in err and "unrecognized declared tier" in err
            for err in floor_errors
        )

    def test_git_tool_absent_from_runtime_registry_not_flagged(self) -> None:
        """classify_risk() resolves an unregistered tool to HIGH (UNKNOWN
        fail-safe), so the floor must not flag what the registry does not carry."""
        registry = self._registry(
            {
                "git_checkout": build_fixture_runtime_tool(
                    "git_checkout", "git", agent_safety_tier="WRITE_DANGEROUS"
                )
            }
        )
        result = ProductionConfigValidator().validate(
            {}, known_tools=self.GIT_TOOLS, runtime_tools=registry
        )
        assert self._floor_errors(result) == []

    def test_no_runtime_registry_defers_the_floor(self) -> None:
        """Config build runs before discovery: without a registry there is no
        declared source, and enforcement defers to the schema gate,
        classify_risk() and the drift report."""
        result = ProductionConfigValidator().validate({}, known_tools=self.GIT_TOOLS)
        assert self._floor_errors(result) == []

    def test_removed_maps_no_longer_feed_the_floor(self) -> None:
        """REQ-011: a stale tool_safety_tiers entry cannot satisfy or break the
        floor — the map is rejected as an unknown key instead."""
        registry = self._registry(
            {
                name: build_fixture_runtime_tool(name, "git")
                for name in ("git_checkout", "git_pull")
            }
        )
        result = ProductionConfigValidator().validate(
            {"tool_safety_tiers": {"git_push": "READ_ONLY"}},
            known_tools=self.GIT_TOOLS,
            runtime_tools=registry,
        )
        assert any(
            "Unknown config keys" in err and "tool_safety_tiers" in err
            for err in result.errors
        )
        assert self._floor_errors(result) == []


class TestProductionConfigValidatorUnknownTopLevelKeys:
    """Tests for general unknown top-level key rejection (REQ-004)."""

    def test_removed_prompt_keys_are_rejected_as_unknown(self) -> None:
        config = {
            "system_prompt_tool": "",
            "system_prompts": {"default": ""},
        }
        result = ProductionConfigValidator().validate(config)
        for name in ("system_prompt_tool", "system_prompts"):
            assert any(
                "Unknown config keys" in err and name in err for err in result.errors
            )

    def test_workflow_db_path_key_is_accepted(self) -> None:
        """workflow_db_path is a registered subsystem DB path key (scripts/db/):
        agent.toml carries it and startup validation must accept it."""
        config = {
            "workflow_db_path": "/opt/llm/db/workflow.sqlite",
        }
        result = ProductionConfigValidator().validate(config)
        assert not any(
            "Unknown config keys" in err and "workflow_db_path" in err
            for err in result.errors
        )

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


class TestProductionConfigValidatorValidKeySetUnchanged:
    """Tests for valid-key set stability after REQ-006 schema consolidation."""

    def test_valid_key_set_unchanged_after_schema_consolidation(self) -> None:
        """REQ-006: the valid-key set is unchanged after consolidating _get_valid_production_keys()."""
        from agent.production_config_validator import _get_valid_production_keys

        keys = _get_valid_production_keys()
        assert "agent_memory_max_startup_snippets" in keys
        assert "system_prompt_tool" not in keys
        assert "system_prompts" not in keys
        assert "security_profile" not in keys
        assert "tool_definitions_strict" not in keys
        assert "routing_drift_strict" not in keys
        assert "memory_embed_url" in keys
        assert "embed_url" not in keys
        assert "refiner_max_tokens" not in keys
        # The maintenance keys are derived through the prefix the file uses: the typed
        # configuration's fields are the same settings without it, so only the prefixed
        # form is accepted.
        assert "sqlite_retention_max_sessions" in keys
        assert "retention_max_sessions" not in keys


class TestProductionConfigValidatorRefinerKeys:
    """REQ-006: refiner keys are rejected by the named rule, not by key derivation.

    Moved from tests/agent/test_config_builders.py with the RAG builder that reported
    them; check_agent_refiner_keys() is called from validate(), so the message stays.
    """

    @pytest.mark.parametrize(
        "key",
        [
            "use_refiner",
            "refiner_max_tokens",
            "refiner_timeout",
            "refiner_max_chars_per_chunk",
        ],
    )
    def test_leftover_refiner_key_is_rejected(self, key: str) -> None:
        result = ProductionConfigValidator().validate({key: 1})
        assert any(
            "rag_pipeline_mcp_server.toml" in err and key in err
            for err in result.errors
        )

    def test_agentcfg003_removed_maps_are_out_of_the_valid_key_set(self) -> None:
        """REQ-011: the removed per-tool maps are subtracted from the introspected set."""
        from agent.production_config_validator import _get_valid_production_keys

        keys = _get_valid_production_keys()
        for key in (
            "tool_safety_tiers",
            "approval_risk_rules",
            "approval_resource_keys",
            "approval_dry_run_tools",
        ):
            assert key not in keys


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

    @pytest.mark.parametrize(
        "key",
        [
            "tool_safety_tiers",
            "approval_risk_rules",
            "approval_resource_keys",
            "approval_dry_run_tools",
        ],
    )
    def test_agentcfg003_removed_map_is_fatal(self, key: str) -> None:
        """REQ-011 (AC-05): a config that still sets a removed per-tool map is
        fatal with the key named — no compatibility reader keeps it alive."""
        result = ProductionConfigValidator().validate({key: {}})
        assert any("Unknown config keys" in err and key in err for err in result.errors)


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
