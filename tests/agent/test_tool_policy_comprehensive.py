"""tests/test_tool_policy_comprehensive.py
Comprehensive unit tests for agent/tool_policy.py: risk classification and pre-flight checks.

agentcfg003: tier, risk, and resource-key decisions read the registered tool's
declared metadata through the RuntimeToolRegistry; the removed per-tool config
maps (tool_safety_tiers, approval_risk_rules, approval_resource_keys) no longer
exist, and the static reference sets only report drift.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_enums import RiskLevel
from agent.tool_exceptions import PolicyViolationError
from agent.tool_policy import (
    _STATIC_SIDE_EFFECT_TOOLS,
    _TIER_TO_RISK,
    _escalate_for_github_branch,
    _escalate_for_path,
    _special_case_risk,
    check_allowed_root,
    check_preflight,
    check_write_classification,
    classify_operation_type,
    classify_risk,
)
from shared.runtime_tool_registry import RuntimeToolRegistry

from tests.agent._config_test_defaults import SHIPPED_DB_PATH_KEYS
from tests.agent._producer_registry import make_producer_registry
from tests.agent.test_tool_policy import _runtime_tool, _stub_registry, _write_registry

# Producer-declared tools whose shipped tier maps to RiskLevel.NONE — the
# population the NONE short-circuit in classify_risk() protects (Plan row 12
# lineage; the removed approval_risk_rules map is gone, the declarations are
# the source).
_TIER_NONE_DECLARED_TOOLS = sorted(
    tool.name
    for tool in make_producer_registry().all_tools()
    if _TIER_TO_RISK.get(tool.agent_safety_tier) is RiskLevel.NONE
)


def _cfg(**overrides: Any) -> AgentConfig:
    """Build an AgentConfig for tool_policy.py unit tests.

    This intentionally bypasses ProductionConfigValidator (patched below):
    these tests construct deliberately empty/narrow allowed_tools and approval
    settings to exercise tool_policy.py's own fallback logic, which is a
    different concern from whether the resulting config would be accepted as
    production-ready.
    """
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "llm_retry_base_delay": 1.0,
        "serial_tool_calls": False,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": ["shell_execute"],
        "tool_definitions": [],
        "approval_protected_paths": [],
        "approval_github_allowed_repos": [],
        "approval_high_risk_branches": [],
        "approval_shell_safe_prefixes": [],
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


class TestEscalateForPath:
    """REQ-008: the checked keys are the registered tool's declared path-kind
    keys; an unknown declared scope (no registry, unregistered tool) escalates
    fail closed."""

    def test_already_high_base_risk_no_escalation(self) -> None:
        cfg = _cfg()
        assert _escalate_for_path(cfg, "write_file", "high", {}) is None

    def test_no_matching_path_key_returns_none(self) -> None:
        cfg = _cfg()
        reg = _stub_registry(write_file={"path": "path"})
        assert (
            _escalate_for_path(
                cfg, "write_file", "medium", {"other": "/opt/llm/x"}, reg
            )
            is None
        )

    def test_unregistered_tool_fails_closed_to_high(self) -> None:
        cfg = _cfg()
        assert (
            _escalate_for_path(cfg, "write_file", "medium", {"path": "/opt/llm/x"})
            == "high"
        )

    def test_protected_path_escalates_to_high(self) -> None:
        cfg = _cfg(approval_protected_paths=["/opt/llm/"])
        reg = _stub_registry(write_file={"path": "path"})
        assert (
            _escalate_for_path(
                cfg, "write_file", "medium", {"path": "/opt/llm/config"}, reg
            )
            == "high"
        )

    def test_non_protected_path_no_escalation(self) -> None:
        cfg = _cfg(approval_protected_paths=["/opt/llm/"])
        reg = _stub_registry(write_file={"path": "path"})
        assert (
            _escalate_for_path(
                cfg, "write_file", "medium", {"path": "/home/user/file.txt"}, reg
            )
            is None
        )

    def test_multiple_protected_paths(self) -> None:
        cfg = _cfg(approval_protected_paths=["/opt/llm/", "/etc/"])
        reg = _stub_registry(write_file={"path": "path"})
        assert (
            _escalate_for_path(
                cfg, "write_file", "medium", {"path": "/etc/passwd"}, reg
            )
            == "high"
        )


class TestEscalateForGithubBranch:
    """REQ-008: only declared branch-kind keys are checked; a tool declaring no
    branch key is never branch-escalated."""

    def test_tool_with_no_declared_branch_key_returns_none(self) -> None:
        cfg = _cfg(approval_high_risk_branches=["main", "production"])
        reg = _stub_registry(write_file={"path": "path"})
        assert (
            _escalate_for_github_branch(
                cfg, "write_file", "medium", {"branch": "main"}, reg
            )
            is None
        )

    def test_already_high_base_risk_no_escalation(self) -> None:
        cfg = _cfg()
        assert _escalate_for_github_branch(cfg, "github_push_files", "high", {}) is None

    def test_high_risk_branch_escalates(self) -> None:
        cfg = _cfg(approval_high_risk_branches=["main", "production"])
        reg = _stub_registry(github_push_files={"branch": "branch"})
        assert (
            _escalate_for_github_branch(
                cfg, "github_push_files", "medium", {"branch": "main"}, reg
            )
            == "high"
        )

    def test_non_risk_branch_no_escalation(self) -> None:
        cfg = _cfg(approval_high_risk_branches=["main"])
        reg = _stub_registry(github_push_files={"branch": "branch"})
        assert (
            _escalate_for_github_branch(
                cfg, "github_push_files", "medium", {"branch": "feature"}, reg
            )
            is None
        )

    def test_unregistered_tool_no_branch_decision(self) -> None:
        """classify_risk() resolves an unregistered tool to HIGH before this point;
        the escalation itself reports no branch decision (None)."""
        cfg = _cfg(approval_high_risk_branches=["main"])
        assert (
            _escalate_for_github_branch(
                cfg, "github_push_files", "medium", {"branch": "main"}
            )
            is None
        )


class TestSpecialCaseRisk:
    def test_recursive_delete_returns_high(self) -> None:
        cfg = _cfg()
        assert (
            _special_case_risk(cfg, "delete_directory", {"recursive": True}) == "high"
        )

    def test_non_recursive_delete_returns_none(self) -> None:
        cfg = _cfg()
        assert _special_case_risk(cfg, "delete_directory", {"recursive": False}) is None

    def test_force_flag_returns_high(self) -> None:
        cfg = _cfg()
        assert _special_case_risk(cfg, "write_file", {"force": True}) == "high"

    def test_overwrite_flag_returns_high(self) -> None:
        cfg = _cfg()
        assert _special_case_risk(cfg, "write_file", {"overwrite": True}) == "high"

    def test_clobber_flag_returns_high(self) -> None:
        cfg = _cfg()
        assert _special_case_risk(cfg, "write_file", {"clobber": True}) == "high"

    def test_shell_run_safe_prefix_returns_none(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls", "pwd"])
        assert _special_case_risk(cfg, "shell_run", {"command": "ls -la"}) == "none"

    def test_shell_run_unsafe_command_returns_high(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls", "pwd"])
        assert _special_case_risk(cfg, "shell_run", {"command": "rm -rf /"}) == "high"

    def test_no_special_cases_returns_none(self) -> None:
        cfg = _cfg()
        assert _special_case_risk(cfg, "read_text_file", {}) is None


class TestClassifyOperationType:
    """REQ-007 authority inversion: the registered tool's declared
    side_effect_class decides; the reference sets only sub-classify side effects
    and report disagreement via check_write_classification()."""

    @staticmethod
    def _registry_with(
        *names: str, side_effect_class: str = "read_only"
    ) -> RuntimeToolRegistry:
        is_write = side_effect_class != "read_only"
        tier = "WRITE_DANGEROUS" if is_write else "READ_ONLY"
        return RuntimeToolRegistry(
            tools={
                name: _runtime_tool(
                    name,
                    {},
                    is_write=is_write,
                    tier=tier,
                    side_effect_class=side_effect_class,
                )
                for name in names
            },
            allowed_servers=frozenset({"test_server"}),
        )

    def test_declared_read_only_resolves_to_read(self) -> None:
        reg = self._registry_with("new_read_tool")
        assert classify_operation_type("new_read_tool", reg) == "read"

    def test_declared_write_tool_outside_reference_sets_is_write(self) -> None:
        """ADR-003 INV-03: a declared side effect is never classified as READ,
        even when no reference set names the tool."""
        reg = self._registry_with("new_write_tool", side_effect_class="local_write")
        assert classify_operation_type("new_write_tool", reg) == "write"

    def test_declaration_decides_when_reference_data_disagrees(self) -> None:
        """A disagreement changes no decision here (REQ-007): write_file is a
        reference WRITE tool, yet its declared read_only class resolves to READ,
        and check_write_classification() reports the mismatch as a finding."""
        mismatched = self._registry_with("write_file")
        assert classify_operation_type("write_file", mismatched) == "read"
        assert any("write_file" in m for m in check_write_classification(mismatched))
        extra = self._registry_with("new_write_tool", side_effect_class="local_write")
        assert any("new_write_tool" in m for m in check_write_classification(extra))

    def test_write_classification_clean_when_declaration_matches_reference(
        self,
    ) -> None:
        reg = self._registry_with("write_file", side_effect_class="local_write")
        assert check_write_classification(reg) == []

    def test_no_registry_or_unregistered_fails_closed(self) -> None:
        """ADR-003 Decision #6: no static-set fallback — no declaration means UNKNOWN."""
        assert classify_operation_type("write_file") == "unknown"
        assert (
            classify_operation_type("write_file", self._registry_with("other"))
            == "unknown"
        )

    def test_static_side_effect_membership_is_canonical(self) -> None:
        """sideeffect001 REQ-004: the reference set delegates to the canonical set;
        it is drift-detection input only, never a classification fallback."""
        from shared.tool_constants import ALL_SIDE_EFFECTING_TOOLS

        assert _STATIC_SIDE_EFFECT_TOOLS == ALL_SIDE_EFFECTING_TOOLS
        for name in ("index_paths", "refresh_index"):
            assert name in _STATIC_SIDE_EFFECT_TOOLS
            assert classify_operation_type(name, None) == "unknown"

    def test_producer_declarations_classify_every_write_family(self) -> None:
        """The shipped declarations resolve each reference family to its operation
        type through the live registry."""
        reg = make_producer_registry()
        for name in (
            "write_file",
            "edit_file",
            "create_directory",
            "move_file",
            "index_paths",
            "refresh_index",
            "rag_delete_document",
            "trigger_workflow",
            "git_add",
            "git_commit",
            "git_checkout",
            "git_pull",
            "git_push",
        ):
            assert classify_operation_type(name, reg) == "write", name
        for name in ("delete_file", "delete_directory"):
            assert classify_operation_type(name, reg) == "delete", name
        assert classify_operation_type("shell_run", reg) == "execute"
        for name in (
            "github_push_files",
            "github_create_pull_request",
            "github_merge_pull_request",
        ):
            assert classify_operation_type(name, reg) == "api_write", name
        for name in ("list_directory", "read_text_file", "search_web"):
            assert classify_operation_type(name, reg) == "read", name

    def test_git_checkout_pull_push_risk_is_declared_tier(self) -> None:
        """agentcfg003 REQ-004/REQ-011: the removed approval_risk_rules override no
        longer raises these tools above their declaration — the shipped
        WRITE_DANGEROUS tier maps to medium, which satisfies the production risk
        floor (ProductionConfigValidator._check_approval_risk_floor)."""
        cfg = _cfg()
        reg = make_producer_registry()
        for name in ("git_checkout", "git_pull", "git_push"):
            assert (
                classify_risk(cfg, name, {"repo_path": "/tmp/repo"}, reg) == "medium"
            ), name

    def test_real_config_without_runtime_registry_fails_closed_to_high(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """With no runtime registry there is no declaration to consult:
        classify_risk() resolves every git tool to HIGH (fail-safe), exactly what
        the validator floor relies on before discovery runs."""
        from agent.config_builders import build_agent_config

        # config/agent.toml's [mcp.mcp_servers.git] resolves auth_token from
        # MCP_GIT_AUTH_TOKEN, which tests/conftest.py deliberately defaults to
        # "" for the standalone git MCP server config (many tests rely on that
        # empty-token accept-all behavior) — but McpServerConfig itself
        # requires a non-empty auth_token, so override it locally here rather
        # than changing the shared conftest default.
        monkeypatch.setenv("MCP_GIT_AUTH_TOKEN", "test-token")
        monkeypatch.setenv("MCP_CICD_AUTH_TOKEN", "test-token")
        monkeypatch.setenv("MCP_WEB_SEARCH_AUTH_TOKEN", "test-token")
        cfg = build_agent_config()
        for name in ("git_checkout", "git_pull", "git_push"):
            assert classify_risk(cfg, name, {"repo_path": "/tmp/repo"}) == "high"


class TestCheckAllowedRootEdgeCases:
    """REQ-008: the jail checks the declared path-kind keys; an unknown declared
    scope (no registry, unregistered tool) denies."""

    def test_unregistered_tool_denies(self) -> None:
        cfg = _cfg(allowed_root="/home")
        assert not check_allowed_root(cfg, "write_file", {"path": "/home/x"})

    def test_invalid_path_returns_false(self) -> None:
        cfg = _cfg(allowed_root="/home")
        reg = _stub_registry(write_file={"path": "path"})
        assert not check_allowed_root(cfg, "write_file", {"path": "\0invalid"}, reg)

    def test_absolute_path_outside_root(self) -> None:
        cfg = _cfg(allowed_root="/home/user")
        reg = _stub_registry(write_file={"path": "path"})
        assert not check_allowed_root(cfg, "write_file", {"path": "/etc/passwd"}, reg)

    def test_relative_path_resolved_correctly(self) -> None:
        cfg = _cfg(allowed_root="/home/user")
        reg = _stub_registry(write_file={"path": "path"})
        # This should resolve to a path outside the root
        assert not check_allowed_root(
            cfg, "write_file", {"path": "../../etc/passwd"}, reg
        )


class TestCheckPreflightEdgeCases:
    def test_empty_allowed_tools_list(self) -> None:
        """REQ-002: an empty allowed_tools denies every tool."""
        cfg = _cfg(allowed_tools=[])
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "any_tool", {})
        assert exc_info.value.audit_decision == "denied_allowed_tools"

    def test_none_values_in_args(self) -> None:
        cfg = _cfg(allowed_root="/tmp", allowed_tools=["write_file"])
        reg = _stub_registry(write_file={"path": "path"})
        # None values are skipped by the declared-key path iteration: no denial.
        check_preflight(cfg, "write_file", {"path": None}, reg)  # does not raise

    def test_path_with_special_characters(self) -> None:
        cfg = _cfg(allowed_root="/tmp")
        reg = _stub_registry(write_file={"path": "path"})
        # Test with path containing special characters - should allow valid paths
        assert check_allowed_root(cfg, "write_file", {"path": "/tmp/valid_file"}, reg)

    def test_empty_repo_in_allowlist(self) -> None:
        cfg = _cfg(
            allowed_tools=["github_push_files"], approval_github_allowed_repos=[]
        )
        with pytest.raises(PolicyViolationError):  # Should deny due to empty allowlist
            check_preflight(cfg, "github_push_files", {"owner": "org", "repo": "repo"})

    def test_missing_required_keys(self) -> None:
        cfg = _cfg(allowed_root="/tmp")
        reg = _stub_registry(write_file={"path": "path"})
        # Test missing path key
        assert check_allowed_root(cfg, "write_file", {"other": "/tmp/file"}, reg)

    @staticmethod
    def _reg_with(*names: str) -> RuntimeToolRegistry:
        return RuntimeToolRegistry(
            tools={name: _runtime_tool(name) for name in names},
            allowed_servers=frozenset({"test_server"}),
        )

    def test_discovered_mode_allows_registered_tool(self) -> None:
        cfg = _cfg(tool_policy_mode="discovered", allowed_tools=[])
        reg = self._reg_with("any_tool")
        check_preflight(cfg, "any_tool", {}, reg)  # does not raise

    def test_discovered_mode_denies_unregistered_tool(self) -> None:
        cfg = _cfg(tool_policy_mode="discovered", allowed_tools=[])
        reg = self._reg_with("write_file")
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "any_tool", {}, reg)
        assert exc_info.value.audit_decision == "denied_discovered"

    def test_discovered_mode_denies_disabled_tool(self) -> None:
        cfg = _cfg(
            tool_policy_mode="discovered",
            allowed_tools=[],
            disabled_tools=["write_file"],
        )
        reg = self._reg_with("write_file")
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "write_file", {}, reg)
        assert exc_info.value.audit_decision == "denied_discovered"


