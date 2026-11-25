"""
tests/test_tool_policy.py
Unit tests for tool_policy.py: risk classification, path/repo checks, pre-flight deny.
"""

from __future__ import annotations

from collections.abc import Mapping
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_audit import _extract_resource_scope
from agent.tool_enums import OperationType, RiskLevel
from agent.tool_exceptions import PolicyViolationError
from agent.tool_policy import (
    check_allowed_repo,
    check_allowed_root,
    check_preflight,
    check_write_classification,
    classify_operation_type,
    classify_risk,
    is_plan_mode_blocked,
)
from shared.runtime_tool import AgentSafetyTier
from shared.runtime_tool_registry import RuntimeTool, RuntimeToolRegistry
from shared.tool_metadata import (
    TOOL_FIELD_SET_VERSION,
    ResourceKeyKind,
    SideEffectClass,
)

from tests.agent._config_test_defaults import SHIPPED_DB_PATH_KEYS
from tests.agent._producer_registry import PRODUCER_TIERS

# Every tool name this file passes to the policy functions; the _cfg default
# allowlist must contain them so the deny-on-empty behavior (REQ-002) does not
# interfere with tests that target other axes. Denial tests override the list.
_POLICY_TEST_TOOLS = [
    "any_tool",
    "custom_list_tool",
    "delete_directory",
    "delete_file",
    "dry_run",
    "git_status",
    "github_push_files",
    "not_registered_tool",
    "read",
    "read_multiple_files",
    "read_text_file",
    "shell_run",
    "totally_unregistered_tool_xyz",
    "unknown_tool",
    "write_file",
]


def _cfg(**overrides: Any) -> AgentConfig:
    """Build an AgentConfig for tool_policy.py unit tests.

    This intentionally bypasses ProductionConfigValidator (patched below):
    these tests construct deliberately empty/narrow allowed_tools,
    tool_safety_tiers, and approval_risk_rules to exercise tool_policy.py's
    own fallback logic, which is a different concern from whether the
    resulting config would be accepted as production-ready.
    """
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "llm_retry_base_delay": 1.0,
        "serial_tool_calls": False,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": _POLICY_TEST_TOOLS,
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_protected_paths": [],
        "approval_github_allowed_repos": [],
        "approval_high_risk_branches": [],
        "approval_shell_safe_prefixes": [],
        "approval_resource_keys": {"path_keys": [], "branch_keys": []},
        "allowed_root": "/",
        # memory_embed_enabled now defaults to True; memory_embed_url must be non-empty
        # to satisfy MemoryConfig.__post_init__'s cross-field validation.
        "memory_embed_url": "http://127.0.0.1:9999",
        # build_agent_config() resolves the typed DB configuration from the mapping, so the fixture supplies the mirrored path keys.
        **SHIPPED_DB_PATH_KEYS,
        "mcp_servers": {
            "dummy": {
                "transport": "http",
                "url": "http://127.0.0.1:9999",
                "auth_token": "test-token",
            }
        },
    }
    defaults.update(overrides)
    with patch("agent.config_builders.ProductionConfigValidator") as mock_validator:
        mock_validator.return_value.validate.return_value.errors = []
        mock_validator.return_value.validate.return_value.warnings = []
        return build_agent_config(defaults)


# Post-change shipped approval_shell_safe_prefixes (shellprefix001 seq 02): the config
# gates the executable; the code-side safe-shape rule decides subcommand/flag
# acceptability. Interpreters and test runners are absent from the list by design (REQ-006).
SHELL_PREFIXES_STRICT = ["ls", "cat", "echo", "git", "pwd", "find", "grep"]


def _runtime_tool(
    name: str,
    scope_keys: Mapping[str, ResourceKeyKind] | None = None,
    *,
    is_write: bool = False,
    tier: str = "READ_ONLY",
    side_effect_class: str = "read_only",
) -> RuntimeTool:
    """Build a RuntimeTool stub with the schema-2.1 required fields filled in.

    Defaults describe a read-only tool; tests targeting write-class behavior
    pass ``tier``/``is_write``/``side_effect_class`` explicitly.
    """
    keys = dict(scope_keys or {})
    return RuntimeTool(
        name=name,
        server_key="test_server",
        server_url="",
        description="",
        input_schema={},
        raw_definition={},
        status="active",
        is_write=is_write,
        requires_serial=False,
        resource_scope_kind="filesystem" if keys else "",
        resource_scope_keys=keys,
        agent_safety_tier=cast(AgentSafetyTier, tier),
        side_effect_class=cast(SideEffectClass, side_effect_class),
        retry_policy="safe_read_retry",
        reconciliation_policy="not_required",
        idempotency_required=False,
        preview_capability="none",
        policy_version=TOOL_FIELD_SET_VERSION,
        enabled_for_llm=True,
        capabilities=(),
    )


def _stub_registry(
    **scope_keys_by_tool: Mapping[str, ResourceKeyKind],
) -> RuntimeToolRegistry:
    """Registry stub whose tools declare the given key-to-kind mapping."""
    return RuntimeToolRegistry(
        tools={
            name: _runtime_tool(name, keys) for name, keys in scope_keys_by_tool.items()
        },
        allowed_servers=frozenset({"test_server"}),
    )


def _write_registry(
    **scope_keys_by_tool: Mapping[str, ResourceKeyKind],
) -> RuntimeToolRegistry:
    """Registry stub whose tools declare WRITE_DANGEROUS tier and local_write."""
    return RuntimeToolRegistry(
        tools={
            name: _runtime_tool(
                name,
                keys,
                tier="WRITE_DANGEROUS",
                is_write=True,
                side_effect_class="local_write",
            )
            for name, keys in scope_keys_by_tool.items()
        },
        allowed_servers=frozenset({"test_server"}),
    )


class TestClassifyOperationType:
    def test_github_mutation_tools_classified_as_api_write(self) -> None:
        from shared.tool_constants import (
            GITHUB_DANGEROUS_TOOLS,
            GITHUB_WRITE_TOOLS,
        )

        mutation_set = GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
        reg = RuntimeToolRegistry(
            tools={
                name: _runtime_tool(
                    name,
                    is_write=True,
                    tier="WRITE_SAFE",
                    side_effect_class="external_write",
                )
                for name in mutation_set
            },
            allowed_servers=frozenset({"test_server"}),
        )
        for tool_name in mutation_set:
            assert classify_operation_type(tool_name, reg) == OperationType.API_WRITE

    def test_declared_side_effect_class_is_the_authority(self) -> None:
        """REQ-007: a read_only declaration resolves READ even when the static
        reference sets classify the tool as a write tool."""
        reg = _stub_registry(delete_file={"path": "path"})
        assert classify_operation_type("delete_file", reg) == OperationType.READ

    def test_declared_write_class_subclassified_by_reference_sets(self) -> None:
        reg = RuntimeToolRegistry(
            tools={
                "delete_file": _runtime_tool(
                    "delete_file",
                    {"path": "path"},
                    is_write=True,
                    tier="WRITE_DANGEROUS",
                    side_effect_class="local_write",
                ),
                "shell_run": _runtime_tool(
                    "shell_run",
                    is_write=True,
                    tier="WRITE_DANGEROUS",
                    side_effect_class="local_write",
                ),
                "git_add": _runtime_tool(
                    "git_add",
                    {"repo_path": "path"},
                    is_write=True,
                    tier="WRITE_SAFE",
                    side_effect_class="local_write",
                ),
            },
            allowed_servers=frozenset({"test_server"}),
        )
        assert classify_operation_type("delete_file", reg) == OperationType.DELETE
        assert classify_operation_type("shell_run", reg) == OperationType.EXECUTE
        assert classify_operation_type("git_add", reg) == OperationType.WRITE


class TestWriteClassificationDrift:
    """REQ-007: declared-vs-static disagreement is a drift finding, never a
    decision change; check_write_classification() reports it."""

    def test_drift_finding_reported_but_declaration_decides(self) -> None:
        reg = _stub_registry(delete_file={"path": "path"})  # read_only declaration
        findings = check_write_classification(reg)
        assert any("delete_file" in f for f in findings)
        assert classify_operation_type("delete_file", reg) == OperationType.READ

    def test_consistent_registry_produces_no_findings(self) -> None:
        reg = _write_registry(write_file={"path": "path"})
        assert check_write_classification(reg) == []


