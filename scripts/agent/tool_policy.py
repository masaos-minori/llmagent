"""scripts/agent/tool_policy.py

Tool risk classification and pre-flight access checks.

Policy rules are isolated here so they can be tested independently
of the approval/execution stack.
"""

from __future__ import annotations

import os
import re
import shlex
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

from shared.tool_constants import (
    CICD_WRITE_TOOLS,
    DELETE_TOOLS,
    GIT_WRITE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_WRITE_TOOLS,
    MDQ_WRITE_TOOLS,
    RAG_WRITE_TOOLS,
    SHELL_TOOLS,
    WRITE_TOOLS,
)

from agent.tool_enums import OperationType, RiskLevel
from agent.tool_exceptions import PolicyViolationError

if TYPE_CHECKING:
    from shared.runtime_tool_registry import RuntimeToolRegistry

    from agent.config_dataclasses import AgentConfig


_EXEC_TOOLS: frozenset[str] = frozenset({"shell_run"})

# Shell metacharacters/control operators — fail closed on any detection
_METACHAR_RE = re.compile(r"[;|&]|&&|\|\||`|\$\(|<\(|>\(|>>|<<|[<>]|[\r\n]")


@dataclass(frozen=True)
class _ShellShapeRule:
    """REQ-007: read-only-by-construction shape rule for one shell executable."""

    allowed_subcommands: frozenset[str] | None = None
    deny_flags: frozenset[str] = frozenset()
    deny_flag_prefixes: frozenset[str] = frozenset()


# REQ-006: an executable absent from this table is never auto-approved, even when a
# config approval_shell_safe_prefixes entry gates it. Interpreters and test runners
# (python, python3, pytest, uv) have no entry by design — absence is the denial.
_SAFE_SHELL_SHAPES: dict[str, _ShellShapeRule] = {
    "ls": _ShellShapeRule(),
    "pwd": _ShellShapeRule(),
    "echo": _ShellShapeRule(),
    "cat": _ShellShapeRule(),
    "grep": _ShellShapeRule(deny_flags=frozenset({"-r", "-R"})),
    "find": _ShellShapeRule(deny_flags=frozenset({"-exec", "-delete", "-ok"})),
    "git": _ShellShapeRule(
        allowed_subcommands=frozenset({"log", "status", "show", "diff", "branch"}),
        deny_flags=frozenset(
            {"-D", "-d", "-M", "-m", "-c", "--delete", "--move", "--copy"}
        ),
        deny_flag_prefixes=frozenset({"--output"}),
    ),
}
_GITHUB_MUTATION_TOOLS: frozenset[str] = GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS

# Per-server write-tool sets not covered by the generic WRITE_TOOLS frozenset
# (which only lists the file[read/write/delete] server's write tools).
# See shared/tool_constants.py for the source of each set.
_ALL_WRITE_TOOLS: frozenset[str] = (
    WRITE_TOOLS | MDQ_WRITE_TOOLS | RAG_WRITE_TOOLS | CICD_WRITE_TOOLS | GIT_WRITE_TOOLS
)

_STATIC_SIDE_EFFECT_TOOLS: frozenset[str] = (
    _ALL_WRITE_TOOLS | DELETE_TOOLS | _EXEC_TOOLS | _GITHUB_MUTATION_TOOLS
)

# Maps tool_safety_tiers tier → default approval risk level
_TIER_TO_RISK: dict[str, RiskLevel] = {
    "READ_ONLY": RiskLevel.NONE,
    "WRITE_SAFE": RiskLevel.NONE,
    "WRITE_DANGEROUS": RiskLevel.MEDIUM,
    "ADMIN": RiskLevel.HIGH,
}


def classify_operation_type(
    tool_name: str, registry: RuntimeToolRegistry | None = None
) -> OperationType:
    """Return the operation type for a tool.

    When registry is provided, consults RuntimeToolRegistry for the UNKNOWN/READ
    decision (ADR-003 Decision #8). When registry is None, fails closed to UNKNOWN
    (ADR-003 Decision #6: no static-registry fallback).
    """
    if tool_name in _ALL_WRITE_TOOLS:
        return OperationType.WRITE
    if tool_name in DELETE_TOOLS:
        return OperationType.DELETE
    if tool_name in _EXEC_TOOLS:
        return OperationType.EXECUTE
    if tool_name in _GITHUB_MUTATION_TOOLS:
        return OperationType.API_WRITE
    if registry is None:
        return OperationType.UNKNOWN
    try:
        tool = registry.get(tool_name)
    except KeyError:
        return OperationType.UNKNOWN
    if tool.is_write:
        return OperationType.WRITE
    return OperationType.READ


