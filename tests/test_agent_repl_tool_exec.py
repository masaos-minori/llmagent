"""
tests/test_agent_repl_tool_exec.py
Unit tests for agent_repl_tool_exec security functions:
  - _classify_risk: tier fallback, delete_directory escalation
  - _check_allowed_root: ALLOWED_ROOT enforcement
  - _check_allowed_repo: GitHub repo allowlist (Fail-Closed)
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from agent.repl_tool_exec import (
    _check_allowed_repo,
    _check_allowed_root,
    _classify_risk,
)

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_cfg(
    *,
    approval_risk_rules: dict | None = None,
    tool_safety_tiers: dict | None = None,
    allowed_root: str = "",
    approval_github_allowed_repos: list | None = None,
    approval_protected_paths: list | None = None,
    approval_high_risk_branches: list | None = None,
    approval_shell_safe_prefixes: list | None = None,
    approval_resource_keys: dict | None = None,
) -> MagicMock:
    cfg = MagicMock()
    cfg.approval_risk_rules = (
        approval_risk_rules if approval_risk_rules is not None else {}
    )
    cfg.tool_safety_tiers = tool_safety_tiers if tool_safety_tiers is not None else {}
    cfg.allowed_root = allowed_root
    cfg.approval_github_allowed_repos = (
        approval_github_allowed_repos
        if approval_github_allowed_repos is not None
        else []
    )
    cfg.approval_protected_paths = approval_protected_paths or []
    cfg.approval_high_risk_branches = approval_high_risk_branches or []
    cfg.approval_shell_safe_prefixes = approval_shell_safe_prefixes or []
    cfg.approval_resource_keys = approval_resource_keys or {
        "path_keys": ["path", "file_path", "source", "destination"],
        "branch_keys": ["branch"],
    }
    return cfg


# ── _classify_risk: tier fallback ─────────────────────────────────────────────


class TestClassifyRiskTierFallback:
    def test_read_only_tier_maps_to_none(self) -> None:
        cfg = _make_cfg(
            tool_safety_tiers={"read_text_file": "READ_ONLY"},
        )
        assert _classify_risk(cfg, "read_text_file", {}) == "none"

    def test_write_safe_tier_maps_to_none(self) -> None:
        cfg = _make_cfg(
            tool_safety_tiers={"write_file": "WRITE_SAFE"},
        )
        assert _classify_risk(cfg, "write_file", {}) == "none"

    def test_write_dangerous_tier_maps_to_medium(self) -> None:
        cfg = _make_cfg(
            tool_safety_tiers={"delete_file": "WRITE_DANGEROUS"},
        )
        assert _classify_risk(cfg, "delete_file", {}) == "medium"

    def test_admin_tier_maps_to_high(self) -> None:
        cfg = _make_cfg(
            tool_safety_tiers={"shell_run": "ADMIN"},
            approval_shell_safe_prefixes=[],
        )
        assert _classify_risk(cfg, "shell_run", {"command": "rm -rf /"}) == "high"

    def test_unknown_tool_defaults_to_write_dangerous(self) -> None:
        # No risk_rules and no tier → Fail-Safe: WRITE_DANGEROUS → "medium"
        cfg = _make_cfg()
        assert _classify_risk(cfg, "some_unknown_tool", {}) == "medium"

    def test_approval_risk_rules_takes_priority_over_tier(self) -> None:
        # approval_risk_rules overrides tier default
        cfg = _make_cfg(
            approval_risk_rules={"write_file": "high"},
            tool_safety_tiers={"write_file": "WRITE_SAFE"},
        )
        assert _classify_risk(cfg, "write_file", {}) == "high"

    def test_approval_risk_rules_none_level_is_respected(self) -> None:
        # Explicit "none" in approval_risk_rules overrides tier
        cfg = _make_cfg(
            approval_risk_rules={"delete_file": "none"},
            tool_safety_tiers={"delete_file": "WRITE_DANGEROUS"},
        )
        assert _classify_risk(cfg, "delete_file", {}) == "none"


# ── _classify_risk: delete_directory escalation ───────────────────────────────


class TestClassifyRiskDeleteDirectory:
    def test_delete_directory_recursive_escalates_to_high(self) -> None:
        cfg = _make_cfg(
            approval_risk_rules={"delete_directory": "medium"},
        )
        assert _classify_risk(cfg, "delete_directory", {"recursive": True}) == "high"

    def test_delete_directory_non_recursive_stays_medium(self) -> None:
        cfg = _make_cfg(
            approval_risk_rules={"delete_directory": "medium"},
        )
        assert _classify_risk(cfg, "delete_directory", {"recursive": False}) == "medium"

    def test_delete_directory_no_recursive_key_stays_medium(self) -> None:
        cfg = _make_cfg(
            approval_risk_rules={"delete_directory": "medium"},
        )
        assert _classify_risk(cfg, "delete_directory", {}) == "medium"

    def test_delete_directory_recursive_via_tier_fallback_escalates(self) -> None:
        # Tier: WRITE_DANGEROUS → medium; then recursive escalates to high
        cfg = _make_cfg(
            tool_safety_tiers={"delete_directory": "WRITE_DANGEROUS"},
        )
        assert _classify_risk(cfg, "delete_directory", {"recursive": True}) == "high"


# ── _check_allowed_root ────────────────────────────────────────────────────────


class TestCheckAllowedRoot:
    def test_empty_allowed_root_allows_anything(self, tmp_path: Path) -> None:
        cfg = _make_cfg(allowed_root="")
        assert _check_allowed_root(cfg, "write_file", {"path": str(tmp_path / "a.txt")})

    def test_path_within_root_is_allowed(self, tmp_path: Path) -> None:
        cfg = _make_cfg(allowed_root=str(tmp_path))
        assert _check_allowed_root(
            cfg, "write_file", {"path": str(tmp_path / "sub" / "f.txt")}
        )

    def test_path_outside_root_is_denied(self, tmp_path: Path) -> None:
        root = tmp_path / "allowed"
        root.mkdir()
        cfg = _make_cfg(allowed_root=str(root))
        assert not _check_allowed_root(
            cfg, "write_file", {"path": str(tmp_path / "outside.txt")}
        )

    def test_path_at_root_boundary_is_allowed(self, tmp_path: Path) -> None:
        cfg = _make_cfg(allowed_root=str(tmp_path))
        # Exact root itself
        assert _check_allowed_root(cfg, "create_directory", {"path": str(tmp_path)})

    def test_tool_without_path_args_is_allowed(self, tmp_path: Path) -> None:
        # No path_keys match → all clear
        cfg = _make_cfg(
            allowed_root=str(tmp_path),
            approval_resource_keys={"path_keys": ["path"]},
        )
        assert _check_allowed_root(cfg, "shell_run", {"command": "ls"})

    def test_source_and_destination_both_checked(self, tmp_path: Path) -> None:
        root = tmp_path / "allowed"
        root.mkdir()
        outside = tmp_path / "other"
        outside.mkdir()
        cfg = _make_cfg(
            allowed_root=str(root),
            approval_resource_keys={"path_keys": ["source", "destination"]},
        )
        # source inside, destination outside → denied
        assert not _check_allowed_root(
            cfg,
            "move_file",
            {"source": str(root / "f.txt"), "destination": str(outside / "f.txt")},
        )

    def test_empty_path_value_is_skipped(self, tmp_path: Path) -> None:
        # Empty string path values are ignored
        cfg = _make_cfg(allowed_root=str(tmp_path))
        assert _check_allowed_root(cfg, "write_file", {"path": ""})


# ── _check_allowed_repo ────────────────────────────────────────────────────────


class TestCheckAllowedRepo:
    def test_non_github_write_tool_always_allowed(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        assert _check_allowed_repo(cfg, "write_file", {"owner": "x", "repo": "y"})

    def test_github_read_tool_always_allowed(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        assert _check_allowed_repo(
            cfg, "github_get_file_contents", {"owner": "x", "repo": "y"}
        )

    def test_fail_closed_empty_allowlist_denies_all_writes(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        assert not _check_allowed_repo(
            cfg, "github_push_files", {"owner": "myorg", "repo": "myrepo"}
        )

    def test_repo_in_allowlist_is_allowed(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=["myorg/myrepo"])
        assert _check_allowed_repo(
            cfg, "github_push_files", {"owner": "myorg", "repo": "myrepo"}
        )

    def test_repo_not_in_allowlist_is_denied(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=["myorg/myrepo"])
        assert not _check_allowed_repo(
            cfg, "github_push_files", {"owner": "myorg", "repo": "other"}
        )

    def test_delete_file_denied_when_allowlist_empty(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        assert not _check_allowed_repo(
            cfg, "github_delete_file", {"owner": "a", "repo": "b"}
        )

    def test_merge_pr_allowed_with_matching_repo(self) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=["org/repo"])
        assert _check_allowed_repo(
            cfg, "github_merge_pull_request", {"owner": "org", "repo": "repo"}
        )

    def test_missing_owner_repo_args_treated_as_empty_string(self) -> None:
        # owner/repo = "/" which won't match any allowlist entry
        cfg = _make_cfg(approval_github_allowed_repos=["org/repo"])
        assert not _check_allowed_repo(cfg, "github_push_files", {})

    @pytest.mark.parametrize(
        "tool_name",
        [
            "github_push_files",
            "github_create_or_update_file",
            "github_delete_file",
            "github_merge_pull_request",
            "github_create_pull_request",
            "github_update_pull_request",
            "github_create_branch",
            "github_create_issue",
            "github_add_issue_comment",
        ],
    )
    def test_all_github_write_tools_checked(self, tool_name: str) -> None:
        cfg = _make_cfg(approval_github_allowed_repos=[])
        assert not _check_allowed_repo(cfg, tool_name, {"owner": "a", "repo": "b"})
