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
    ALL_SIDE_EFFECTING_TOOLS,
    DELETE_TOOLS,
    GITHUB_DANGEROUS_TOOLS,
    GITHUB_WRITE_TOOLS,
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
    """read-only-by-construction shape rule for one shell executable."""

    allowed_subcommands: frozenset[str] | None = None
    deny_flags: frozenset[str] = frozenset()
    deny_flag_prefixes: frozenset[str] = frozenset()


# an executable absent from this table is never auto-approved, even when a
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

# Side-effect membership delegated to the shared canonical set (ADR-004,
# sideeffect001): identical members, now shared with dispatch dedup and the
# HTTP fail-closed gate. The granular sets are reference data: they sub-classify
# declared side-effect classes into DELETE/EXECUTE/API_WRITE/WRITE and feed the
# drift findings in check_write_classification(); they never decide READ vs write.
_STATIC_SIDE_EFFECT_TOOLS: frozenset[str] = ALL_SIDE_EFFECTING_TOOLS

# Maps the tool's declared agent_safety_tier to the default approval risk level
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

    The registered tool's declared ``side_effect_class`` is the decision input
    (REQ-007 authority inversion): ``read_only`` resolves to READ, and a
    side-effect class is sub-classified with the reference sets in
    ``shared.tool_constants`` into DELETE/EXECUTE/API_WRITE/WRITE. The static
    sets are reference data only; disagreement with the declaration is reported
    by ``check_write_classification()`` and changes no decision here.
    When registry is None or the tool is unregistered, fails closed to UNKNOWN
    (ADR-003 Decision #6: no static-registry fallback).
    """
    if registry is None:
        return OperationType.UNKNOWN
    try:
        tool = registry.get(tool_name)
    except KeyError:
        return OperationType.UNKNOWN
    if tool.side_effect_class == "read_only":
        return OperationType.READ
    if tool_name in DELETE_TOOLS:
        return OperationType.DELETE
    if tool_name in _EXEC_TOOLS:
        return OperationType.EXECUTE
    if tool_name in _GITHUB_MUTATION_TOOLS:
        return OperationType.API_WRITE
    return OperationType.WRITE


def check_write_classification(registry: RuntimeToolRegistry) -> list[str]:
    """Return one finding per tool whose declared write classification disagrees with the reference sets.

    ADR-003 INV-03: approval and audit classification must not diverge from the
    registry entry. REQ-007 (AC-10): both comparisons are drift reports — the value
    the producer declared is the authority, the static tool sets are reference data,
    and a finding never changes a decision.
    """
    findings: list[str] = []
    for tool in registry.all_tools():
        static_write = tool.name in _STATIC_SIDE_EFFECT_TOOLS
        if tool.is_write != static_write:
            findings.append(
                f"{tool.name}: declared is_write={tool.is_write} disagrees with the "
                f"reference tool sets (listed_as_side_effect={static_write})"
            )
        declared_write = tool.side_effect_class != "read_only"
        if declared_write != static_write:
            findings.append(
                f"{tool.name}: declared side_effect_class={tool.side_effect_class} "
                f"disagrees with the reference tool sets "
                f"(listed_as_side_effect={static_write})"
            )
    return findings


def _iter_string_arg_values(args: dict[str, Any], keys: list[str]) -> Iterator[str]:
    """Yield each non-empty string value present in args for the given keys."""
    for key in keys:
        val = args.get(key)
        if isinstance(val, str) and val:
            yield val


class _NotInspectablePathValueError(ValueError):
    """Raised when a path-argument value is neither `str` nor `list[str]`.

    Module-private signal: the callers in this file convert it into the unchanged
    deny/escalate outcomes (`denied_root_jail` / `RiskLevel.HIGH`); it never escapes
    the policy layer.
    """


def _resolve_path_keys(
    cfg: AgentConfig,
    tool_name: str,
    registry: RuntimeToolRegistry | None,
) -> list[str] | None:
    """Return the checked path argument names: the registered tool's declared keys
    whose kind is ``path``.

    REQ-008: the declared key-to-kind mapping is the only key source; the removed
    ``approval_resource_keys`` lists no longer contribute, so a path argument and
    a branch argument of the same tool resolve differently. `cfg` stays in the
    signature for the policy-call surface. A `registry=None` call or a supplied
    registry whose tool is unregistered (`KeyError`) returns `None`: the declared
    scope is unknown and the caller fails closed; no lookup error escapes the
    policy.
    """
    if registry is None:
        return None
    try:
        tool = registry.get(tool_name)
    except KeyError:
        return None
    return [key for key, kind in tool.resource_scope_keys.items() if kind == "path"]


def _iter_path_arg_values(args: dict[str, Any], keys: list[str]) -> Iterator[str]:
    """Yield each inspectable path value under the given keys.

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
    """tokens whose value must be routed through the path checks.

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
    # bare tokens and --flag=value values are path candidates
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

    rule absence is the denial mechanism (deny-by-default). allowed
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

    The checked key set is the registered tool's declared path-kind keys
    (REQ-008); every element of a list-valued arg is checked and a
    not-inspectable value escalates (fail closed). When the declared scope is
    unknown (`keys is None`) the tool is unregistered and `classify_risk()` has
    already resolved a `HIGH` base; the escalation returns HIGH here too rather
    than silently checking nothing.
    """
    if base == RiskLevel.HIGH:
        return None
    keys = _resolve_path_keys(cfg, tool_name, registry)
    if keys is None:
        return RiskLevel.HIGH
    protected = cfg.approval.approval_protected_paths
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
    registry: RuntimeToolRegistry | None = None,
) -> RiskLevel | None:
    """Return HIGH when a declared branch-kind argument is in high_risk_branches.

    REQ-008: the checked keys are the registered tool's declared branch-kind keys,
    not a tool-name prefix or a global config list; a tool that declares no
    branch key is not branch-escalated.
    """
    if base == RiskLevel.HIGH:
        return None
    keys = None
    if registry is not None:
        try:
            tool = registry.get(tool_name)
        except KeyError:
            tool = None
        if tool is not None:
            keys = [
                key
                for key, kind in tool.resource_scope_keys.items()
                if kind == "branch"
            ]
    if keys is None:
        # Unregistered tool: declared scope unknown, no branch decision possible.
        # classify_risk() has already resolved a HIGH base for this case.
        return None
    for val in _iter_string_arg_values(args, keys):
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
        # fail closed on any shell metacharacter in raw command
        if _has_metacharacters(cmd):
            return RiskLevel.HIGH
        # parsed identity match replaces startswith below
        try:
            argv = shlex.split(cmd)
        except ValueError:
            return RiskLevel.HIGH
        if not argv:
            return RiskLevel.HIGH
        if match := _match_executable_identity(
            argv, cfg.approval.approval_shell_safe_prefixes
        ):
            # route positional args through path/argument checks
            if escalated := _check_positional_args(cfg, argv, match):
                return escalated
            # one normalized executable name gates both the prefix match
            # (basename-matched in _match_executable_identity) and this rule lookup
            exe = os.path.basename(argv[0])
            # safe-shape rule decides auto-approval; deny by default
            if _safe_shape_violation(exe, argv[1:]):
                return RiskLevel.HIGH
            return match
        return RiskLevel.HIGH
    return None