def check_write_classification(registry: RuntimeToolRegistry) -> list[str]:
    """Return one finding per tool whose RuntimeTool write flag disagrees with the static sets.

    ADR-003 INV-03: approval and audit classification must not diverge from the
    registry's write attribute.
    """
    findings: list[str] = []
    for tool in registry.all_tools():
        static_write = tool.name in _STATIC_SIDE_EFFECT_TOOLS
        if tool.is_write != static_write:
            findings.append(
                f"{tool.name}: RuntimeTool.is_write={tool.is_write} but the static "
                f"tool sets classify it as side_effect={static_write}"
            )
    return findings


def _iter_string_arg_values(args: dict[str, Any], keys: list[str]) -> Iterator[str]:
    """Yield each non-empty string value present in args for the given keys."""
    for key in keys:
        val = args.get(key)
        if isinstance(val, str) and val:
            yield val


class _NotInspectablePathValueError(ValueError):
    """Raised when a path-argument value is neither `str` nor `list[str]` (REQ-002).

    Module-private signal: the callers in this file convert it into the unchanged
    deny/escalate outcomes (`denied_root_jail` / `RiskLevel.HIGH`); it never escapes
    the policy layer.
    """


def _resolve_path_keys(
    cfg: AgentConfig,
    tool_name: str,
    registry: RuntimeToolRegistry | None,
) -> list[str] | None:
    """Return the checked path argument names: configured path_keys unioned with the
    registered tool's declared resource_scope_keys (REQ-001).

    `registry=None` returns the configured keys only (optional-registry callers/tests
    keep configured-key behavior). A supplied registry whose tool is unregistered
    (`KeyError`) returns `None` so the caller fails closed; no lookup error escapes the
    policy (REQ-003). Order is stable: configured keys first.
    """
    keys = list(cfg.approval.approval_resource_keys.get("path_keys", []))
    if registry is None:
        return keys
    try:
        tool = registry.get(tool_name)
    except KeyError:
        return None
    keys.extend(key for key in tool.resource_scope_keys if key not in keys)
    return keys


def _configured_path_keys(cfg: AgentConfig) -> list[str]:
    """The configured ``approval_resource_keys.path_keys`` with no registry lookup.

    Used to validate a path argument when the tool is unregistered: the declared
    scope is unknown, so only configured keys can be checked.
    """
    return list(cfg.approval.approval_resource_keys.get("path_keys", []))


def _iter_path_arg_values(args: dict[str, Any], keys: list[str]) -> Iterator[str]:
    """Yield each inspectable path value under the given keys (REQ-002).

    A non-empty `str` value yields as today; a `list` value yields each non-empty
    `str` element. A value that is neither, or a `list` containing a non-string
    element, raises `_NotInspectablePathValueError` so callers fail closed. Absent
    keys and empty strings keep today's skip semantics.
    """
    for key in keys:
        val = args.get(key)
        if val is None:
            continue
        if isinstance(val, str):
            if val:
                yield val
        elif isinstance(val, list):
            for item in val:
                if isinstance(item, str):
                    if item:
                        yield item
                else:
                    raise _NotInspectablePathValueError(
                        f"{key}: list element {item!r} is not a string"
                    )
        else:
            raise _NotInspectablePathValueError(
                f"{key}: value {val!r} is neither a string nor a list of strings"
            )


def _has_metacharacters(cmd: str) -> bool:
    """Return True if the raw command contains shell metacharacters/control operators."""
    return bool(_METACHAR_RE.search(cmd))


def _match_executable_identity(
    argv: list[str],
    prefixes: list[str],
) -> RiskLevel | None:
    """Return NONE if the parsed command exactly matches a safe prefix entry, else None."""
    if not argv:
        return None
    for prefix_entry in prefixes:
        prefix_tokens = shlex.split(prefix_entry) if prefix_entry.strip() else []
        if not prefix_tokens:
            continue
        # Single-word prefix: match basename of the first argv token
        if len(prefix_tokens) == 1:
            if os.path.basename(argv[0]) == prefix_tokens[0]:
                return RiskLevel.NONE
        # Multi-word prefix: match corresponding leading tokens
        elif len(argv) >= len(prefix_tokens):
            if all(
                os.path.basename(a) == p
                for a, p in zip(argv[: len(prefix_tokens)], prefix_tokens)
            ):
                return RiskLevel.NONE
    return None