class TestClassifyRiskEdgeCases:
    def test_mixed_tier_classification(self) -> None:
        reg = RuntimeToolRegistry(
            tools={
                "read_text_file": _runtime_tool("read_text_file"),
                "write_file": _runtime_tool(
                    "write_file",
                    {"path": "path"},
                    is_write=True,
                    tier="WRITE_SAFE",
                    side_effect_class="local_write",
                ),
                "delete_file": _runtime_tool(
                    "delete_file",
                    {"path": "path"},
                    is_write=True,
                    tier="WRITE_DANGEROUS",
                    side_effect_class="local_write",
                ),
            },
            allowed_servers=frozenset({"test_server"}),
        )

        assert (
            classify_risk(cfg := _cfg(), "read_text_file", {}, reg) == "none"
        )  # READ_ONLY -> none
        assert classify_risk(cfg, "write_file", {}, reg) == "none"  # WRITE_SAFE -> none
        assert (
            classify_risk(cfg, "delete_file", {}, reg) == "medium"
        )  # WRITE_DANGEROUS -> medium

        # shell_run is unregistered here: no declaration to consult, so the
        # fail-safe base is HIGH (the missing command arg also special-cases HIGH).
        result = classify_risk(cfg, "shell_run", {})
        assert result == "high"

    def test_complex_nested_args(self) -> None:
        cfg = _cfg(approval_protected_paths=["/opt/llm/"])
        reg = _write_registry(delete_file={"path": "path"})

        # Complex args with nested structures. delete_file declares WRITE_DANGEROUS
        # (tier-MEDIUM base); the protected path escalates it to HIGH.
        result = classify_risk(
            cfg,
            "delete_file",
            {
                "path": "/opt/llm/config.json",
                "metadata": {"author": "test", "version": 1},
                "options": ["--debug", "--verbose"],
            },
            reg,
        )
        assert result == "high"  # Escalated due to protected path