class TestClassifyRisk:
    @staticmethod
    def _registry_with(**tier_by_tool: str) -> RuntimeToolRegistry:
        tool_map: dict[str, RuntimeTool] = {}
        for t, tier in tier_by_tool.items():
            tool_map[t] = _runtime_tool(
                t,
                tier=tier,
                is_write=tier != "READ_ONLY",
                side_effect_class="read_only" if tier == "READ_ONLY" else "local_write",
            )
        return RuntimeToolRegistry(
            tools=tool_map, allowed_servers=frozenset({"test_server"})
        )

    def test_force_flag_returns_high(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "write_file", {"force": True})
        assert result == "high"

    def test_overwrite_flag_returns_high(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "write_file", {"overwrite": True})
        assert result == "high"

    def test_clobber_flag_returns_high(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "write_file", {"clobber": True})
        assert result == "high"

    def test_recursive_delete_returns_high(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "delete_directory", {"recursive": True})
        assert result == "high"

    def test_non_recursive_delete_fails_closed_without_registry(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "delete_directory", {"recursive": False})
        assert result == "high"

    def test_write_dangerous_tier_tool_with_no_path_match_returns_medium(self) -> None:
        cfg = _cfg()
        reg = self._registry_with(custom_list_tool="WRITE_DANGEROUS")
        result = classify_risk(cfg, "custom_list_tool", {"path": "/tmp/f"}, reg)
        assert result == "medium"

    def test_read_only_tier_returns_none(self) -> None:
        cfg = _cfg()
        reg = self._registry_with(read_text_file="READ_ONLY")
        result = classify_risk(cfg, "read_text_file", {"path": "/tmp/f"}, reg)
        assert result == "none"

    def test_protected_path_escalates_to_high(self) -> None:
        cfg = _cfg(approval_protected_paths=["/opt/llm/"])
        reg = _write_registry(write_file={"path": "path"})
        result = classify_risk(cfg, "write_file", {"path": "/opt/llm/config"}, reg)
        assert result == "high"

    def test_non_protected_path_no_escalation(self) -> None:
        cfg = _cfg(approval_protected_paths=["/opt/llm/"])
        reg = _write_registry(write_file={"path": "path"})
        result = classify_risk(cfg, "write_file", {"path": "/home/user/file.txt"}, reg)
        assert result == "medium"

    def test_declared_tier_is_the_single_risk_source(self) -> None:
        """REQ-004/REQ-011: approval_risk_rules no longer feed classify_risk.
        A leftover rule cannot soften the fail-closed HIGH of an unregistered
        call, and the declared tier decides when the tool is registered."""
        cfg = _cfg(approval_risk_rules={"write_file": "none"})
        assert classify_risk(cfg, "write_file", {}) == "high"
        reg = self._registry_with(write_file="WRITE_SAFE")
        assert classify_risk(cfg, "write_file", {}, reg) == "none"

    def test_force_flag_does_not_override_none_tier(self) -> None:
        cfg = _cfg()
        reg = self._registry_with(write_file="WRITE_SAFE")
        result = classify_risk(cfg, "write_file", {"force": True}, reg)
        assert result == "none"


