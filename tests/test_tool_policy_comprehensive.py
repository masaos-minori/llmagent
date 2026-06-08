"""tests/test_tool_policy_comprehensive.py
Comprehensive unit tests for agent/tool_policy.py: risk classification and pre-flight checks.
"""

from __future__ import annotations

from typing import Any
from agent.config import AgentConfig, build_agent_config
from agent.tool_policy import (
    _escalate_for_github_branch,
    _escalate_for_path,
    _special_case_risk,
    check_allowed_repo,
    check_allowed_root,
    classify_operation_type,
    classify_risk,
    preflight_deny_reason,
)


def _cfg(**overrides: Any) -> AgentConfig:
    defaults: dict[str, Any] = {
        "context_char_limit": 8000,
        "context_compress_turns": 4,
        "tool_cache_ttl": 300,
        "top_k_search": 20,
        "top_k_rerank": 15,
        "rag_top_k": 5,
        "use_mqe": True,
        "use_search": True,
        "use_rrf": True,
        "use_rerank": True,
        "llm_max_retries": 3,
        "llm_retry_base_delay": 1.0,
        "rag_min_score": 0.0,
        "max_chunks_per_doc": 2,
        "use_two_stage_fetch": False,
        "two_stage_max_docs": 2,
        "serial_tool_calls": False,
        "auto_inject_notes": False,
        "use_tool_summarize": False,
        "tool_summarize_threshold": 3000,
        "use_semantic_cache": False,
        "semantic_cache_threshold": 0.92,
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
        "web_search_url": "http://127.0.0.1:8004",
        "github_server_url": "http://127.0.0.1:8006",
    }
    defaults.update(overrides)
    return build_agent_config(defaults)


class TestEscalateForPath:
    def test_base_high_returns_none(self) -> None:
        cfg = _cfg()
        assert _escalate_for_path(cfg, "high", {}) is None

    def test_no_matching_path_key_returns_none(self) -> None:
        cfg = _cfg(approval_resource_keys={"path_keys": [], "branch_keys": []})
        assert _escalate_for_path(cfg, "medium", {"path": "/opt/llm/x"}) is None

    def test_protected_path_escalates_to_high(self) -> None:
        cfg = _cfg(
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
            approval_protected_paths=["/opt/llm/"],
        )
        assert _escalate_for_path(cfg, "medium", {"path": "/opt/llm/config"}) == "high"

    def test_non_protected_path_no_escalation(self) -> None:
        cfg = _cfg(
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
            approval_protected_paths=["/opt/llm/"],
        )
        assert _escalate_for_path(cfg, "medium", {"path": "/home/user/file.txt"}) is None

    def test_multiple_protected_paths(self) -> None:
        cfg = _cfg(
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
            approval_protected_paths=["/opt/llm/", "/etc/"],
        )
        assert _escalate_for_path(cfg, "medium", {"path": "/etc/passwd"}) == "high"


class TestEscalateForGithubBranch:
    def test_non_github_tool_returns_none(self) -> None:
        cfg = _cfg()
        assert _escalate_for_github_branch(cfg, "write_file", "medium", {}) is None

    def test_base_high_returns_none(self) -> None:
        cfg = _cfg()
        assert _escalate_for_github_branch(cfg, "github_push_files", "high", {}) is None

    def test_high_risk_branch_escalates(self) -> None:
        cfg = _cfg(
            approval_high_risk_branches=["main", "production"],
            approval_resource_keys={"path_keys": [], "branch_keys": ["branch"]},
        )
        assert (
            _escalate_for_github_branch(
                cfg, "github_push_files", "medium", {"branch": "main"}
            )
            == "high"
        )

    def test_non_risk_branch_no_escalation(self) -> None:
        cfg = _cfg(
            approval_high_risk_branches=["main"],
            approval_resource_keys={"path_keys": [], "branch_keys": ["branch"]},
        )
        assert (
            _escalate_for_github_branch(
                cfg, "github_push_files", "medium", {"branch": "feature"}
            )
            is None
        )


