#!/usr/bin/env python3
"""scripts/shared/resource_scope.py

Resource-scope resolution and schema-2.0 contract validation.

`resolve_resource_scopes()` turns a `RuntimeTool`'s declared
`resource_scope_kind`/`resource_scope_keys` plus a call's actual arguments into a tuple of
kind-prefixed scope strings. `_scopes_conflict()` is the overlap predicate consumed later
by `scripts/agent/tool_scheduler.py`'s conflict-graph grouping.
`validate_tool_schema_v2()` validates a raw MCP tool-list entry against the schema-2.1
contract (schema-2.0 fields unchanged plus the declared policy fields).

Import-layer design decisions: this module is part of the `shared` leaf layer and MUST
NOT import `agent`, `mcp_servers`, `rag`, or `db` (enforced by the `shared-is-leaf`
`.importlinter` contract). It imports `RuntimeTool` from `shared.runtime_tool` for its
type signature only and otherwise operates on plain built-in types (`Mapping[str, Any]`,
`dict[str, Any]`, `tuple[str, ...]`) so it stays independently unit-testable with no
registry/agent dependency. Do not "fix" this by importing from `agent` even if a future
caller lives there — callers reach into this module, not the other way around.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import PurePosixPath
from typing import Any, get_args

from shared.runtime_tool import AgentSafetyTier, RuntimeTool
from shared.tool_metadata import (
    PREVIEW_CAPABILITY_VALUES,
    RECONCILIATION_POLICY_VALUES,
    RESOURCE_KEY_KIND_VALUES,
    RETRY_POLICY_VALUES,
    SIDE_EFFECT_CLASS_VALUES,
    TOOL_FIELD_SET_VERSION,
)

# Known `resource_scope_kind` vocabulary, per the plan's Design section scope-string
# examples and the Affected-areas table's per-server kind assignments. `""` denotes an
# unscoped tool (no conflict-graph entry needed).
_KNOWN_SCOPE_KINDS = frozenset(
    {
        "",
        "filesystem",
        "git_repo",
        "github_repo",
        "github_branch",
        "github_issue",
        "github_pull_request",
        "cicd_workflow",
        "rag_store",
        "mdq_store",
        "process",
    }
)

# Scope kinds whose values are filesystem-like paths and should be normalized via
# `PurePosixPath` rather than used as a raw string.
_FILESYSTEM_LIKE_KINDS = frozenset({"filesystem", "git_repo"})

# Fail-closed fallback scope for a write tool whose declared resource_scope_keys did not
# resolve to any present, non-empty argument value. Never the bare tool name and never an
# empty tuple: an under-specified write tool must never look freely parallelizable to the
# scheduler.
_FALLBACK_WRITE_SCOPE = "global:write"

# Scope kinds whose present key values are composed into a single joined scope string
# (rather than one scope string per key), keyed by the join separator.
_COMPOSED_KIND_SEPARATORS = {
    "github_repo": "/",
    "github_branch": "/",
    "github_issue": "/",
    "github_pull_request": "/",
    "cicd_workflow": ":",
}

# Descendant GitHub kinds whose identity is scoped by the `github_repo:` ancestor kind
# (`<owner>/<repo>` ancestor identity, `<owner>/<repo>/<name>` descendant identity).
_GITHUB_FINE_KINDS = frozenset({"github_branch", "github_issue", "github_pull_request"})

# Declared agent-safety tiers the schema validator accepts (same Literal the builder
# types against; `shared` reads `runtime_tool`, never `agent`).
_KNOWN_AGENT_SAFETY_TIERS: frozenset[str] = frozenset(get_args(AgentSafetyTier))


def resolve_resource_scopes(
    tool: RuntimeTool, args: Mapping[str, Any]
) -> tuple[str, ...]:
    """Resolve the resource scope strings a tool call occupies.

    Each returned string has the shape `f"{tool.resource_scope_kind}:{normalized_value}"`,
    built from `tool.resource_scope_keys` in declared order (only keys present in *args*
    with a non-empty value contribute a scope string). Kind-prefixing makes cross-kind
    string-equality collisions structurally impossible.

    Returns `()` for an unscoped tool (`tool.resource_scope_kind == ""`) or a non-write
    tool with no resolvable keys. Returns `(_FALLBACK_WRITE_SCOPE,)` for a write tool whose
    keys did not resolve to any present, non-empty argument value (fail-closed: never an
    empty tuple and never the bare tool name for a write tool), and for a write tool whose
    composed GitHub identity is missing one of its declared keys — a partial identity such as
    `github_branch:<owner>/<repo>` from an omitted `branch` names no resource, so it fails
    closed instead of resolving a partial identity.
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
        if (
            tool.is_write
            and tool.resource_scope_kind in _GITHUB_FINE_KINDS
            and len(parts) < len(tool.resource_scope_keys)
        ):
            # A GitHub identity names a resource only when every declared key resolves.
            return (_FALLBACK_WRITE_SCOPE,)
        scopes = (
            [f"{tool.resource_scope_kind}:{separator.join(parts)}"] if parts else []
        )
    else:
        scopes = []
        for key in tool.resource_scope_keys:
            value = args.get(key)
            if not value:
                continue
            if tool.resource_scope_kind in _FILESYSTEM_LIKE_KINDS:
                normalized = str(PurePosixPath(str(value)))
            else:
                normalized = str(value)
            scopes.append(f"{tool.resource_scope_kind}:{normalized}")

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def _scopes_conflict(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). A `"github_repo:"`
    scope conflicts with a finer GitHub kind (`_GITHUB_FINE_KINDS`) when the descendant
    identity begins with the ancestor identity followed by `/`, also checked in both
    directions. Every other case (different kind prefixes, or same kind with different
    non-filesystem values) never conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    for ancestor, descendant in ((a, b), (b, a)):
        ancestor_kind, _, ancestor_identity = ancestor.partition(":")
        descendant_kind, _, descendant_identity = descendant.partition(":")
        if (
            ancestor_kind == "github_repo"
            and descendant_kind in _GITHUB_FINE_KINDS
            and descendant_identity.startswith(f"{ancestor_identity}/")
        ):
            return True

    return False


