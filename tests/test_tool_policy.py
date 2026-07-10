"""
tests/test_tool_policy.py
Unit tests for tool_policy.py: risk classification, path/repo checks, pre-flight deny.
"""

from __future__ import annotations

from typing import Any

import pytest
from agent.config_builders import build_agent_config
from agent.config_dataclasses import AgentConfig
from agent.tool_exceptions import PolicyViolationError
from agent.tool_policy import (
    check_allowed_repo,
    check_allowed_root,
    check_preflight,
    classify_risk,
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
        "mcp_servers": {
            "_dummy": {"transport": "http", "url": "http://127.0.0.1:9999"}
        },
    }
    defaults.update(overrides)
    return build_agent_config(defaults)


class TestClassifyRisk:
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
        result = classify_risk(cfg, "read_text_file", {"path": "/tmp/f"})
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


class TestCfgHelperDefaults:
    def test_unknown_tool_defaults_to_medium_risk(self) -> None:
        cfg = _cfg()
        assert classify_risk(cfg, "unknown_tool", {}) == "medium"

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


class TestEscalateForPath:
    def test_already_high_base_risk_no_escalation(self) -> None:
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg()
        assert _escalate_for_path(cfg, "high", {}) is None

    def test_no_matching_path_key_returns_none(self) -> None:
        from agent.tool_policy import _escalate_for_path

        cfg = _cfg(approval_resource_keys={"path_keys": [], "branch_keys": []})
        assert _escalate_for_path(cfg, "medium", {"path": "/opt/llm/x"}) is None


class TestEscalateForGithubBranch:
    def test_non_github_tool_returns_none(self) -> None:
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg()
        assert _escalate_for_github_branch(cfg, "write_file", "medium", {}) is None

    def test_already_high_base_risk_no_escalation(self) -> None:
        from agent.tool_policy import _escalate_for_github_branch

        cfg = _cfg()
        assert _escalate_for_github_branch(cfg, "github_push_files", "high", {}) is None

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