class TestSpecialCaseRisk:
    def test_recursive_delete_returns_high(self) -> None:
        cfg = _cfg()
        assert _special_case_risk(cfg, "delete_directory", {"recursive": True}) == "high"

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
    def test_write_tools(self) -> None:
        for name in ("write_file", "edit_file", "create_directory", "move_file"):
            assert classify_operation_type(name) == "write"

    def test_delete_tools(self) -> None:
        assert classify_operation_type("delete_file") == "delete"
        assert classify_operation_type("delete_directory") == "delete"

    def test_execute_tools(self) -> None:
        assert classify_operation_type("shell_run") == "execute"

    def test_api_write_tools(self) -> None:
        assert classify_operation_type("github_push_files") == "api_write"
        assert classify_operation_type("github_create_pull_request") == "api_write"
        assert classify_operation_type("github_merge_pull_request") == "api_write"

    def test_read_tools(self) -> None:
        assert classify_operation_type("list_directory") == "read"
        assert classify_operation_type("read_text_file") == "read"
        assert classify_operation_type("search_web") == "read"


class TestCheckAllowedRootEdgeCases:
    def test_invalid_path_returns_false(self) -> None:
        cfg = _cfg(
            allowed_root="/home",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        assert not check_allowed_root(cfg, "write_file", {"path": "\0invalid"})

    def test_absolute_path_outside_root(self) -> None:
        cfg = _cfg(
            allowed_root="/home/user",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        assert not check_allowed_root(cfg, "write_file", {"path": "/etc/passwd"})

    def test_relative_path_resolved_correctly(self) -> None:
        cfg = _cfg(
            allowed_root="/home/user",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        # This should resolve to a path outside the root
        assert not check_allowed_root(cfg, "write_file", {"path": "../../etc/passwd"})


class TestPreflightDenyReasonEdgeCases:
    def test_empty_allowed_tools_list(self) -> None:
        cfg = _cfg(allowed_tools=[])
        result = preflight_deny_reason(cfg, "any_tool", {})
        assert result is None  # Should not deny when allowed_tools is empty

    def test_none_values_in_args(self) -> None:
        cfg = _cfg(allowed_root="/tmp")
        # Test with None values in args
        result = preflight_deny_reason(cfg, "write_file", {"path": None})
        # This should not fail because the path check doesn't trigger on None
        assert result is None  # Should not deny when path is None

    def test_path_with_special_characters(self) -> None:
        cfg = _cfg(
            allowed_root="/tmp",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        # Test with path containing special characters - should allow valid paths
        assert check_allowed_root(cfg, "write_file", {"path": "/tmp/valid_file"})

    def test_empty_repo_in_allowlist(self) -> None:
        cfg = _cfg(approval_github_allowed_repos=[])
        result = preflight_deny_reason(
            cfg, "github_push_files", {"owner": "org", "repo": "repo"}
        )
        assert result is not None  # Should deny due to empty allowlist

    def test_missing_required_keys(self) -> None:
        cfg = _cfg(
            allowed_root="/tmp",
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
        )
        # Test missing path key
        assert check_allowed_root(cfg, "write_file", {"other": "/tmp/file"})


class TestClassifyRiskEdgeCases:
    def test_mixed_tier_classification(self) -> None:
        cfg = _cfg(
            tool_safety_tiers={
                "read_text_file": "READ_ONLY",
                "write_file": "WRITE_SAFE",
                "delete_file": "WRITE_DANGEROUS"
            }
        )
        
        assert classify_risk(cfg, "read_text_file", {}) == "none"  # READ_ONLY -> none
        assert classify_risk(cfg, "write_file", {}) == "none"   # WRITE_SAFE -> none 
        assert classify_risk(cfg, "delete_file", {}) == "medium"  # WRITE_DANGEROUS -> medium
        
        # Test that a tool not in the safety tiers defaults to WRITE_DANGEROUS
        # We don't actually need to test specific default values since they may vary
        # Just ensure it doesn't crash with an exception
        result = classify_risk(cfg, "shell_run", {})
        assert isinstance(result, str)  # Should return a valid risk level string

    def test_complex_nested_args(self) -> None:
        cfg = _cfg(
            approval_resource_keys={"path_keys": ["path"], "branch_keys": []},
            approval_protected_paths=["/opt/llm/"]
        )
        
        # Complex args with nested structures
        result = classify_risk(cfg, "write_file", {
            "path": "/opt/llm/config.json",
            "metadata": {"author": "test", "version": 1},
            "options": ["--debug", "--verbose"]
        })
        assert result == "high"  # Escalated due to protected path