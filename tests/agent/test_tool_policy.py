"""
tests/test_tool_policy.py
Unit tests for tool_policy.py: risk classification, path/repo checks, pre-flight deny.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_enums import OperationType
from agent.tool_exceptions import PolicyViolationError
from agent.tool_policy import (
    check_allowed_repo,
    check_allowed_root,
    check_preflight,
    classify_operation_type,
    classify_risk,
)
from shared.runtime_tool_registry import RuntimeTool, RuntimeToolRegistry


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
        "llm_max_retries": 3,
        "llm_retry_base_delay": 1.0,
        "serial_tool_calls": False,
        "tool_result_max_llm_chars": 4000,
        "masked_fields": [],
        "allowed_tools": [],
        "tool_definitions": [],
        "tool_safety_tiers": {},
        "approval_risk_rules": {},
        "approval_protected_paths": [],
        "approval_github_allowed_repos": [],
        "approval_high_risk_branches": [],
        "approval_shell_safe_prefixes": [],
        "approval_resource_keys": {"path_keys": [], "branch_keys": []},
        "allowed_root": "",
        # memory_embed_enabled now defaults to True; embed_url must be non-empty
        # to satisfy AgentConfig.__post_init__'s cross-field validation.
        "embed_url": "http://127.0.0.1:9999",
        "mcp_servers": {
            "_dummy": {
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


class TestClassifyOperationType:
    def test_github_mutation_tools_classified_as_api_write(self) -> None:
        from shared.tool_constants import (
            GITHUB_DANGEROUS_TOOLS,
            GITHUB_WRITE_TOOLS,
        )

        mutation_set = GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
        for tool_name in mutation_set:
            assert classify_operation_type(tool_name) == OperationType.API_WRITE


class TestClassifyRisk:
    @staticmethod
    def _registry_with(*tools: str) -> RuntimeToolRegistry:
        tool_map: dict[str, RuntimeTool] = {}
        for t in tools:
            tool_map[t] = RuntimeTool(
                name=t,
                server_key="test_server",
                server_url="",
                description="",
                input_schema={},
                raw_definition={},
                status="active",
                is_write=False,
                requires_serial=False,
                resource_scope_kind="",
                resource_scope_keys=(),
                agent_safety_tier="READ_ONLY",
                enabled_for_llm=True,
                capabilities=(),
            )
        return RuntimeToolRegistry(tools=tool_map)

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

    def test_non_recursive_delete_defaults_to_high_from_constants(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "delete_directory", {"recursive": False})
        assert result == "high"

    def test_base_tier_tool_with_no_path_match_returns_medium(self) -> None:
        cfg = _cfg()
        reg = self._registry_with("read_text_file")
        result = classify_risk(cfg, "read_text_file", {"path": "/tmp/f"}, reg)
        assert result == "medium"

    def test_read_only_tier_returns_none(self) -> None:
        cfg = _cfg(tool_safety_tiers={"read_text_file": "READ_ONLY"})
        result = classify_risk(cfg, "read_text_file", {"path": "/tmp/f"})
        assert result == "none"

    def test_protected_path_escalates_to_high(self) -> None:
        cfg = _cfg(
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
            approval_protected_paths=["/opt/llm/"],
        )
        result = classify_risk(cfg, "write_file", {"path": "/opt/llm/config"})
        assert result == "high"

    def test_non_protected_path_no_escalation(self) -> None:
        cfg = _cfg(
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
            approval_protected_paths=["/opt/llm/"],
        )
        result = classify_risk(cfg, "write_file", {"path": "/home/user/file.txt"})
        assert result == "medium"

    def test_explicit_risk_rule_takes_precedence(self) -> None:
        cfg = _cfg(approval_risk_rules={"write_file": "none"})
        result = classify_risk(cfg, "write_file", {})
        assert result == "none"

    def test_force_flag_does_not_override_none_risk_rule(self) -> None:
        cfg = _cfg(approval_risk_rules={"write_file": "none"})
        result = classify_risk(cfg, "write_file", {"force": True})
        assert result == "none"


class TestCheckAllowedRoot:
    def test_allows_path_within_root(self) -> None:
        cfg = _cfg(
            allowed_root="/home",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        assert check_allowed_root(cfg, "write_file", {"path": "/home/user/doc.md"})

    def test_denies_path_outside_root(self) -> None:
        cfg = _cfg(
            allowed_root="/home",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        assert not check_allowed_root(cfg, "write_file", {"path": "/tmp/foo"})

    def test_empty_root_allows_all(self) -> None:
        cfg = _cfg(
            allowed_root="",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        assert check_allowed_root(cfg, "write_file", {"path": "/any/path"})

    def test_no_matching_keys_allows(self) -> None:
        cfg = _cfg(
            allowed_root="/home",
            approval_resource_keys={"path_keys": [], "branch_keys": []},
        )
        assert check_allowed_root(cfg, "write_file", {})

    def test_configured_path_key_absent_from_args_allows(self) -> None:
        """A path_key configured but missing from args must be skipped
        (not treated as a violation)."""
        cfg = _cfg(
            allowed_root="/home",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        assert check_allowed_root(cfg, "write_file", {})


class TestCfgHelperDefaults:
    def test_unknown_tool_defaults_to_high_risk(self) -> None:
        # was: test_unknown_tool_defaults_to_medium_risk asserting "medium" -- now "high"
        # per this plan's fail-safe acceptance criterion for unregistered tools.
        cfg = _cfg()
        assert classify_risk(cfg, "unknown_tool", {}) == "high"

    def test_shell_run_no_command_defaults_to_high_risk(self) -> None:
        cfg = _cfg()
        assert classify_risk(cfg, "shell_run", {}) == "high"

    def test_empty_allowed_root_permits_any_path(self) -> None:
        cfg = _cfg()
        assert (
            check_allowed_root(cfg, "write_file", {"path": "/any/absolute/path"})
            is True
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
        cfg = _cfg(allowed_root="", approval_github_allowed_repos=[])
        check_preflight(cfg, "read_text_file", {"path": "/tmp/f"})  # does not raise

    def test_denied_by_allowed_tools(self) -> None:
        cfg = _cfg(allowed_tools=["read_text_file"])
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "write_file", {})
        assert exc_info.value.audit_decision == "denied_allowed_tools"
        assert "write_file" in str(exc_info.value)

    def test_allowed_tools_none_does_not_block(self) -> None:
        cfg = _cfg(allowed_tools=[])
        check_preflight(cfg, "any_tool", {})  # does not raise

    def test_denied_by_root_jail(self) -> None:
        cfg = _cfg(
            allowed_root="/home",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(cfg, "write_file", {"path": "/tmp/foo"})
        assert exc_info.value.audit_decision == "denied_root_jail"

    def test_denied_by_repo_allowlist(self) -> None:
        cfg = _cfg(approval_github_allowed_repos=["myorg/allowed-repo"])
        with pytest.raises(PolicyViolationError) as exc_info:
            check_preflight(
                cfg, "github_push_files", {"owner": "myorg", "repo": "other-repo"}
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
            check_preflight(cfg, "dry_run", {})
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
            check_preflight(cfg, "read", {})
        except PolicyViolationError:
            pytest.fail("READ with allowed_tools should pass")


class TestEscalateForPath:
    def test_already_high_base_risk_no_escalation(self) -> None:
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg()
        assert _escalate_for_path(cfg, "high", {}) is None

    def test_no_matching_path_key_returns_none(self) -> None:
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg(approval_resource_keys={"path_keys": [], "branch_keys": []})
        assert _escalate_for_path(cfg, "medium", {"path": "/opt/llm/x"}) is None

    def test_configured_path_key_absent_from_args_skipped(self) -> None:
        """A path_key configured but missing from args must be skipped (not
        treated as a match), leaving the risk unescalated."""
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg(
            approval_protected_paths=["/etc"],
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        assert _escalate_for_path(cfg, "medium", {}) is None


class TestEscalateForGithubBranch:
    def test_non_github_tool_returns_none(self) -> None:
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg()
        assert _escalate_for_github_branch(cfg, "write_file", "medium", {}) is None

    def test_already_high_base_risk_no_escalation(self) -> None:
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg()
        assert _escalate_for_github_branch(cfg, "github_push_files", "high", {}) is None

    def test_configured_branch_key_absent_from_args_skipped(self) -> None:
        """A branch_key configured but missing from args must be skipped (not
        treated as a match), leaving the risk unescalated."""
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg(
            approval_high_risk_branches=["main"],
            approval_resource_keys={"path_keys": [], "branch_keys": ["branch"]},
        )
        assert (
            _escalate_for_github_branch(cfg, "github_push_files", "medium", {}) is None
        )

    def test_high_risk_branch_escalates(self) -> None:
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg(
            approval_high_risk_branches=["main"],
            approval_resource_keys={"path_keys": [], "branch_keys": ["branch"]},
        )
        assert (
            _escalate_for_github_branch(
                cfg, "github_push_files", "medium", {"branch": "main"}
            )
            == "high"
        )


class TestCheckAllowedRootEdgeCases:
    def test_invalid_path_returns_false(self) -> None:
        cfg = _cfg(
            allowed_root="/home",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        assert not check_allowed_root(cfg, "write_file", {"path": "\0invalid"})


class TestClassifyRiskConstantsFallback:
    """Tests for priority 3: tool_constants.py classification when not in tool_safety_tiers."""

    def test_delete_tool_defaults_to_high(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "delete_file", {})
        assert result == "high"

    def test_delete_directory_no_recursive_defaults_to_high(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "delete_directory", {"recursive": False})
        assert result == "high"

    def test_shell_tool_defaults_to_high(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "shell_run", {})
        assert result == "high"

    def test_write_tool_defaults_to_medium(self) -> None:
        cfg = _cfg()
        result = classify_risk(cfg, "write_file", {})
        assert result == "medium"

    def test_explicit_risk_rule_overrides_constants(self) -> None:
        cfg = _cfg(approval_risk_rules={"delete_file": "none"})
        result = classify_risk(cfg, "delete_file", {})
        assert result == "none"

    def test_safety_tier_overrides_constants(self) -> None:
        cfg = _cfg(tool_safety_tiers={"shell_run": "READ_ONLY"})
        result = classify_risk(cfg, "shell_run", {})
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
        cfg = _cfg(approval_shell_safe_prefixes=['"git log"'])
        result = classify_risk(cfg, "shell_run", {"command": '"git log"'})
        assert result == "none"

    def test_single_letter_prefix_matches_exact_name(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["c"])
        result = classify_risk(cfg, "shell_run", {"command": "c"})
        assert result == "none"

    def test_single_letter_prefix_rejects_longer_name(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["c"])
        result = classify_risk(cfg, "shell_run", {"command": "cat"})
        assert result == "high"

    def test_case_sensitive_prefix_reject(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["Cat"])
        result = classify_risk(cfg, "shell_run", {"command": "cat"})
        assert result == "high"

    def test_case_sensitive_prefix_accept(self) -> None:
        cfg = _cfg(approval_shell_safe_prefixes=["Cat"])
        result = classify_risk(cfg, "shell_run", {"command": "Cat"})
        assert result == "none"

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
        The command '$HOME' also becomes ['$HOME'], so they match."""
        cfg = _cfg(approval_shell_safe_prefixes=[r"\$HOME"])
        result = classify_risk(cfg, "shell_run", {"command": "$HOME"})
        assert result == "none"

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
        cfg = _cfg(approval_shell_safe_prefixes=['"git log"'])
        result = classify_risk(cfg, "shell_run", {"command": '"git log"'})
        assert result == "none"

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
        The command '$HOME' also becomes ['$HOME'], so they match."""
        cfg = _cfg(approval_shell_safe_prefixes=[r"\$HOME"])
        result = classify_risk(cfg, "shell_run", {"command": "$HOME"})
        assert result == "none"

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