class TestCheckAllowedRoot:
    def test_allows_path_within_root(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(write_file={"path": "path"})
        assert check_allowed_root(cfg, "write_file", {"path": "/home/user/doc.md"}, reg)

    def test_denies_path_outside_root(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(write_file={"path": "path"})
        assert not check_allowed_root(cfg, "write_file", {"path": "/tmp/foo"}, reg)

    def test_empty_root_denies_path_bearing_call(self) -> None:
        """REQ-003: an empty allowed_root (reachable via /reload) denies a call
        with a path argument and still passes a pathless call."""
        cfg = _cfg()
        cfg.approval.allowed_root = ""
        reg = _stub_registry(write_file={"path": "path"})
        assert not check_allowed_root(cfg, "write_file", {"path": "/any/path"}, reg)
        assert check_allowed_root(cfg, "write_file", {}, reg)

    def test_no_matching_keys_allows(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(write_file={})
        assert check_allowed_root(cfg, "write_file", {}, reg)

    def test_declared_path_key_absent_from_args_allows(self) -> None:
        """A declared path key missing from args must be skipped
        (not treated as a violation)."""
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(write_file={"path": "path"})
        assert check_allowed_root(cfg, "write_file", {}, reg)

    def test_registry_omitted_fails_closed(self) -> None:
        """REQ-008: with no registry the declared scope is unknown, so the jail
        cannot be verified; the call denies rather than falling back to
        configured keys."""
        cfg = _cfg(allowed_root="/home")
        assert not check_allowed_root(cfg, "write_file", {"path": "/home/user/doc.md"})
        assert not check_allowed_root(cfg, "write_file", {})


class TestDeclaredScopeKeys:
    """REQ-008 (agentcfg003): the declared key-to-kind mapping is the only key
    source for the path checks.

    These exercise list-valued path arguments, fail-closed on unexpected value
    types, and fail-closed on an unregistered tool.
    """

    def test_list_paths_one_outside_root_denied(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(read_multiple_files={"paths": "path"})
        assert not check_allowed_root(
            cfg, "read_multiple_files", {"paths": ["/home/a", "/tmp/b"]}, reg
        )

    def test_list_paths_all_inside_allowed(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(read_multiple_files={"paths": "path"})
        assert check_allowed_root(
            cfg, "read_multiple_files", {"paths": ["/home/a", "/home/b"]}, reg
        )

    def test_declared_repo_path_outside_root_denied(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(git_clone={"repo_path": "path"})
        assert not check_allowed_root(cfg, "git_clone", {"repo_path": "/tmp/x"}, reg)

    def test_present_non_string_value_fails_closed(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(read_multiple_files={"paths": "path"})
        assert not check_allowed_root(cfg, "read_multiple_files", {"paths": 123}, reg)

    def test_list_element_non_string_fails_closed(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(read_multiple_files={"paths": "path"})
        assert not check_allowed_root(
            cfg, "read_multiple_files", {"paths": ["/home/a", 5]}, reg
        )

    def test_unregistered_tool_fails_closed(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(read_multiple_files={"paths": "path"})
        # write_file is not in the registry -> fail closed (deny), never open.
        assert not check_allowed_root(cfg, "write_file", {"path": "/home/a"}, reg)

    def test_check_preflight_threads_registry(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(read_multiple_files={"paths": "path"})
        with pytest.raises(PolicyViolationError):
            check_preflight(
                cfg, "read_multiple_files", {"paths": ["/home/a", "/tmp/b"]}, reg
            )

    def test_escalate_for_path_checks_declared_key(self) -> None:
        from agent.tool_enums import RiskLevel
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg(approval_protected_paths=["/etc"])
        reg = _stub_registry(git_clone={"repo_path": "path"})
        result = _escalate_for_path(
            cfg, "git_clone", RiskLevel.MEDIUM, {"repo_path": "/etc/passwd"}, reg
        )
        assert result == RiskLevel.HIGH

    def test_branch_kind_key_is_not_path_checked(self) -> None:
        """T-04: kind filtering — a branch-kind key never enters the jail check
        or the protected-path escalation, only path-kind keys do."""
        from agent.tool_enums import RiskLevel
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg(allowed_root="/home", approval_protected_paths=["/etc"])
        reg = _stub_registry(custom_list_tool={"path": "path", "branch": "branch"})
        assert check_allowed_root(
            cfg, "custom_list_tool", {"path": "/home/a", "branch": "/etc/x"}, reg
        )
        assert (
            _escalate_for_path(
                cfg, "custom_list_tool", RiskLevel.MEDIUM, {"branch": "/etc/x"}, reg
            )
            is None
        )


class TestCfgHelperDefaults:
    def test_unknown_tool_defaults_to_high_risk(self) -> None:
        # was: test_unknown_tool_defaults_to_medium_risk asserting "medium" -- now "high"
        # per this plan's fail-safe acceptance criterion for unregistered tools.
        cfg = _cfg()
        assert classify_risk(cfg, "unknown_tool", {}) == "high"

    def test_shell_run_no_command_defaults_to_high_risk(self) -> None:
        cfg = _cfg()
        assert classify_risk(cfg, "shell_run", {}) == "high"

    def test_empty_root_pathless_call_passes(self) -> None:
        cfg = _cfg()
        cfg.approval.allowed_root = ""
        reg = _stub_registry(write_file={"path": "path"})
        assert check_allowed_root(cfg, "write_file", {}, reg) is True
        assert (
            check_allowed_root(cfg, "write_file", {"path": "/any/absolute/path"}, reg)
            is False
        )


class TestCheckAllowedRepo:
    def test_allows_api_write_to_allowed_repo(self) -> None:
        cfg = _cfg(approval_github_allowed_repos=["myorg/allowed-repo"])
        assert check_allowed_repo(
            cfg, "github_push_files", {"owner": "myorg", "repo": "allowed-repo"}
        )

    def test_denies_api_write_to_other_repo(self) -> None:
        cfg = _cfg(approval_github_allowed_repos=["myorg/allowed-repo"])
        assert not check_allowed_repo(
            cfg, "github_push_files", {"owner": "myorg", "repo": "other-repo"}
        )

    def test_empty_allowed_repos_denies_all_github_writes(self) -> None:
        cfg = _cfg(approval_github_allowed_repos=[])
        assert not check_allowed_repo(
            cfg, "github_push_files", {"owner": "myorg", "repo": "repo"}
        )

    def test_non_github_tool_always_allowed(self) -> None:
        cfg = _cfg(approval_github_allowed_repos=[])
        assert check_allowed_repo(cfg, "write_file", {})

    def test_missing_owner_or_repo_not_in_allowed(self) -> None:
        cfg = _cfg(approval_github_allowed_repos=["myorg/repo"])
        assert not check_allowed_repo(
            cfg, "github_push_files", {"owner": "", "repo": ""}
        )


class TestCheckPreflight:
    def test_passes_when_all_checks_pass(self) -> None:
        cfg = _cfg(approval_github_allowed_repos=[])
        reg = _stub_registry(read_text_file={"path": "path"})
        check_preflight(
            cfg, "read_text_file", {"path": "/tmp/f"}, reg
        )  # does not raise

    def test_denied_by_allowed_tools(self) -> None:
        cfg = _cfg(allowed_tools=["read_text_file"])
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "write_file", {})
        assert exc_info.value.audit_decision == "denied_allowed_tools"
        assert "write_file" in str(exc_info.value)

    def test_empty_allowed_tools_denies_every_tool(self) -> None:
        """REQ-002: an empty allowed_tools is an empty allowlist (AC-02)."""
        cfg = _cfg(allowed_tools=[])
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "any_tool", {})
        assert exc_info.value.audit_decision == "denied_allowed_tools"

    def test_denied_by_root_jail(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(write_file={"path": "path"})
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "write_file", {"path": "/tmp/foo"}, reg)
        assert exc_info.value.audit_decision == "denied_root_jail"

    def test_denied_by_repo_allowlist(self) -> None:
        cfg = _cfg(approval_github_allowed_repos=["myorg/allowed-repo"])
        reg = _stub_registry(
            github_push_files={"owner": "non_escalating", "repo": "repo"}
        )
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(
                cfg, "github_push_files", {"owner": "myorg", "repo": "other-repo"}, reg
            )
        assert exc_info.value.audit_decision == "denied_repo_allowlist"

    def test_dry_run_operations_require_allowed_tools(self) -> None:
        """dry_run must still pass allowed_tools check."""
        cfg = _cfg(
            allowed_tools=["dry_run"],
            allowed_root="/tmp",
            approval_github_allowed_repos=["github.com/example/repo"],
        )
        try:
            check_preflight(cfg, "dry_run", {}, _stub_registry(dry_run={}))
        except PolicyViolationError:
            pytest.fail("dry_run with allowed_tools should pass")

    def test_read_operations_require_allowed_tools(self) -> None:
        """READ must still pass allowed_tools check."""
        cfg = _cfg(
            allowed_tools=["read"],
            allowed_root="/tmp",
            approval_github_allowed_repos=["github.com/example/repo"],
        )
        try:
            check_preflight(cfg, "read", {}, _stub_registry(read={}))
        except PolicyViolationError:
            pytest.fail("READ with allowed_tools should pass")

    def test_t04_gateway_bypass_gap_resolved(self) -> None:
        """T-04: Gateway-bypass path in tool_runner.py is resolved.

        When gateway is None, the preflight check must fire for non-READ operations
        to prevent unauthorized execution. This test verifies the policy layer
        correctly denies unauthorized operations even without a gateway.
        """
        # Non-READ operation without gateway should be denied by preflight
        cfg = _cfg(allowed_tools=["read_text_file"])
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "write_file", {})
        assert exc_info.value.audit_decision == "denied_allowed_tools"

        # READ operation should still pass (per REQ-09 exemption)
        cfg = _cfg(allowed_tools=["read_text_file"])
        reg = _stub_registry(read_text_file={"path": "path"})
        check_preflight(
            cfg, "read_text_file", {"path": "/tmp/f"}, reg
        )  # does not raise

    def test_already_high_base_risk_no_escalation(self) -> None:
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg()
        assert _escalate_for_path(cfg, "write_file", RiskLevel.HIGH, {}) is None

    def test_registered_tool_without_path_keys_returns_none(self) -> None:
        """A registered tool that declares no path-kind keys is not escalated."""
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg()
        reg = _stub_registry(write_file={})
        assert (
            _escalate_for_path(
                cfg, "write_file", RiskLevel.MEDIUM, {"path": "/opt/llm/x"}, reg
            )
            is None
        )

    def test_unknown_declared_scope_fails_closed(self) -> None:
        """REQ-008 fail-closed: unregistered tool or no registry escalates HIGH
        rather than silently checking nothing."""
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg()
        assert (
            _escalate_for_path(
                cfg, "write_file", RiskLevel.MEDIUM, {"path": "/opt/llm/x"}
            )
            == "high"
        )
        assert (
            _escalate_for_path(
                cfg,
                "write_file",
                RiskLevel.MEDIUM,
                {"path": "/opt/llm/x"},
                _stub_registry(),
            )
            == "high"
        )

    def test_declared_path_key_absent_from_args_skipped(self) -> None:
        """A declared path key missing from args must be skipped (not
        treated as a match), leaving the risk unescalated."""
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg(approval_protected_paths=["/etc"])
        reg = _stub_registry(write_file={"path": "path"})
        assert _escalate_for_path(cfg, "write_file", RiskLevel.MEDIUM, {}, reg) is None

    @staticmethod
    def _reg_with(*names: str) -> RuntimeToolRegistry:
        tools = {name: _runtime_tool(name) for name in names}
        return RuntimeToolRegistry(
            tools=tools, allowed_servers=frozenset({"test_server"})
        )

    def test_discovered_mode_allows_registered_tool(self) -> None:
        cfg = _cfg(tool_policy_mode="discovered")
        reg = self._reg_with("read_text_file")
        check_preflight(
            cfg, "read_text_file", {"path": "/tmp/f"}, reg
        )  # does not raise

    def test_discovered_mode_denies_unregistered_tool(self) -> None:
        cfg = _cfg(tool_policy_mode="discovered")
        reg = self._reg_with("read_text_file")
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "totally_unregistered_tool_xyz", {}, reg)
        assert exc_info.value.audit_decision == "denied_discovered"

    def test_discovered_mode_allows_empty_allowed_tools(self) -> None:
        """REQ-004: an empty allowed_tools is valid in discovered mode."""
        cfg = _cfg(tool_policy_mode="discovered", allowed_tools=[])
        reg = self._reg_with("read_text_file")
        check_preflight(
            cfg, "read_text_file", {"path": "/tmp/f"}, reg
        )  # does not raise

    def test_discovered_mode_denies_disabled_tool(self) -> None:
        cfg = _cfg(
            tool_policy_mode="discovered",
            disabled_tools=["read_text_file"],
            allowed_tools=[],
        )
        reg = self._reg_with("read_text_file")
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "read_text_file", {"path": "/tmp/f"}, reg)
        assert exc_info.value.audit_decision == "denied_discovered"


class TestEscalateForGithubBranch:
    def test_unregistered_tool_returns_none(self) -> None:
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg()
        assert (
            _escalate_for_github_branch(cfg, "write_file", RiskLevel.MEDIUM, {}) is None
        )

    def test_already_high_base_risk_no_escalation(self) -> None:
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg()
        assert (
            _escalate_for_github_branch(cfg, "github_push_files", RiskLevel.HIGH, {})
            is None
        )

    def test_declared_branch_key_absent_from_args_skipped(self) -> None:
        """A declared branch-kind key missing from args must be skipped (not
        treated as a match), leaving the risk unescalated."""
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg(approval_high_risk_branches=["main"])
        reg = _stub_registry(github_push_files={"branch": "branch"})
        assert (
            _escalate_for_github_branch(
                cfg, "github_push_files", RiskLevel.MEDIUM, {}, reg
            )
            is None
        )

    def test_high_risk_branch_escalates(self) -> None:
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg(approval_high_risk_branches=["main"])
        reg = _stub_registry(github_push_files={"branch": "branch"})
        assert (
            _escalate_for_github_branch(
                cfg, "github_push_files", RiskLevel.MEDIUM, {"branch": "main"}, reg
            )
            == "high"
        )

    def test_no_branch_kind_declaration_no_escalation(self) -> None:
        """REQ-008: escalation follows the declared key kind, not the tool-name
        prefix — a registered github_ tool with no branch-kind key is never
        branch-escalated."""
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg(approval_high_risk_branches=["main"])
        reg = _stub_registry(
            github_push_files={"repo": "repo", "owner": "non_escalating"}
        )
        assert (
            _escalate_for_github_branch(
                cfg, "github_push_files", RiskLevel.MEDIUM, {"branch": "main"}, reg
            )
            is None
        )


class TestCheckAllowedRootEdgeCases:
    def test_invalid_path_returns_false(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(write_file={"path": "path"})
        assert not check_allowed_root(cfg, "write_file", {"path": "\0invalid"}, reg)


class TestClassifyRiskDeclaredTier:
    """REQ-004/REQ-011: the declared tier is the single risk source; the
    tool_constants fallback and the approval_risk_rules priority no longer exist."""

    def test_delete_tool_fails_closed_without_registry(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "delete_file", {})
        assert result == "high"

    def test_delete_directory_no_recursive_fails_closed_without_registry(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "delete_directory", {"recursive": False})
        assert result == "high"

    def test_shell_tool_fails_closed_without_registry(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "shell_run", {})
        assert result == "high"

    def test_write_dangerous_tier_resolves_medium(self) -> None:
        cfg = _cfg()
        reg = _write_registry(write_file={"path": "path"})
        result = classify_risk(cfg, "write_file", {"path": "/tmp/f"}, reg)
        assert result == "medium"

    def test_declared_tier_replaces_removed_rules(self) -> None:
        """A leftover approval_risk_rules entry has no effect: the declared tier
        alone decides (REQ-011 config removal)."""
        cfg = _cfg(approval_risk_rules={"delete_file": "medium"})
        reg = RuntimeToolRegistry(
            tools={
                "delete_file": _runtime_tool(
                    "delete_file",
                    {"path": "path"},
                    tier="WRITE_SAFE",
                    is_write=True,
                    side_effect_class="local_write",
                )
            },
            allowed_servers=frozenset({"test_server"}),
        )
        result = classify_risk(cfg, "delete_file", {}, reg)
        assert result == "none"

    def test_recursive_flag_special_case_still_escalates_from_medium(self) -> None:
        cfg = _cfg()
        reg = _write_registry(delete_directory={"path": "path"})
        assert (
            classify_risk(cfg, "delete_directory", {"recursive": True}, reg) == "high"
        )
        assert (
            classify_risk(cfg, "delete_directory", {"recursive": False}, reg)
            == "medium"
        )

    def test_read_only_tier_tool_resolves_none(self) -> None:
        cfg = _cfg()
        reg = _stub_registry(custom_list_tool={})
        result = classify_risk(cfg, "custom_list_tool", {}, reg)
        assert result == "none"


class TestClassifyOperationTypeUnknown:
    def test_unregistered_tool_returns_unknown(self) -> None:
        from agent.tool_enums import OperationType

        assert (
            classify_operation_type("totally_unregistered_tool_xyz")
            == OperationType.UNKNOWN
        )


class TestClassifyRiskUnknown:
    def test_unregistered_tool_returns_high_risk(self) -> None:
        cfg = _cfg()
        assert classify_risk(cfg, "totally_unregistered_tool_xyz", {}) == "high"

    def test_unregistered_tool_high_risk_not_overridden_by_default_tier_fallback(
        self,
    ) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "totally_unregistered_tool_xyz", {})
        assert result != "medium"
        assert result == "high"


class TestPrefixCollision:
    """REQ-005: prefix collisions must be rejected — a command whose name merely
    starts with a safe-prefix entry must not receive RiskLevel.NONE."""

    def test_category_dump_does_not_match_cat_prefix(self) -> None:
        """REQ-005: a command whose name merely starts with 'cat' must not
        receive RiskLevel.NONE just because 'cat' is in approval_shell_safe_prefixes."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "category_dump_secrets"})
        assert result == "high"

    def test_bin_cat_matches_cat_prefix_via_basename(self) -> None:
        """REQ-001: /bin/cat should match the 'cat' prefix via basename comparison."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "/bin/cat /etc/hostname"})
        assert result == "none"

    def test_git_log_does_not_match_gitlog_prefix(self) -> None:
        """REQ-005: 'git-log' must not match the 'git log' prefix (token boundary)."""
        cfg = _cfg(approval_shell_safe_prefixes=["git log"])
        result = classify_risk(cfg, "shell_run", {"command": "git-log status"})
        assert result == "high"

    def test_cat_with_flag_does_not_match_category_prefix(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["category"])
        result = classify_risk(cfg, "shell_run", {"command": "cat --help"})
        assert result == "high"

    def test_partial_token_match_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": "lsof /tmp"})
        assert result == "high"

    def test_full_path_multi_word_prefix_match(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["git log"])
        result = classify_risk(
            cfg, "shell_run", {"command": "/usr/bin/git log --oneline"}
        )
        assert result == "none"

    def test_full_path_multi_word_prefix_mismatch(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["git log"])
        result = classify_risk(cfg, "shell_run", {"command": "/usr/bin/git status"})
        assert result == "high"

    def test_empty_prefix_entry_skipped(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["", "ls"])
        result = classify_risk(cfg, "shell_run", {"command": "ls -la"})
        assert result == "none"

    def test_whitespace_only_prefix_entry_skipped(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["   ", "ls"])
        result = classify_risk(cfg, "shell_run", {"command": "ls -la"})
        assert result == "none"

    def test_quoted_prefix_entry_matches(self) -> None:
        """Quoted prefix entry like '\"git log\"' is a single token after shlex.split,
        so it does NOT match the multi-word command 'git log --oneline'."""
        cfg = _cfg(approval_shell_safe_prefixes=['"git log"'])
        result = classify_risk(cfg, "shell_run", {"command": "git log --oneline"})
        assert result == "high"

    def test_quoted_command_matches_quoted_prefix(self) -> None:
        """A7 strict deny-by-default: shlex collapses the quoted prefix/command into the
        single token 'git log'; that executable has no code-defined safe-shape rule."""
        cfg = _cfg(approval_shell_safe_prefixes=['"git log"'])
        result = classify_risk(cfg, "shell_run", {"command": '"git log"'})
        assert result == "high"

    def test_single_letter_prefix_matches_exact_name(self) -> None:
        """A7 strict deny-by-default: 'c' passes the config gate but has no code-defined
        safe-shape rule, so it is not auto-approved."""
        cfg = _cfg(approval_shell_safe_prefixes=["c"])
        result = classify_risk(cfg, "shell_run", {"command": "c"})
        assert result == "high"

    def test_single_letter_prefix_rejects_longer_name(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["c"])
        result = classify_risk(cfg, "shell_run", {"command": "cat"})
        assert result == "high"

    def test_case_sensitive_prefix_reject(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["Cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat"})
        assert result == "high"

    def test_case_sensitive_prefix_accept(self) -> None:
        """A7 strict deny-by-default: the gate accepts 'Cat' but the executable has no
        code-defined safe-shape rule, so it is not auto-approved."""
        cfg = _cfg(approval_shell_safe_prefixes=["Cat"])
        result = classify_risk(cfg, "shell_run", {"command": "Cat"})
        assert result == "high"

    def test_symlink_basename_match(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "/usr/local/bin/cat"})
        assert result == "none"

    def test_dot_slash_prefix_match(self) -> None:
        """'./cat' prefix is a single token; os.path.basename('./cat') != './cat',
        so it does NOT match the command './cat'."""
        cfg = _cfg(approval_shell_safe_prefixes=["./cat"])
        result = classify_risk(cfg, "shell_run", {"command": "./cat"})
        assert result == "high"

    def test_dot_slash_prefix_reject_different_name(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["./cat"])
        result = classify_risk(cfg, "shell_run", {"command": "./category"})
        assert result == "high"

    def test_trailing_slash_in_prefix_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat/"])
        result = classify_risk(cfg, "shell_run", {"command": "cat"})
        assert result == "high"

    def test_double_space_between_tokens_rejected(self) -> None:
        """shlex.split('git  log') normalizes multiple spaces to single space,
        producing ['git', 'log'], so the prefix 'git  log' also becomes ['git', 'log'].
        Both match, resulting in NONE."""
        cfg = _cfg(approval_shell_safe_prefixes=["git log"])
        result = classify_risk(cfg, "shell_run", {"command": "git  log"})
        assert result == "none"

    def test_tab_between_tokens_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["git\tlog"])
        result = classify_risk(cfg, "shell_run", {"command": "git\tlog"})
        assert result == "none"

    def test_backslash_escape_in_prefix(self) -> None:
        """shlex.split(r'\\$HOME') treats \\$ as literal $, producing ['$HOME'].
        The command '$HOME' also becomes ['$HOME'], so they match — but A7 strict
        deny-by-default: the matched executable '$HOME' has no safe-shape rule."""
        cfg = _cfg(approval_shell_safe_prefixes=[r"\$HOME"])
        result = classify_risk(cfg, "shell_run", {"command": "$HOME"})
        assert result == "high"

    def test_unicode_prefix_rejected_for_ascii_command(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["\u0063at"])
        result = classify_risk(cfg, "shell_run", {"command": "cat"})
        assert result == "none"

    def test_null_byte_in_command_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat\x00/etc/passwd"})
        assert result == "high"

    def test_very_long_command_after_prefix_match(self) -> None:
        long_args = " ".join(["--arg=" + str(i) for i in range(100)])
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": f"echo {long_args}"})
        assert result == "none"

    def test_special_chars_in_arg_value(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": 'echo "hello world"'})
        assert result == "none"

    def test_newline_in_middle_of_command_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat\n/etc/passwd"})
        assert result == "high"

    def test_carriage_return_in_command_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat\r/etc/passwd"})
        assert result == "high"

    def test_multiple_spaces_before_argument(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat   /etc/passwd"})
        assert result == "none"

    def test_leading_whitespace_in_command_stripped_by_shlex(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "  cat /etc/passwd"})
        assert result == "none"

    def test_trailing_whitespace_in_command_stripped_by_shlex(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/passwd  "})
        assert result == "none"

    def test_mixed_quotes_in_command(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": "echo 'hello' \"world\""})
        assert result == "none"

    def test_nested_parentheses_in_arg_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": "echo $(echo $(whoami))"})
        assert result == "high"

    def test_process_substitution_in_arg_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["diff"])
        result = classify_risk(cfg, "shell_run", {"command": "diff <(cat a) <(cat b)"})
        assert result == "high"

    def test_redirection_in_arg_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": "echo hello > /tmp/out"})
        assert result == "high"

    def test_heredoc_in_arg_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat << EOF"})
        assert result == "high"

    def test_glob_pattern_in_arg_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat *.txt"})
        assert result == "none"

    def test_tilde_expansion_in_arg_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat ~/file.txt"})
        assert result == "none"

    def test_environment_variable_in_arg_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat $HOME/file.txt"})
        assert result == "none"

    def test_dollar_brace_in_arg_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat ${HOME}/file.txt"})
        assert result == "none"

    def test_semicolon_with_space_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo ; rm bar"})
        assert result == "high"

    def test_ampersand_with_space_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo & rm bar"})
        assert result == "high"

    def test_pipe_with_space_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo | grep bar"})
        assert result == "high"

    def test_and_operator_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo && rm bar"})
        assert result == "high"

    def test_or_operator_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo || rm bar"})
        assert result == "high"

    def test_backtick_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat `whoami`"})
        assert result == "high"

    def test_dollar_paren_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat $(rm -rf /)"})
        assert result == "high"

    def test_less_than_process_sub_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat <(rm -rf /)"})
        assert result == "high"

    def test_greater_than_process_sub_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat >(rm -rf /)"})
        assert result == "high"

    def test_single_gt_redirection_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat > /tmp/out"})
        assert result == "high"

    def test_single_lt_redirection_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat < /etc/passwd"})
        assert result == "high"

    def test_double_gt_redirection_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat >> /tmp/out"})
        assert result == "high"

    def test_heredoc_operator_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat << EOF"})
        assert result == "high"

    def test_double_heredoc_operator_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat <<< EOF"})
        assert result == "high"

    def test_unsafe_find_exec_flag_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = classify_risk(cfg, "shell_run", {"command": "find . -exec rm {} \\;"})
        assert result == "high"

    def test_unsafe_find_delete_flag_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = classify_risk(cfg, "shell_run", {"command": "find . -delete"})
        assert result == "high"

    def test_unsafe_find_ok_flag_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = classify_risk(cfg, "shell_run", {"command": "find . -ok rm {} \\;"})
        assert result == "high"

    def test_unsafe_grep_recursive_flag_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["grep"])
        result = classify_risk(cfg, "shell_run", {"command": "grep -r pattern ."})
        assert result == "high"

    def test_unsafe_grep_recursive_uppercase_flag_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["grep"])
        result = classify_risk(cfg, "shell_run", {"command": "grep -R pattern ."})
        assert result == "high"

    def test_safe_find_without_unsafe_flags_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = classify_risk(cfg, "shell_run", {"command": "find . -name '*.txt'"})
        assert result == "none"

    def test_safe_grep_without_unsafe_flags_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["grep"])
        result = classify_risk(cfg, "shell_run", {"command": "grep pattern file.txt"})
        assert result == "none"

    def test_cat_protected_path_escalates(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
            approval_protected_paths=["/etc/"],
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/shadow"})
        assert result == "high"

    def test_cat_within_allowed_root_passes(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/home/user",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /home/user/file.txt"})
        assert result == "none"

    def test_cat_outside_allowed_root_escalates(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/tmp",
            approval_resource_keys={"path_keys": [], "branch_keys": []},
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/passwd"})
        assert result == "high"

    def test_positional_arg_value_error_in_resolve_escalates(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/tmp",
            approval_resource_keys={"path_keys": [], "branch_keys": []},
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat \x00invalid"})
        assert result == "high"

    def test_flag_only_no_positional_routing_needed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": "ls -la"})
        assert result == "none"

    def test_empty_command_after_split_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": ""})
        assert result == "high"

    def test_non_string_command_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": 123})
        assert result == "high"

    def test_none_command_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": None})
        assert result == "high"

    def test_unbalanced_quotes_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": 'ls "unbalanced'})
        assert result == "high"

    def test_prefix_collision_category_vs_cat(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["category_dump_secrets"])
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/passwd"})
        assert result == "high"

    def test_prefix_collision_gitlog_vs_git_log(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["git log"])
        result = classify_risk(cfg, "shell_run", {"command": "git-log status"})
        assert result == "high"

    def test_prefix_collision_lsof_vs_ls(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": "lsof /tmp"})
        assert result == "high"

    def test_prefix_collision_pwd_vs_password(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["pwd"])
        result = classify_risk(cfg, "shell_run", {"command": "password"})
        assert result == "high"

    def test_prefix_collision_rm_vs_remove(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["rm"])
        result = classify_risk(cfg, "shell_run", {"command": "remove file"})
        assert result == "high"

    def test_prefix_collision_mv_vs_move(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["mv"])
        result = classify_risk(cfg, "shell_run", {"command": "move file dest"})
        assert result == "high"

    def test_prefix_collision_cp_vs_copy(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cp"])
        result = classify_risk(cfg, "shell_run", {"command": "copy source dest"})
        assert result == "high"

    def test_prefix_collision_ln_vs_link(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ln"])
        result = classify_risk(cfg, "shell_run", {"command": "link source dest"})
        assert result == "high"

    def test_prefix_collision_chmod_vs_chown(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["chmod"])
        result = classify_risk(cfg, "shell_run", {"command": "chown user file"})
        assert result == "high"

    def test_prefix_collision_echo_vs_echoing(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": "echoing message"})
        assert result == "high"

    def test_prefix_collision_head_vs_header(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["head"])
        result = classify_risk(cfg, "shell_run", {"command": "header line"})
        assert result == "high"

    def test_prefix_collision_tail_vs_tailing(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["tail"])
        result = classify_risk(cfg, "shell_run", {"command": "tailing log"})
        assert result == "high"

    def test_prefix_collision_wildcard_match_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["*"])
        result = classify_risk(cfg, "shell_run", {"command": "anything goes"})
        assert result == "high"

    def test_prefix_collision_dot_slash_prefix(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["./cat"])
        result = classify_risk(cfg, "shell_run", {"command": "./category"})
        assert result == "high"

    def test_prefix_collision_absolute_path_basename_match(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(
            cfg, "shell_run", {"command": "/usr/bin/cat /etc/hostname"}
        )
        assert result == "none"

    def test_prefix_collision_symlink_basename_match(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "/usr/local/bin/cat"})
        assert result == "none"

    def test_prefix_collision_quoted_prefix_matches_quoted_command(self) -> None:
        """A7 strict deny-by-default: the quoted prefix/command collapse to the single
        token 'git log', an executable with no code-defined safe-shape rule."""
        cfg = _cfg(approval_shell_safe_prefixes=['"git log"'])
        result = classify_risk(cfg, "shell_run", {"command": '"git log"'})
        assert result == "high"

    def test_prefix_collision_quoted_prefix_rejects_unquoted_command(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=['"git log"'])
        result = classify_risk(cfg, "shell_run", {"command": "git log"})
        assert result == "high"

    def test_prefix_collision_double_space_token_boundary(self) -> None:
        """shlex.split('git  log') normalizes multiple spaces to single space,
        producing ['git', 'log'], so the prefix 'git log' also becomes ['git', 'log'].
        Both match, resulting in NONE."""
        cfg = _cfg(approval_shell_safe_prefixes=["git log"])
        result = classify_risk(cfg, "shell_run", {"command": "git  log"})
        assert result == "none"

    def test_prefix_collision_tab_token_boundary(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["git\tlog"])
        result = classify_risk(cfg, "shell_run", {"command": "git\tlog"})
        assert result == "none"

    def test_prefix_collision_backslash_escape_mismatch(self) -> None:
        """shlex.split(r'\\$HOME') treats \\$ as literal $, producing ['$HOME'].
        The command '$HOME' also becomes ['$HOME'], so they match — but A7 strict
        deny-by-default: the matched executable '$HOME' has no safe-shape rule."""
        cfg = _cfg(approval_shell_safe_prefixes=[r"\$HOME"])
        result = classify_risk(cfg, "shell_run", {"command": "$HOME"})
        assert result == "high"

    def test_prefix_collision_unicode_equality_accepts(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["\u0063at"])
        result = classify_risk(cfg, "shell_run", {"command": "cat"})
        assert result == "none"

    def test_prefix_collision_null_byte_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat\x00/etc/passwd"})
        assert result == "high"

    def test_prefix_collision_long_command_after_prefix_match(self) -> None:
        long_args = " ".join(["--arg=" + str(i) for i in range(100)])
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": f"echo {long_args}"})
        assert result == "none"

    def test_prefix_collision_special_chars_in_arg_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": 'echo "hello world"'})
        assert result == "none"

    def test_prefix_collision_newline_in_middle_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat\n/etc/passwd"})
        assert result == "high"

    def test_prefix_collision_carriage_return_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat\r/etc/passwd"})
        assert result == "high"

    def test_prefix_collision_multiple_spaces_before_argument_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat   /etc/passwd"})
        assert result == "none"

    def test_prefix_collision_leading_whitespace_stripped_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "  cat /etc/passwd"})
        assert result == "none"

    def test_prefix_collision_trailing_whitespace_stripped_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/passwd  "})
        assert result == "none"

    def test_prefix_collision_mixed_quotes_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": "echo 'hello' \"world\""})
        assert result == "none"

    def test_prefix_collision_nested_parentheses_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": "echo $(echo $(whoami))"})
        assert result == "high"

    def test_prefix_collision_process_substitution_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["diff"])
        result = classify_risk(cfg, "shell_run", {"command": "diff <(cat a) <(cat b)"})
        assert result == "high"

    def test_prefix_collision_redirection_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["echo"])
        result = classify_risk(cfg, "shell_run", {"command": "echo hello > /tmp/out"})
        assert result == "high"

    def test_prefix_collision_heredoc_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat << EOF"})
        assert result == "high"

    def test_prefix_collision_glob_pattern_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat *.txt"})
        assert result == "none"

    def test_prefix_collision_tilde_expansion_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat ~/file.txt"})
        assert result == "none"

    def test_prefix_collision_env_var_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat $HOME/file.txt"})
        assert result == "none"

    def test_prefix_collision_dollar_brace_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat ${HOME}/file.txt"})
        assert result == "none"

    def test_prefix_collision_semicolon_with_space_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo ; rm bar"})
        assert result == "high"

    def test_prefix_collision_ampersand_with_space_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo & rm bar"})
        assert result == "high"

    def test_prefix_collision_pipe_with_space_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo | grep bar"})
        assert result == "high"

    def test_prefix_collision_and_operator_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo && rm bar"})
        assert result == "high"

    def test_prefix_collision_or_operator_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo || rm bar"})
        assert result == "high"

    def test_prefix_collision_backtick_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat `whoami`"})
        assert result == "high"

    def test_prefix_collision_dollar_paren_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat $(rm -rf /)"})
        assert result == "high"

    def test_prefix_collision_less_than_process_sub_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat <(rm -rf /)"})
        assert result == "high"

    def test_prefix_collision_greater_than_process_sub_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat >(rm -rf /)"})
        assert result == "high"

    def test_prefix_collision_single_gt_redirection_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat > /tmp/out"})
        assert result == "high"

    def test_prefix_collision_single_lt_redirection_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat < /etc/passwd"})
        assert result == "high"

    def test_prefix_collision_double_gt_redirection_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat >> /tmp/out"})
        assert result == "high"

    def test_prefix_collision_heredoc_operator_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat << EOF"})
        assert result == "high"

    def test_prefix_collision_double_heredoc_operator_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat <<< EOF"})
        assert result == "high"

    def test_prefix_collision_unsafe_find_exec_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = classify_risk(cfg, "shell_run", {"command": "find . -exec rm {} \\;"})
        assert result == "high"

    def test_prefix_collision_unsafe_find_delete_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = classify_risk(cfg, "shell_run", {"command": "find . -delete"})
        assert result == "high"

    def test_prefix_collision_unsafe_find_ok_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = classify_risk(cfg, "shell_run", {"command": "find . -ok rm {} \\;"})
        assert result == "high"

    def test_prefix_collision_unsafe_grep_recursive_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["grep"])
        result = classify_risk(cfg, "shell_run", {"command": "grep -r pattern ."})
        assert result == "high"

    def test_prefix_collision_unsafe_grep_recursive_uppercase_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["grep"])
        result = classify_risk(cfg, "shell_run", {"command": "grep -R pattern ."})
        assert result == "high"

    def test_prefix_collision_safe_find_without_unsafe_flags_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = classify_risk(cfg, "shell_run", {"command": "find . -name '*.txt'"})
        assert result == "none"

    def test_prefix_collision_safe_grep_without_unsafe_flags_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["grep"])
        result = classify_risk(cfg, "shell_run", {"command": "grep pattern file.txt"})
        assert result == "none"

    def test_prefix_collision_cat_protected_path_escalates(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
            approval_protected_paths=["/etc/"],
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/shadow"})
        assert result == "high"

    def test_prefix_collision_cat_within_allowed_root_passes(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/home/user",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /home/user/file.txt"})
        assert result == "none"

    def test_prefix_collision_cat_outside_allowed_root_escalates(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/tmp",
            approval_resource_keys={"path_keys": [], "branch_keys": []},
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/passwd"})
        assert result == "high"

    def test_prefix_collision_positional_arg_value_error_escalates(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/tmp",
            approval_resource_keys={"path_keys": [], "branch_keys": []},
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat \x00invalid"})
        assert result == "high"

    def test_prefix_collision_flag_only_no_positional_routing_needed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": "ls -la"})
        assert result == "none"

    def test_prefix_collision_empty_command_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": ""})
        assert result == "high"

    def test_prefix_collision_non_string_command_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": 123})
        assert result == "high"

    def test_prefix_collision_none_command_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": None})
        assert result == "high"

    def test_prefix_collision_unbalanced_quotes_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = classify_risk(cfg, "shell_run", {"command": 'ls "unbalanced'})
        assert result == "high"


class TestFlagValuePathCandidates:
    """REQ-003 (shellrisk001): the value of a long --flag=value token must reach the
    protected-path and allowed_root checks, identical to the space-separated form."""

    @staticmethod
    def _root_cfg(allowed_root: str) -> AgentConfig:
        return _cfg(
            approval_shell_safe_prefixes=["cat", "grep", "ls", "git"],
            approval_protected_paths=["/etc/"],
            allowed_root=allowed_root,
        )

    def test_flag_value_protected_path_escalates(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        cfg = self._root_cfg(str(tmp_path))
        result = classify_risk(cfg, "shell_run", {"command": "cat --file=/etc/shadow"})
        assert result == "high"

    def test_flag_value_outside_allowed_root_escalates(
        self, tmp_path, monkeypatch
    ) -> None:
        """No protected-path entries configured: the escalation must come from the
        allowed_root check on the flag value."""
        root = tmp_path / "root"
        root.mkdir()
        monkeypatch.chdir(root)
        cfg = _cfg(approval_shell_safe_prefixes=["grep", "ls"], allowed_root=str(root))
        assert (
            classify_risk(cfg, "shell_run", {"command": "grep --include=/etc/shadow x"})
            == "high"
        )
        assert (
            classify_risk(cfg, "shell_run", {"command": "ls --ignore=/etc"}) == "high"
        )

    def test_flag_value_parity_with_separate_token(self, tmp_path, monkeypatch) -> None:
        """The --flag=value form and the space-separated form classify identically."""
        monkeypatch.chdir(tmp_path)
        cfg = self._root_cfg(str(tmp_path))
        for joined, separated in (
            ("cat --file=/etc/shadow", "cat --file /etc/shadow"),
            ("grep --include=/etc/shadow x", "grep --include /etc/shadow x"),
            ("ls --ignore=/etc", "ls --ignore /etc"),
        ):
            assert (
                classify_risk(cfg, "shell_run", {"command": joined})
                == classify_risk(cfg, "shell_run", {"command": separated})
                == "high"
            )

    def test_flag_value_in_root_stays_none(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        cfg = self._root_cfg(str(tmp_path))
        result = classify_risk(cfg, "shell_run", {"command": "cat --file=notes.txt"})
        assert result == "none"

    def test_flag_value_non_path_stays_none(self, tmp_path, monkeypatch) -> None:
        """Fail-closed parity: a non-path value resolves relative to the cwd, which is
        inside allowed_root here."""
        monkeypatch.chdir(tmp_path)
        cfg = self._root_cfg(str(tmp_path))
        assert (
            classify_risk(cfg, "shell_run", {"command": "ls --ignore=*.py"}) == "none"
        )

    def test_bare_flag_and_empty_value_stay_none(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        cfg = self._root_cfg(str(tmp_path))
        assert classify_risk(cfg, "shell_run", {"command": "ls --ignore"}) == "none"
        assert classify_risk(cfg, "shell_run", {"command": "ls --ignore="}) == "none"

    def test_flag_value_nul_escalates(self, tmp_path, monkeypatch) -> None:
        """An embedded NUL escalates through the existing ValueError branch."""
        monkeypatch.chdir(tmp_path)
        cfg = self._root_cfg(str(tmp_path))
        assert (
            classify_risk(cfg, "shell_run", {"command": "cat --file=x\x00y"}) == "high"
        )

    def test_git_diff_output_flag_high_pin(self, tmp_path, monkeypatch) -> None:
        """High pin: reaches high via the shellprefix001 git safe-shape rule, not via
        this flag-value extraction fix."""
        monkeypatch.chdir(tmp_path)
        cfg = self._root_cfg(str(tmp_path))
        assert (
            classify_risk(cfg, "shell_run", {"command": "git diff --output=/etc/x"})
            == "high"
        )


class TestShellSafeShape:
    """REQ-006/REQ-007 (shellprefix001): shell_run auto-approval requires both the config
    gate and a code-defined read-only safe shape; deny-by-default otherwise."""

    @staticmethod
    def _strict_cfg(allowed_root: str) -> AgentConfig:
        return _cfg(
            approval_shell_safe_prefixes=list(SHELL_PREFIXES_STRICT),
            approval_protected_paths=["/etc/", "/opt/"],
            allowed_root=allowed_root,
        )

    def test_python_interpreter_not_auto_approved(self, tmp_path, monkeypatch) -> None:
        root = tmp_path / "root"
        outside = tmp_path / "outside"
        root.mkdir()
        outside.mkdir()
        cfg = self._strict_cfg(str(root))
        monkeypatch.chdir(root)
        assert (
            classify_risk(cfg, "shell_run", {"command": "python -c print(1)"}) == "high"
        )
        monkeypatch.chdir(outside)
        assert (
            classify_risk(cfg, "shell_run", {"command": "python -c print(1)"}) == "high"
        )

    def test_pytest_not_auto_approved(self, tmp_path, monkeypatch) -> None:
        root = tmp_path / "root"
        outside = tmp_path / "outside"
        root.mkdir()
        outside.mkdir()
        cfg = self._strict_cfg(str(root))
        monkeypatch.chdir(root)
        assert classify_risk(cfg, "shell_run", {"command": "pytest tests/"}) == "high"
        monkeypatch.chdir(outside)
        assert classify_risk(cfg, "shell_run", {"command": "pytest tests/"}) == "high"

    def test_uv_run_not_auto_approved(self, tmp_path, monkeypatch) -> None:
        root = tmp_path / "root"
        outside = tmp_path / "outside"
        root.mkdir()
        outside.mkdir()
        cfg = self._strict_cfg(str(root))
        monkeypatch.chdir(root)
        assert classify_risk(cfg, "shell_run", {"command": "uv run pytest"}) == "high"
        monkeypatch.chdir(outside)
        assert classify_risk(cfg, "shell_run", {"command": "uv run pytest"}) == "high"

    def test_git_branch_delete_not_auto_approved(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        cfg = self._strict_cfg(str(tmp_path))
        result = classify_risk(cfg, "shell_run", {"command": "git branch -D feature"})
        assert result == "high"

    def test_git_diff_output_flag_not_auto_approved(
        self, tmp_path, monkeypatch
    ) -> None:
        """Escalation must come from the git safe-shape rule, not the path check: the
        working directory is inside allowed_root."""
        monkeypatch.chdir(tmp_path)
        cfg = self._strict_cfg(str(tmp_path))
        result = classify_risk(
            cfg, "shell_run", {"command": "git diff --output=/tmp/x"}
        )
        assert result == "high"

    def test_full_path_find_delete_escalates(self, tmp_path, monkeypatch) -> None:
        """REQ-008: the normalized basename 'find' must hit the deny-flag rule even when
        the command token is a full path."""
        monkeypatch.chdir(tmp_path)
        cfg = self._strict_cfg(str(tmp_path))
        result = classify_risk(
            cfg, "shell_run", {"command": f"/usr/bin/find {tmp_path} -delete"}
        )
        assert result == "high"

    def test_git_unlisted_subcommand_not_auto_approved(
        self, tmp_path, monkeypatch
    ) -> None:
        """REQ-007: a git subcommand outside allowed_subcommands (and bare git) is not
        auto-approved."""
        monkeypatch.chdir(tmp_path)
        cfg = self._strict_cfg(str(tmp_path))
        for command in ("git", "git checkout main", "git push", "git reset --hard"):
            assert classify_risk(cfg, "shell_run", {"command": command}) == "high"

    def test_git_readonly_forms_remain_none(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        cfg = self._strict_cfg(str(tmp_path))
        for command in (
            "git status",
            "git log --oneline",
            "git diff",
            "git show",
            "git branch",
        ):
            assert classify_risk(cfg, "shell_run", {"command": command}) == "none"

    def test_full_path_git_log_remains_none(self, tmp_path, monkeypatch) -> None:
        monkeypatch.chdir(tmp_path)
        cfg = self._strict_cfg(str(tmp_path))
        result = classify_risk(
            cfg, "shell_run", {"command": "/usr/bin/git log --oneline"}
        )
        assert result == "none"


class TestMetacharacterRejection:
    def test_semicolon_metacharacter_rejected(self) -> None:
        """REQ-005: ';' must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(
            cfg, "shell_run", {"command": "cat /etc/hosts; rm -rf /"}
        )
        assert result == "high"

    def test_ampersand_metacharacter_rejected(self) -> None:
        """REQ-005: '&' must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo & rm bar"})
        assert result == "high"

    def test_pipe_metacharacter_rejected(self) -> None:
        """REQ-005: '|' must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo | sh"})
        assert result == "high"

    def test_backtick_metacharacter_rejected(self) -> None:
        """REQ-005: backtick must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat `whoami`"})
        assert result == "high"

    def test_dollar_paren_metacharacter_rejected(self) -> None:
        """REQ-005: $(...) must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat $'$(rm -rf /)'"})
        assert result == "high"

    def test_double_ampersand_metacharacter_rejected(self) -> None:
        """REQ-005: '&&' must cause HIGH regardless of prefix match."""
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat foo && rm bar"})
        assert result == "high"


class TestPathArgumentConstraints:
    def test_cat_protected_path_escalates(self) -> None:
        """REQ-003: cat on a protected path must escalate to HIGH."""
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
            approval_protected_paths=["/etc/"],
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/shadow"})
        assert result == "high"

    def test_cat_within_allowed_root_passes(self) -> None:
        """REQ-003: cat within allowed_root must pass path checks."""
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/home/user",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /home/user/file.txt"})
        assert result == "none"


class TestDeclaredKeyAuthority:
    """REQ-008 (agentcfg003): the checked path argument names are the registered
    tool's declared path-kind keys; the configured approval_resource_keys lists
    no longer contribute; every string element of a list-valued path argument is
    checked; a value that is neither str nor list[str] fails closed."""

    @staticmethod
    def _root_cfg(tmp_path) -> AgentConfig:
        return _cfg(allowed_root=str(tmp_path))

    def test_preflight_list_outside_element_denied(self, tmp_path) -> None:
        """AC-1: a declared list-valued path key with one element outside allowed_root."""
        cfg = self._root_cfg(tmp_path)
        reg = _stub_registry(read_multiple_files={"paths": "path"})
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(
                cfg,
                "read_multiple_files",
                {"paths": [str(tmp_path / "in.txt"), "/etc/shadow"]},
                reg,
            )
        assert exc_info.value.audit_decision == "denied_root_jail"

    def test_preflight_list_all_inside_passes(self, tmp_path) -> None:
        """AC-1 counterpart: a list with all elements inside allowed_root passes."""
        cfg = self._root_cfg(tmp_path)
        reg = _stub_registry(read_multiple_files={"paths": "path"})
        check_preflight(
            cfg,
            "read_multiple_files",
            {"paths": [str(tmp_path / "a.txt"), str(tmp_path / "b.txt")]},
            reg,
        )  # does not raise

    def test_preflight_declared_repo_path_denied(self, tmp_path) -> None:
        """AC-2 (policy half): a declared non-list path key under a different name."""
        cfg = self._root_cfg(tmp_path)
        reg = _stub_registry(git_status={"repo_path": "path"})
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "git_status", {"repo_path": "/etc"}, reg)
        assert exc_info.value.audit_decision == "denied_root_jail"

    def test_configured_path_keys_no_longer_apply(self, tmp_path) -> None:
        """REQ-008/REQ-011: a key named only in approval_resource_keys is not
        checked; the declared mapping is the sole key source."""
        cfg = _cfg(
            allowed_root=str(tmp_path),
            approval_resource_keys={"path_keys": ["paths"], "branch_keys": ["branch"]},
        )
        reg = _stub_registry(git_status={"repo_path": "repo"})
        check_preflight(
            cfg,
            "git_status",
            {"paths": ["/etc/out"], "branch": "main", "repo_path": str(tmp_path)},
            reg,
        )  # does not raise: no path-kind declared keys

    def test_preflight_unregistered_tool_denies(self, tmp_path) -> None:
        """AC-3 revised: no registry entry -> fail closed regardless of any
        configured key list; no KeyError escapes."""
        cfg = self._root_cfg(tmp_path)
        reg = _stub_registry()  # empty registry
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(
                cfg,
                "not_registered_tool",
                {"paths": [str(tmp_path / "in.txt"), "/etc/out"]},
                reg,
            )
        assert exc_info.value.audit_decision == "denied_root_jail"
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "not_registered_tool", {"foo": "bar"}, reg)
        assert exc_info.value.audit_decision == "denied_root_jail"

    def test_preflight_non_string_path_value_denied(self, tmp_path) -> None:
        """REQ-002 fail-closed: a not-inspectable value denies under a declared key."""
        cfg = self._root_cfg(tmp_path)
        reg = _stub_registry(write_file={"path": "path"})
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "write_file", {"path": 123}, reg)
        assert exc_info.value.audit_decision == "denied_root_jail"

    def test_preflight_list_non_string_element_denied(self, tmp_path) -> None:
        """REQ-002 fail-closed: a list containing a non-string element denies."""
        cfg = self._root_cfg(tmp_path)
        reg = _stub_registry(custom_list_tool={"paths": "path"})
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(
                cfg, "custom_list_tool", {"paths": [str(tmp_path / "in.txt"), 123]}, reg
            )
        assert exc_info.value.audit_decision == "denied_root_jail"

    def test_absent_and_empty_values_keep_skip_semantics(self, tmp_path) -> None:
        """Regression pin: key absent, empty string, and empty-string list elements
        keep today's skip semantics (no deny, no smuggled pass)."""
        cfg = self._root_cfg(tmp_path)
        reg = _stub_registry(write_file={"path": "path"})
        check_preflight(cfg, "write_file", {}, reg)  # does not raise
        check_preflight(cfg, "write_file", {"path": ""}, reg)  # does not raise
        check_preflight(
            cfg, "write_file", {"path": [str(tmp_path / "in.txt"), ""]}, reg
        )

    def test_registry_omitted_fails_closed(self, tmp_path) -> None:
        """REQ-008: calls without a registry no longer fall back to configured
        keys; the jail denies because the declared scope cannot be verified."""
        cfg = self._root_cfg(tmp_path)
        assert not check_allowed_root(
            cfg, "write_file", {"path": str(tmp_path / "in.txt")}
        )

    def test_classify_risk_list_element_protected_escalates(self) -> None:
        """REQ-001/REQ-002: a protected-path list element escalates via classify_risk."""
        cfg = _cfg(
            approval_resource_keys={"path_keys": [], "branch_keys": []},
            approval_protected_paths=["/etc/"],
        )
        reg = _write_registry(read_multiple_files={"paths": "path"})
        result = classify_risk(
            cfg, "read_multiple_files", {"paths": ["/tmp/in", "/etc/shadow"]}, reg
        )
        assert result == "high"

    def test_classify_risk_non_string_path_escalates(self) -> None:
        """REQ-002 fail-closed: classify_risk escalates a not-inspectable path value."""
        cfg = _cfg()
        reg = _write_registry(write_file={"path": "path"})
        assert classify_risk(cfg, "write_file", {"path": 123}, reg) == "high"


class TestAuditResourceScopeExtraction:
    """REQ-004/REQ-008/REQ-011 (agentcfg003): the audit resource_scope resolves from the
    declared `resource_scope_keys` mapping alone; list-valued path args are recorded as
    elements joined with ';'."""

    @staticmethod
    def _audit_ctx(
        cfg: AgentConfig, registry: RuntimeToolRegistry | None = None
    ) -> SimpleNamespace:
        """Minimal ctx stub exposing only what _extract_resource_scope reads."""
        return SimpleNamespace(
            cfg=SimpleNamespace(approval=cfg.approval),
            services_required=SimpleNamespace(runtime_tools=registry),
        )

    def test_list_value_recorded_as_joined_elements(self) -> None:
        """AC-1 (audit half): elements joined with ';', not the Python repr."""
        cfg = _cfg()
        reg = _stub_registry(write_multiple_files={"paths": "path"})
        ctx = self._audit_ctx(cfg, reg)
        scope = _extract_resource_scope(
            ctx, {"paths": ["/opt/llm/a", "/etc/shadow"]}, "write_multiple_files"
        )
        assert scope == {"paths": "/opt/llm/a;/etc/shadow"}

    def test_empty_elements_dropped_empty_list_absent(self) -> None:
        """Empty-string elements are dropped; an all-empty list is not recorded."""
        cfg = _cfg()
        reg = _stub_registry(write_multiple_files={"paths": "path"})
        ctx = self._audit_ctx(cfg, reg)
        assert _extract_resource_scope(
            ctx, {"paths": ["/a", ""]}, "write_multiple_files"
        ) == {"paths": "/a"}
        assert _extract_resource_scope(ctx, {"paths": []}, "write_multiple_files") == {}

    def test_declared_key_recorded_without_configured_key(self) -> None:
        """AC-2 (audit half): declared repo_path recorded under the declared key."""
        cfg = _cfg()
        reg = _stub_registry(git_status={"repo_path": "path"})
        ctx = self._audit_ctx(cfg, reg)
        scope = _extract_resource_scope(ctx, {"repo_path": "/srv/repo"}, "git_status")
        assert scope == {"repo_path": "/srv/repo"}

    def test_declared_list_key_joined(self) -> None:
        """Declared key union applies to list values as well."""
        cfg = _cfg()
        reg = _stub_registry(read_multiple_files={"paths": "path"})
        ctx = self._audit_ctx(cfg, reg)
        scope = _extract_resource_scope(
            ctx, {"paths": ["/a", "/b"]}, "read_multiple_files"
        )
        assert scope == {"paths": "/a;/b"}

    def test_unregistered_tool_yields_empty_scope(self) -> None:
        """REQ-011 (audit half): an unknown tool name yields an empty scope — the
        config-key fallback is removed, and no raise occurs."""
        cfg = _cfg()
        reg = _stub_registry(read_multiple_files={"paths": "path"})
        ctx = self._audit_ctx(cfg, reg)
        scope = _extract_resource_scope(
            ctx, {"path": "/x", "other": "/y"}, "no_such_tool"
        )
        assert scope == {}

    def test_absent_registry_yields_empty_scope(self) -> None:
        """REQ-011: with no runtime registry there is no source, so the scope is empty."""
        cfg = _cfg()
        ctx = self._audit_ctx(cfg, None)
        assert _extract_resource_scope(ctx, {"path": "/opt/llm/x"}, "write_file") == {}

    def test_scalar_and_branch_values_unchanged(self) -> None:
        """AC-4 pin: scalar path values and branch keys keep today's str(v) form."""
        cfg = _cfg()
        reg = _stub_registry(write_file={"path": "path", "branch": "branch"})
        ctx = self._audit_ctx(cfg, reg)
        scope = _extract_resource_scope(
            ctx, {"path": "/opt/llm/x", "branch": "main"}, "write_file"
        )
        assert scope == {"path": "/opt/llm/x", "branch": "main"}


class TestClassifyRiskBranchProvenance:
    """AC-003 characterization: each test names the classify_risk() branch
    (declared tier, escalation, NONE short-circuit) that produced the asserted
    level (agentcfg003 REQ-004/REQ-007; the rule and constants priorities are
    removed)."""

    def test_declared_tier_beats_cfg_side_leftovers(self) -> None:
        # Declared-tier branch: a leftover approval_risk_rules entry and a cfg
        # tier map cannot compete — the registry declaration decides.
        cfg = _cfg(
            approval_risk_rules={"write_file": "medium"},
            tool_safety_tiers={"write_file": "WRITE_SAFE"},
        )
        reg = RuntimeToolRegistry(
            tools={
                "write_file": _runtime_tool(
                    "write_file",
                    tier="ADMIN",
                    is_write=True,
                    side_effect_class="local_write",
                )
            },
            allowed_servers=frozenset({"test_server"}),
        )
        assert classify_risk(cfg, "write_file", {}, reg) == "high"

    def test_tier_provenance_medium(self) -> None:
        # Declared-tier branch: the WRITE_DANGEROUS tier produces medium.
        cfg = _cfg()
        reg = _write_registry(write_file={})
        assert classify_risk(cfg, "write_file", {}, reg) == "medium"

    def test_escalation_provenance_for_declared_path_tool(self) -> None:
        # Escalation branch: a medium-tier path-bearing tool with a protected
        # path is raised to high by _escalate_for_path().
        cfg = _cfg(approval_protected_paths=["/opt/llm/"])
        reg = _write_registry(write_file={"path": "path"})
        assert (
            classify_risk(cfg, "write_file", {"path": "/opt/llm/config"}, reg) == "high"
        )

    def test_tier_none_short_circuits_escalation(self) -> None:
        # NONE short-circuit branch: a NONE-tier tool returns before escalation
        # even with a protected path; provenance evidence is that
        # _escalate_for_path() is never called.
        cfg = _cfg(approval_protected_paths=["/opt/llm/"])
        reg = _stub_registry(write_file={"path": "path"})  # READ_ONLY -> NONE
        with patch("agent.tool_policy._escalate_for_path") as escalate:
            assert (
                classify_risk(cfg, "write_file", {"path": "/opt/llm/config"}, reg)
                == "none"
            )
            escalate.assert_not_called()


class TestTierNoneGapProvenance:
    """REQ-001 measured gap: shipped tier-NONE tools (WRITE_SAFE/READ_ONLY map
    to NONE) return none even with a protected path argument (Plan row 11); the
    tiers here come from the registry declaration, not the cfg map."""

    SHIPPED_NONE_TIER_TOOLS = ["git_add", "git_commit", "index_paths", "refresh_index"]

    @staticmethod
    def _tier_reg(*tools: str) -> RuntimeToolRegistry:
        tier_by_tool = {t: PRODUCER_TIERS[t] for t in tools}
        return RuntimeToolRegistry(
            tools={
                t: _runtime_tool(
                    t,
                    {"path": "path"},
                    tier=tier,
                    is_write=tier != "READ_ONLY",
                    side_effect_class="read_only"
                    if tier == "READ_ONLY"
                    else "local_write",
                )
                for t, tier in tier_by_tool.items()
            },
            allowed_servers=frozenset({"test_server"}),
        )

    @pytest.mark.parametrize("tool", SHIPPED_NONE_TIER_TOOLS)
    def test_write_safe_tool_returns_none_on_protected_path(self, tool: str) -> None:
        cfg = _cfg(approval_protected_paths=["/opt/llm/"])
        reg = self._tier_reg(tool)
        with patch("agent.tool_policy._escalate_for_path") as escalate:
            assert classify_risk(cfg, tool, {"path": "/opt/llm/data/x"}, reg) == "none"
            escalate.assert_not_called()

    def test_read_only_tool_returns_none_on_protected_path(self) -> None:
        cfg = _cfg(approval_protected_paths=["/opt/llm/"])
        reg = self._tier_reg("git_status")
        assert (
            classify_risk(cfg, "git_status", {"path": "/opt/llm/data/x"}, reg) == "none"
        )


class TestPlanModeProvenance:
    """is_plan_mode_blocked(): the declared agent_safety_tier is the authority
    and plan_blocked_tools extends it (DT-03 Option A posture, REQ-006)."""

    @staticmethod
    def _reg_with(**tier_by_tool: str) -> RuntimeToolRegistry:
        return RuntimeToolRegistry(
            tools={
                name: _runtime_tool(name, tier=tier)
                for name, tier in tier_by_tool.items()
            },
            allowed_servers=frozenset({"test_server"}),
        )

    def test_tier_rule_is_the_authority(self) -> None:
        cfg = _cfg(plan_blocked_tools=[])
        reg = self._reg_with(read_text_file="READ_ONLY", write_file="WRITE_DANGEROUS")
        assert is_plan_mode_blocked(cfg, "read_text_file", reg) is False
        assert is_plan_mode_blocked(cfg, "write_file", reg) is True
        # unknown tool name: no declared tier and the check fails closed
        assert is_plan_mode_blocked(cfg, "mystery_tool", reg) is True
        # T-06: no registry at all also fails closed
        assert is_plan_mode_blocked(cfg, "read_text_file") is True

    def test_plan_blocked_tools_extends_tier_rule(self) -> None:
        # a tier-READ_ONLY tool is still blocked when named explicitly,
        # proving the list is an extension of the tier rule, not its source
        cfg = _cfg(plan_blocked_tools=["git_status"])
        reg = self._reg_with(git_status="READ_ONLY")
        assert is_plan_mode_blocked(cfg, "git_status", reg) is True