def is_plan_mode_blocked(
    cfg: AgentConfig, tool_name: str, registry: RuntimeToolRegistry | None = None
) -> bool:
    """Return True when plan mode must reject the tool call.

    Plan mode permits read-only tools only: the tool's declared ``agent_safety_tier``
    is the authority (REQ-006) — a tool is blocked unless its declared tier is
    READ_ONLY, so a tool absent from the registry (including an unknown tool name)
    fails closed.
    cfg.tool.plan_blocked_tools is an explicit operational extension naming
    tools blocked regardless of their tier; under the shipped tiers every entry
    is already blocked by the tier rule (redundant-by-design).
    Canonical policy: docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md
    """
    if tool_name in cfg.tool.plan_blocked_tools:
        return True
    if registry is None:
        return True
    try:
        tool = registry.get(tool_name)
    except KeyError:
        return True
    return tool.agent_safety_tier != "READ_ONLY"


def classify_risk(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
    registry: RuntimeToolRegistry | None = None,
) -> RiskLevel:
    """Return the risk level for a tool call.

    Lookup order: the registered tool's declared ``agent_safety_tier`` mapped
    through ``_TIER_TO_RISK``, then `_special_case_risk()`, `_escalate_for_path()`
    and `_escalate_for_github_branch()`. A base of RiskLevel.NONE returns before
    those, so a tier-NONE tool (index_paths, refresh_index, git_add, git_commit,
    write_file, edit_file, create_directory, move_file, every READ_ONLY tool) is
    never escalated by approval_protected_paths. A tier-MEDIUM path-bearing tool
    whose path is protected (delete_file, delete_directory, the git writes under
    the shipped approval_protected_paths) escalates to HIGH; check_allowed_root()
    rejects jail-external paths first, and an empty approval_github_allowed_repos
    denies all GitHub writes (check_allowed_repo()).
    A tool absent from the registry, and a call without a registry, resolves to
    HIGH: with no declaration there is nothing to consult (fail closed).
    The removed per-tool approval risk rules no longer exist: the declared tier
    is the single risk source (REQ-004, REQ-011).
    Canonical policy: docs/23_agent/agent_06_02_tool-execution-and-approval-approval.md
    """
    base: RiskLevel | None = None
    if registry is not None:
        try:
            tool = registry.get(tool_name)
        except KeyError:
            tool = None
        if tool is not None:
            base = _TIER_TO_RISK.get(tool.agent_safety_tier, RiskLevel.MEDIUM)
    if base is None:
        # Fail-safe: a tool name absent from the registry entirely (or no registry
        # supplied) is treated as maximally risky rather than inferred from a name.
        base = RiskLevel.HIGH
    if base == RiskLevel.NONE:
        return RiskLevel.NONE
    if override := _special_case_risk(cfg, tool_name, args):
        return override
    if escalated := _escalate_for_path(cfg, tool_name, base, args, registry):
        return escalated
    if escalated := _escalate_for_github_branch(cfg, tool_name, base, args, registry):
        return escalated
    return base