def _iter_path_candidates(argv: list[str]) -> list[str]:
    """REQ-001: tokens whose value must be routed through the path checks.

    A bare token is a candidate; a `--flag=value` token contributes the text after its
    first equals sign. Long flags without a value, the end-of-options marker, short
    flags and empty values contribute nothing (attached short-flag values and
    `key=value` operands are out of scope).
    """
    candidates: list[str] = []
    for token in argv[1:]:
        if not token.startswith("-"):
            candidates.append(token)
        elif token.startswith("--") and "=" in token:
            value = token.split("=", 1)[1]
            if value:
                candidates.append(value)
    return candidates


def _check_positional_args(
    cfg: AgentConfig,
    argv: list[str],
    base: RiskLevel,
) -> RiskLevel | None:
    """Route positional and flag-value args through protected-path and allowed-root checks."""
    if base == RiskLevel.HIGH:
        return None
    # REQ-001: bare tokens and --flag=value values are path candidates
    positional = _iter_path_candidates(argv)
    if not positional:
        return None
    for pos in positional:
        # Check protected paths
        if any(pos.startswith(p) for p in cfg.approval.approval_protected_paths):
            return RiskLevel.HIGH
        # Check allowed_root
        if not cfg.approval.allowed_root:
            # Empty allowed_root: a path candidate cannot be confined (fail closed).
            return RiskLevel.HIGH
        root = Path(cfg.approval.allowed_root).resolve()
        try:
            resolved = Path(pos).resolve()
        except (ValueError, OSError):
            return RiskLevel.HIGH
        if not resolved.is_relative_to(root):
            return RiskLevel.HIGH
    return None


def _safe_shape_violation(exe: str, argv: list[str]) -> bool:
    """Return True when the argument tail violates, or has no, safe-shape rule for exe.

    REQ-006: rule absence is the denial mechanism (deny-by-default). REQ-007: allowed
    subcommands and denied flags are per-executable. `argv` is the tail after the
    executable token.
    """
    rule = _SAFE_SHELL_SHAPES.get(exe)
    if rule is None:
        return True
    tokens = argv
    if rule.allowed_subcommands is not None:
        subcommand = argv[0] if argv else ""
        if subcommand not in rule.allowed_subcommands:
            return True
        tokens = argv[1:]
    if any(token in rule.deny_flags for token in tokens):
        return True
    return any(token.startswith(p) for p in rule.deny_flag_prefixes for token in tokens)


def _escalate_for_path(
    cfg: AgentConfig,
    tool_name: str,
    base: RiskLevel,
    args: dict[str, Any],
    registry: RuntimeToolRegistry | None = None,
) -> RiskLevel | None:
    """Return HIGH when any path arg is under a protected directory, else None.

    The checked key set is the configured path_keys unioned with the registered
    tool's declared scope keys; every element of a list-valued arg is checked and a
    not-inspectable value escalates (fail closed).
    """
    if base == RiskLevel.HIGH:
        return None
    protected = cfg.approval.approval_protected_paths
    keys = _resolve_path_keys(cfg, tool_name, registry)
    if keys is None:
        # Unregistered tool: declared scope unknown; check configured keys only.
        keys = _configured_path_keys(cfg)
    try:
        for val in _iter_path_arg_values(args, keys):
            if any(val.startswith(p) for p in protected):
                return RiskLevel.HIGH
    except _NotInspectablePathValueError:
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
    for val in _iter_string_arg_values(args, branch_keys):
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
        # REQ-002: fail closed on any shell metacharacter in raw command
        if _has_metacharacters(cmd):
            return RiskLevel.HIGH
        # REQ-001: parsed identity match replaces startswith below
        try:
            argv = shlex.split(cmd)
        except ValueError:
            return RiskLevel.HIGH
        if not argv:
            return RiskLevel.HIGH
        if match := _match_executable_identity(
            argv, cfg.approval.approval_shell_safe_prefixes
        ):
            # REQ-003: route positional args through path/argument checks
            if escalated := _check_positional_args(cfg, argv, match):
                return escalated
            # REQ-008: one normalized executable name gates both the prefix match
            # (basename-matched in _match_executable_identity) and this rule lookup
            exe = os.path.basename(argv[0])
            # REQ-006/REQ-007: safe-shape rule decides auto-approval; deny by default
            if _safe_shape_violation(exe, argv[1:]):
                return RiskLevel.HIGH
            return match
        return RiskLevel.HIGH
    return None


