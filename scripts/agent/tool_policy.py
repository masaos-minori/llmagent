"""agent/tool_policy.py
Tool risk classification and pre-flight access checks.

Policy rules are isolated here so they can be tested independently
of the approval/execution stack.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from shared.tool_constants import DELETE_TOOLS, WRITE_TOOLS

from agent.tool_enums import OperationType, RiskLevel
from agent.tool_exceptions import PolicyViolationError

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
_TIER_TO_RISK: dict[str, RiskLevel] = {
    "READ_ONLY": RiskLevel.NONE,
    "WRITE_SAFE": RiskLevel.NONE,
    "WRITE_DANGEROUS": RiskLevel.MEDIUM,
    "ADMIN": RiskLevel.HIGH,
}


def classify_operation_type(tool_name: str) -> OperationType:
    """Return the operation type for a tool."""
    if tool_name in WRITE_TOOLS:
        return OperationType.WRITE
    if tool_name in DELETE_TOOLS:
        return OperationType.DELETE
    if tool_name in _EXEC_TOOLS:
        return OperationType.EXECUTE
    if tool_name in _API_WRITE_TOOLS:
        return OperationType.API_WRITE
    return OperationType.READ


def _escalate_for_path(
    cfg: AgentConfig,
    base: RiskLevel,
    args: dict[str, Any],
) -> RiskLevel | None:
    """Return HIGH when any path arg is under a protected directory, else None."""
    if base == RiskLevel.HIGH:
        return None
    path_keys = cfg.approval.approval_resource_keys.get("path_keys", [])
    for key in path_keys:
        val = args.get(key)
        if not isinstance(val, str) or not val:
            continue
        if any(val.startswith(p) for p in cfg.approval.approval_protected_paths):
            return RiskLevel.HIGH
    return None


def _escalate_for_github_branch(
    cfg: AgentConfig,
    tool_name: str,
    base: RiskLevel,
    args: dict[str, Any],
) -> RiskLevel | None:
    """Return HIGH when the target GitHub branch is in high_risk_branches, else None."""
    if not tool_name.startswith("github_") or base == RiskLevel.HIGH:
        return None
    branch_keys = cfg.approval.approval_resource_keys.get("branch_keys", [])
    for key in branch_keys:
        val = args.get(key)
        if not isinstance(val, str) or not val:
            continue
        if val in cfg.approval.approval_high_risk_branches:
            return RiskLevel.HIGH
    return None


def _special_case_risk(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
) -> RiskLevel | None:
    """Return a fixed risk level for tools with argument-dependent rules, else None.

    Covers delete_directory (recursive escalation) and shell_run (safe-prefix bypass).
    """
    if tool_name == "delete_directory" and args.get("recursive"):
        return RiskLevel.HIGH
    for flag in ("force", "overwrite", "clobber"):
        if args.get(flag) is True:
            return RiskLevel.HIGH
    if tool_name == "shell_run":
        cmd = args.get("command")
        if not isinstance(cmd, str):
            return RiskLevel.HIGH
        if any(cmd.startswith(p) for p in cfg.approval.approval_shell_safe_prefixes):
            return RiskLevel.NONE
        return RiskLevel.HIGH
    return None


def classify_risk(cfg: AgentConfig, tool_name: str, args: dict[str, Any]) -> RiskLevel:
    """Return the risk level for a tool call.

    Order: explicit rule → tier fallback → special-case → escalation overrides.
    """
    base: RiskLevel | None = None
    raw_rule = cfg.approval.approval_risk_rules.get(tool_name)
    if raw_rule is not None:
        base = RiskLevel(raw_rule)
    if base is None:
        tier = cfg.approval.tool_safety_tiers.get(tool_name, "WRITE_DANGEROUS")
        base = _TIER_TO_RISK.get(tier, RiskLevel.MEDIUM)
    if base == RiskLevel.NONE:
        return RiskLevel.NONE
    if override := _special_case_risk(cfg, tool_name, args):
        return override
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
    """Return False when any path argument is outside cfg.approval.allowed_root."""
    if not cfg.approval.allowed_root:
        return True
    root = Path(cfg.approval.allowed_root).resolve()
    path_keys = cfg.approval.approval_resource_keys.get("path_keys", [])
    for key in path_keys:
        val = args.get(key)
        if not isinstance(val, str) or not val:
            continue
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
    allowed = cfg.approval.approval_github_allowed_repos
    if not allowed:
        return False
    owner = args.get("owner")
    repo = args.get("repo")
    if not isinstance(owner, str) or not isinstance(repo, str):
        return False
    return f"{owner}/{repo}" in allowed


def check_preflight(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
) -> None:
    """Raise PolicyViolationError when a pre-flight check denies the tool call.

    Does nothing when all checks pass.
    """
    if cfg.tool.allowed_tools and tool_name not in cfg.tool.allowed_tools:
        raise PolicyViolationError(
            "denied_allowed_tools",
            f"  [DENIED] {tool_name}: not in allowed_tools for this session",
        )
    if not check_allowed_root(cfg, tool_name, args):
        raise PolicyViolationError(
            "denied_root_jail",
            f"  [DENIED] {tool_name}: path outside allowed_root ({cfg.approval.allowed_root!r})",
        )
    if not check_allowed_repo(cfg, tool_name, args):
        raise PolicyViolationError(
            "denied_repo_allowlist",
            f"  [DENIED] {tool_name}: repo not in approval_github_allowed_repos",
        )


def preflight_deny_reason(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
) -> tuple[str, str] | None:
    """Deprecated: use check_preflight() instead.

    Returns (audit_decision, message) when a pre-flight check denies the call,
    or None when all checks pass.
    """
    try:
        check_preflight(cfg, tool_name, args)
        return None
    except PolicyViolationError as e:
        return (e.audit_decision, str(e))