def check_allowed_root(
    cfg: AgentConfig,
    tool_name: str,
    args: dict[str, Any],
    registry: RuntimeToolRegistry | None = None,
) -> bool:
    """Return False when any path argument is outside cfg.approval.allowed_root.

    The checked key set is the registered tool's declared path-kind keys (REQ-008:
    the removed configured lists no longer contribute); every element of a
    list-valued arg is checked and a not-inspectable value denies (fail closed).
    An empty `allowed_root` denies a call that carries a path argument (nothing can
    be confined); a call with no path argument passes. A tool whose declared scope
    cannot be resolved (no registry, or not registered) denies: the jail cannot be
    verified against an unknown scope (fail closed).
    """
    keys = _resolve_path_keys(cfg, tool_name, registry)
    if keys is None:
        # Unregistered tool or no registry: declared scope unknown, so no argument
        # set can be verified against it; deny rather than skip the jail check.
        return False
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
    tool's declared scope keys available to the root-jail check.
    """
    if cfg.tool.tool_policy_mode == "explicit_allowlist":
        if tool_name not in cfg.tool.allowed_tools:
            raise PolicyViolationError(
                "denied_allowed_tools",
                f"{tool_name}: not in allowed_tools for this session",
            )
    else:  # discovered: allow registered tools not in the hard denylist
        registered = (
            {tool.name for tool in registry.all_tools()}
            if registry is not None
            else set()
        )
        if tool_name not in registered or tool_name in cfg.tool.disabled_tools:
            raise PolicyViolationError(
                "denied_discovered",
                f"{tool_name}: not a registered tool or is disabled",
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