def _scope_keys_problems(
    entry: dict[str, Any], properties: dict[str, Any] | None
) -> list[str]:
    """Return the problems with *entry*'s `resource_scope_keys` declaration."""
    if "resource_scope_keys" not in entry:
        return ["resource_scope_keys is required"]
    resource_scope_keys = entry["resource_scope_keys"]
    if not isinstance(resource_scope_keys, dict) or not all(
        isinstance(key, str) and isinstance(kind, str)
        for key, kind in resource_scope_keys.items()
    ):
        return ["resource_scope_keys must be a mapping of key name to ResourceKeyKind"]
    problems = [
        f"resource_scope_key {key!r} kind {kind!r} is not in the closed value set"
        for key, kind in resource_scope_keys.items()
        if kind not in RESOURCE_KEY_KIND_VALUES
    ]
    if properties is None:
        return problems
    problems.extend(
        f"resource_scope_key {key!r} not in inputSchema.properties"
        for key in resource_scope_keys
        if key not in properties
    )
    return problems


def _scope_problems(
    entry: dict[str, Any], properties: dict[str, Any] | None
) -> list[str]:
    """Return the problems with *entry*'s resource-scope declaration."""
    problems: list[str] = []

    if "resource_scope" in entry:
        problems.append(
            "legacy singular resource_scope is not supported; "
            "use resource_scope_kind and resource_scope_keys"
        )

    if "resource_scope_kind" not in entry:
        problems.append("resource_scope_kind is required")
    elif entry["resource_scope_kind"] not in _KNOWN_SCOPE_KINDS:
        problems.append(
            f"unknown resource_scope_kind: {entry['resource_scope_kind']!r}"
        )

    problems.extend(_scope_keys_problems(entry, properties))
    return problems


def _policy_problems(entry: dict[str, Any]) -> list[str]:
    """Return the problems with *entry*'s declared policy fields."""
    problems: list[str] = []
    closed_set_fields: tuple[tuple[str, frozenset[str]], ...] = (
        ("side_effect_class", SIDE_EFFECT_CLASS_VALUES),
        ("retry_policy", RETRY_POLICY_VALUES),
        ("reconciliation_policy", RECONCILIATION_POLICY_VALUES),
        ("preview_capability", PREVIEW_CAPABILITY_VALUES),
        ("agent_safety_tier", _KNOWN_AGENT_SAFETY_TIERS),
    )
    for field, allowed in closed_set_fields:
        if field not in entry:
            problems.append(f"{field} is required")
        elif entry[field] not in allowed:
            problems.append(f"{field} must be one of {sorted(allowed)}")

    if "idempotency_required" not in entry:
        problems.append("idempotency_required is required")
    elif not isinstance(entry["idempotency_required"], bool):
        problems.append("idempotency_required must be a bool")

    if "policy_version" not in entry:
        problems.append("policy_version is required")
    elif entry["policy_version"] != TOOL_FIELD_SET_VERSION:
        problems.append(f"policy_version must be {TOOL_FIELD_SET_VERSION!r}")
    return problems


def validate_tool_schema_v2(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.1 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.

    Required fields: `is_write`, `requires_serial`, `resource_scope_kind`,
    `resource_scope_keys` (schema 2.0, unchanged), plus the declared policy fields
    `agent_safety_tier`, `side_effect_class`, `retry_policy`, `reconciliation_policy`,
    `idempotency_required`, `preview_capability` and `policy_version`. Vocabulary fields
    must carry a value from the closed value sets in `shared.tool_metadata`;
    `policy_version` must equal `TOOL_FIELD_SET_VERSION`. Empty values (`""`, `{}`) are
    valid for the scope fields. An entry carrying the legacy singular `resource_scope`
    key is rejected.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputSchema")
    properties: dict[str, Any] | None = None
    if not isinstance(input_schema, dict) or not input_schema:
        problems.append("inputSchema must be a non-empty dict")
    elif not isinstance(input_schema.get("properties"), dict):
        problems.append("inputSchema.properties must be a dict")
    else:
        properties = input_schema["properties"]

    # `bool` is a subclass of `int` in Python, so `isinstance(x, bool)` alone correctly
    # rejects plain `int`/`None`/`str` values while accepting only true booleans.
    if "is_write" not in entry:
        problems.append("is_write is required")
    elif not isinstance(entry.get("is_write"), bool):
        problems.append("is_write must be a bool")

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    problems.extend(_scope_problems(entry, properties))
    problems.extend(_policy_problems(entry))

    return problems