def is_plan_mode_blocked(cfg: AgentConfig, tool_name: str) -> bool:
    """Return True when plan mode must reject the tool call.

    Plan mode permits read-only tools only: a tool is blocked unless its
    tool_safety_tiers entry is READ_ONLY, so a tool without a tier (including
    an unknown tool name) fails closed. cfg.tool.plan_blocked_tools names
    additional tools that are blocked regardless of their tier.
    """
    if tool_name in cfg.tool.plan_blocked_tools:
        return True
    return cfg.approval.tool_safety_tiers.get(tool_name) != "READ_ONLY"


def classify_risk(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
    registry: RuntimeToolRegistry | None = None,
) -> RiskLevel:
    """Return the risk level for a tool call.

    Order: explicit rule → tier fallback → special-case → escalation overrides.
    The registry parameter is threaded through to Priority 3 (operation type
    classification) so UNKNOWN/READ decisions use RuntimeToolRegistry instead
    of the static ToolRegistry.
    """
    base: RiskLevel | None = None
    raw_rule = cfg.approval.approval_risk_rules.get(tool_name)
    if raw_rule is not None:
        base = RiskLevel(raw_rule)
    # Priority 2: tool_safety_tiers
    if base is None and tool_name in cfg.approval.tool_safety_tiers:
        tier = cfg.approval.tool_safety_tiers[tool_name]
        base = _TIER_TO_RISK.get(tier, RiskLevel.MEDIUM)
    # Priority 3: tool_constants.py classification
    if base is None:
        if classify_operation_type(tool_name, registry) == OperationType.UNKNOWN:
            # Fail-safe: a tool name absent from the registry entirely (not just
            # untiered) is treated as maximally risky rather than defaulting to
            # MEDIUM like a real-but-untiered tool would.
            base = RiskLevel.HIGH
        elif tool_name in DELETE_TOOLS or tool_name in SHELL_TOOLS:
            base = RiskLevel.HIGH
        elif tool_name in WRITE_TOOLS:
            base = RiskLevel.MEDIUM
        else:
            base = RiskLevel.MEDIUM  # Priority 4: unchanged default
    if base == RiskLevel.NONE:
        return RiskLevel.NONE
    if override := _special_case_risk(cfg, tool_name, args):
        return override
    if escalated := _escalate_for_path(cfg, tool_name, base, args, registry):
        return escalated
    if escalated := _escalate_for_github_branch(cfg, tool_name, base, args):
        return escalated
    return base


def check_allowed_root(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
    registry: RuntimeToolRegistry | None = None,
) -> bool:
    """Return False when any path argument is outside cfg.approval.allowed_root.

    The checked key set is the configured path_keys unioned with the registered
    tool's declared scope keys; every element of a list-valued arg is checked and a
    not-inspectable value denies (fail closed). An empty `allowed_root` denies a
    call that carries a path argument (nothing can be confined); a call with no
    path argument passes.
    """
    keys = _resolve_path_keys(cfg, tool_name, registry)
    if keys is None:
        # Unregistered tool: declared scope unknown. Deny when it carries a path
        # argument (cannot be verified against declared scope); a path-less call
        # passes the root-jail check.
        for _ in _iter_path_arg_values(args, _configured_path_keys(cfg)):
            return False
        return True
    if not cfg.approval.allowed_root:
        try:
            next(_iter_path_arg_values(args, keys))
        except StopIteration:
            return True
        except _NotInspectablePathValueError:
            return False
        return False
    root = Path(cfg.approval.allowed_root).resolve()
    try:
        for val in _iter_path_arg_values(args, keys):
            try:
                resolved = Path(val).resolve()
            except (ValueError, OSError):
                return False
            if not resolved.is_relative_to(root):
                return False
    except _NotInspectablePathValueError:
        return False
    return True


def check_allowed_repo(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
) -> bool:
    """Return False when a GitHub write tool targets a repo not in the allowlist."""
    if tool_name not in _GITHUB_MUTATION_TOOLS:
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
    registry: RuntimeToolRegistry | None = None,
) -> None:
    """Raise PolicyViolationError when a pre-flight check denies the tool call.

    Does nothing when all checks pass. The optional registry makes the registered
    tool's declared scope keys available to the root-jail check (REQ-003).
    """
    if tool_name not in cfg.tool.allowed_tools:
        raise PolicyViolationError(
            "denied_allowed_tools",
            f"{tool_name}: not in allowed_tools for this session",
        )
    if not check_allowed_root(cfg, tool_name, args, registry):
        raise PolicyViolationError(
            "denied_root_jail",
            f"{tool_name}: path outside allowed_root ({cfg.approval.allowed_root!r})",
        )
    if not check_allowed_repo(cfg, tool_name, args):
        raise PolicyViolationError(
            "denied_repo_allowlist",
            f"{tool_name}: repo not in approval_github_allowed_repos",
        )
