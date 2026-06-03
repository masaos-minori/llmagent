"""agent/tool_policy.py
Tool risk classification and pre-flight access checks.

Extracted from repl_tool_exec.py so policy rules can be tested and
modified without loading the full approval/execution stack.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from shared.tool_constants import DELETE_TOOLS, WRITE_TOOLS

if TYPE_CHECKING:
    from agent.config import AgentConfig


_EXEC_TOOLS: frozenset[str] = frozenset({"shell_run"})
_API_WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "github_push_files",
        "github_create_or_update_file",
        "github_delete_file",
        "github_merge_pull_request",
        "github_create_branch",
        "github_create_pull_request",
        "github_update_pull_request",
        "github_create_issue",
        "github_add_issue_comment",
    },
)

# Maps tool_safety_tiers tier → default approval risk level
_TIER_TO_RISK: dict[str, str] = {
    "READ_ONLY": "none",
    "WRITE_SAFE": "none",
    "WRITE_DANGEROUS": "medium",
    "ADMIN": "high",
}


def classify_operation_type(tool_name: str) -> str:
    """Return operation type: write | delete | execute | api_write | read."""
    if tool_name in WRITE_TOOLS:
        return "write"
    if tool_name in DELETE_TOOLS:
        return "delete"
    if tool_name in _EXEC_TOOLS:
        return "execute"
    if tool_name in _API_WRITE_TOOLS:
        return "api_write"
    return "read"


def _escalate_for_path(
    cfg: AgentConfig,
    base: str,
    args: dict[str, Any],
) -> str | None:
    """Return 'high' when any path arg is under a protected directory, else None."""
    if base == "high":
        return None
    path_keys = cfg.approval_resource_keys.get("path_keys", [])
    for key in path_keys:
        val = str(args.get(key) or "")
        if val and any(val.startswith(p) for p in cfg.approval_protected_paths):
            return "high"
    return None


def _escalate_for_github_branch(
    cfg: AgentConfig,
    tool_name: str,
    base: str,
    args: dict[str, Any],
) -> str | None:
    """Return 'high' when the target GitHub branch is in high_risk_branches, else None."""
    if not tool_name.startswith("github_") or base == "high":
        return None
    branch_keys = cfg.approval_resource_keys.get("branch_keys", [])
    for key in branch_keys:
        val = str(args.get(key) or "")
        if val and val in cfg.approval_high_risk_branches:
            return "high"
    return None


def classify_risk(cfg: AgentConfig, tool_name: str, args: dict[str, Any]) -> str:
    """Return the risk level: 'none' | 'medium' | 'high'.

    Order: explicit rule → tier fallback → escalation overrides.
    """
    base: str | None = cfg.approval_risk_rules.get(tool_name)
    if base is None:
        tier = cfg.tool_safety_tiers.get(tool_name, "WRITE_DANGEROUS")
        base = _TIER_TO_RISK[tier]
    if base == "none":
        return "none"
    if tool_name == "delete_directory" and args.get("recursive"):
        return "high"
    if tool_name == "shell_run":
        cmd = str(args.get("command", ""))
        if any(cmd.startswith(p) for p in cfg.approval_shell_safe_prefixes):
            return "none"
        return "high"
    if escalated := _escalate_for_path(cfg, base, args):
        return escalated
    if escalated := _escalate_for_github_branch(cfg, tool_name, base, args):
        return escalated
    return base


def check_allowed_root(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
) -> bool:
    """Return False when any path argument is outside cfg.allowed_root."""
    if not cfg.allowed_root:
        return True
    root = Path(cfg.allowed_root).resolve()
    path_keys = cfg.approval_resource_keys.get("path_keys", [])
    for key in path_keys:
        val = str(args.get(key) or "")
        if val:
            try:
                resolved = Path(val).resolve()
            except (ValueError, OSError):
                return False
            if not resolved.is_relative_to(root):
                return False
    return True


def check_allowed_repo(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
) -> bool:
    """Return False when a GitHub write tool targets a repo not in the allowlist."""
    if tool_name not in _API_WRITE_TOOLS:
        return True
    allowed = cfg.approval_github_allowed_repos
    if not allowed:
        return False
    owner = str(args.get("owner", ""))
    repo = str(args.get("repo", ""))
    return f"{owner}/{repo}" in allowed


def preflight_deny_reason(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
) -> tuple[str, str] | None:
    """Return (audit_decision, message) when a pre-flight check denies the call.

    Returns None when all checks pass.
    """
    if cfg.allowed_tools and tool_name not in cfg.allowed_tools:
        return (
            "denied_allowed_tools",
            f"  [DENIED] {tool_name}: not in allowed_tools for this session",
        )
    if not check_allowed_root(cfg, tool_name, args):
        return (
            "denied_root_jail",
            f"  [DENIED] {tool_name}: path outside allowed_root"
            f" ({cfg.allowed_root!r})",
        )
    if not check_allowed_repo(cfg, tool_name, args):
        return (
            "denied_repo_allowlist",
            f"  [DENIED] {tool_name}: repo not in approval_github_allowed_repos",
        )
    return None