class TestSpecialCaseRiskReq001Req002Req003Req004:
    """REQ-001 through REQ-004: safe-prefix parsing, metacharacter rejection,
    positional routing, and unsafe-flag denial."""

    # --- REQ-001: parsed identity match replaces startswith ---

    def test_single_word_prefix_matches_basename(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        assert _special_case_risk(cfg, "shell_run", {"command": "ls -la"}) == "none"

    def test_full_path_basename_matching(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        assert (
            _special_case_risk(cfg, "shell_run", {"command": "/bin/ls -la"}) == "none"
        )

    def test_prefix_collision_cat_vs_category_dump_secrets(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["category_dump_secrets"])
        result = _special_case_risk(cfg, "shell_run", {"command": "cat /etc/passwd"})
        assert result == "high"

    def test_multi_word_prefix_does_not_match_shorter_command(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["git log"])
        result = _special_case_risk(cfg, "shell_run", {"command": "git log --oneline"})
        assert result == "none"

    def test_multi_word_prefix_mismatch_git_log_vs_git_pull(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["git log"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "git pull origin main"}
        )
        assert result == "high"

    def test_multi_word_prefix_exact_token_match(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["git log"])
        result = _special_case_risk(cfg, "shell_run", {"command": "git log"})
        assert result == "none"

    def test_empty_prefix_list_returns_high(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=[])
        result = _special_case_risk(cfg, "shell_run", {"command": "ls -la"})
        assert result == "high"

    def test_non_string_command_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": 123})
        assert result == "high"

    def test_none_command_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": None})
        assert result == "high"

    def test_unbalanced_quotes_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": 'ls "unbalanced'})
        assert result == "high"

    def test_empty_command_after_split_fails_closed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": ""})
        assert result == "high"

    # --- REQ-002: metacharacter fail-closed ---

    def test_semicolon_metacharacter_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": "ls; rm -rf /"})
        assert result == "high"

    def test_ampersand_metacharacter_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "ls & cat /etc/passwd"}
        )
        assert result == "high"

    def test_pipe_metacharacter_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": "ls | grep foo"})
        assert result == "high"

    def test_double_ampersand_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "ls && cat /etc/passwd"}
        )
        assert result == "high"

    def test_double_pipe_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "ls || cat /etc/passwd"}
        )
        assert result == "high"

    def test_backtick_metacharacter_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": "ls `whoami`"})
        assert result == "high"

    def test_subshell_metacharacter_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "ls $(cat /etc/passwd)"}
        )
        assert result == "high"

    def test_process_substitution_less_than_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "ls <(cat /etc/passwd)"}
        )
        assert result == "high"

    def test_process_substitution_greater_than_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "ls >(cat /etc/passwd)"}
        )
        assert result == "high"

    def test_redirection_greater_than_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": "ls > /tmp/out"})
        assert result == "high"

    def test_redirection_less_than_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": "ls < /etc/passwd"})
        assert result == "high"

    def test_double_redirection_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": "ls >> /tmp/out"})
        assert result == "high"

    def test_heredoc_operator_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": "ls << EOF"})
        assert result == "high"

    def test_newline_metacharacter_rejected(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": "ls\nrm -rf /"})
        assert result == "high"

    # --- REQ-003: positional arg routing ---

    def test_positional_arg_protected_path_escalates(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            approval_protected_paths=["/etc/shadow"],
        )
        result = _special_case_risk(cfg, "shell_run", {"command": "cat /etc/shadow"})
        assert result == "high"

    def test_positional_arg_outside_allowed_root_escalates(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/tmp",
        )
        result = _special_case_risk(cfg, "shell_run", {"command": "cat /etc/passwd"})
        assert result == "high"

    def test_positional_arg_inside_allowed_root_passes(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/tmp",
        )
        result = _special_case_risk(cfg, "shell_run", {"command": "cat /tmp/file.txt"})
        assert result == "none"

    def test_flag_only_no_positional_routing_needed(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["ls"])
        result = _special_case_risk(cfg, "shell_run", {"command": "ls -la"})
        assert result == "none"

    def test_positional_arg_value_error_in_resolve_escalates(self) -> None:
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/tmp",
        )
        # Null byte in path should trigger ValueError during Path.resolve()
        result = _special_case_risk(cfg, "shell_run", {"command": "cat \x00invalid"})
        assert result == "high"

    # --- REQ-004: unsafe flag denylist ---

    def test_find_exec_flag_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "find . -exec rm {} \\;"}
        )
        assert result == "high"

    def test_find_delete_flag_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = _special_case_risk(cfg, "shell_run", {"command": "find . -delete"})
        assert result == "high"

    def test_find_ok_flag_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "find . -ok rm {} \\;"}
        )
        assert result == "high"

    def test_grep_recursive_flag_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["grep"])
        result = _special_case_risk(cfg, "shell_run", {"command": "grep -r pattern ."})
        assert result == "high"

    def test_grep_recursive_uppercase_flag_denied(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["grep"])
        result = _special_case_risk(cfg, "shell_run", {"command": "grep -R pattern ."})
        assert result == "high"

    def test_find_without_unsafe_flags_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["find"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "find . -name '*.txt'"}
        )
        assert result == "none"

    def test_grep_without_unsafe_flags_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["grep"])
        result = _special_case_risk(
            cfg, "shell_run", {"command": "grep pattern file.txt"}
        )
        assert result == "none"

    def test_cat_without_unsafe_flags_passes(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["cat"])
        result = _special_case_risk(cfg, "shell_run", {"command": "cat file.txt"})
        assert result == "none"


class TestMetacharacterRejectionComprehensive:
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


class TestPathArgumentConstraintsComprehensive:
    def test_cat_protected_path_escalates(self) -> None:
        """REQ-003: cat on a protected path must escalate to HIGH."""
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            approval_protected_paths=["/etc/"],
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /etc/shadow"})
        assert result == "high"

    def test_cat_within_allowed_root_passes(self) -> None:
        """REQ-003: cat within allowed_root must pass path checks."""
        cfg = _cfg(
            approval_shell_safe_prefixes=["cat"],
            allowed_root="/home/user",
        )
        result = classify_risk(cfg, "shell_run", {"command": "cat /home/user/file.txt"})
        assert result == "none"


class TestClassifyRiskConfigPosture:
    """REQ-004/REQ-007 properties over the producer-declared tier data
    (make_producer_registry mirrors every shipped TOOL_LIST declaration): a
    future declaration change surfaces as a test failure, not silent policy
    drift (Plan row 12 lineage)."""

    @staticmethod
    def _shipped_cfg() -> AgentConfig:
        return _cfg(approval_protected_paths=["/opt/", "/etc/"])

    def test_declared_tier_maps_to_expected_risk_for_every_producer_tool(self) -> None:
        """Provenance: with no per-tool config maps left, every shipped tool
        resolves to exactly _TIER_TO_RISK[declared tier] when consulted through
        the live registry (no extra args)."""
        cfg = self._shipped_cfg()
        reg = make_producer_registry()
        for tool in sorted(reg.all_tools(), key=lambda t: t.name):
            expected = _TIER_TO_RISK[tool.agent_safety_tier]
            assert classify_risk(cfg, tool.name, {}, reg) is expected, tool.name

    def test_declared_none_tier_superset_matches_expected_tool_sets(self) -> None:
        """Provenance: the tier-NONE population is exactly the tools the shipped
        tiers declare READ_ONLY or WRITE_SAFE — the declaration is the only source."""
        reg = make_producer_registry()
        expected = sorted(
            tool.name
            for tool in reg.all_tools()
            if tool.agent_safety_tier in ("READ_ONLY", "WRITE_SAFE")
        )
        assert _TIER_NONE_DECLARED_TOOLS == expected

    @pytest.mark.parametrize("tool", _TIER_NONE_DECLARED_TOOLS)
    def test_tier_none_declared_tool_never_escalates(self, tool: str) -> None:
        """Provenance: the NONE short-circuit returns before _special_case_risk()
        and _escalate_for_path() — a tier-NONE tool stays none even with a
        protected-path argument."""
        cfg = self._shipped_cfg()
        reg = make_producer_registry()
        with (
            patch("agent.tool_policy._special_case_risk") as special,
            patch("agent.tool_policy._escalate_for_path") as escalate,
        ):
            assert classify_risk(cfg, tool, {"path": "/opt/local/data"}, reg) == "none"
            special.assert_not_called()
            escalate.assert_not_called()
