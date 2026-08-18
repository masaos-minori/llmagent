#!/usr/bin/env python3
"""scripts/shared/resource_scope.py

Resource-scope resolution and schema-2.0 contract validation.

`resolve_resource_scopes()` turns a `RuntimeTool`'s declared
`resource_scope_kind`/`resource_scope_keys` plus a call's actual arguments into a tuple of
kind-prefixed scope strings. `_scopes_conflict()` is the overlap predicate consumed later
by `scripts/agent/tool_scheduler.py`'s conflict-graph grouping (not wired up yet).
`validate_tool_schema_v2()` validates a raw MCP tool-list entry against the schema-2.0
contract.

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
from typing import Any

from shared.runtime_tool import RuntimeTool

# Known `resource_scope_kind` vocabulary, per the plan's Design section scope-string
# examples and the Affected-areas table's per-server kind assignments. `""` denotes an
# unscoped tool (no conflict-graph entry needed).
_KNOWN_SCOPE_KINDS = frozenset(
    {
        "",
        "filesystem",
        "git_repo",
        "github_repo",
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
    "cicd_workflow": ":",
}


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_x_resolve_resource_scopes__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_resolve_resource_scopes__mutmut)
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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


def x_resolve_resource_scopes__mutmut_orig(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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


def x_resolve_resource_scopes__mutmut_1(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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


def x_resolve_resource_scopes__mutmut_2(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = None
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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


def x_resolve_resource_scopes__mutmut_3(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(None)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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


def x_resolve_resource_scopes__mutmut_4(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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


def x_resolve_resource_scopes__mutmut_5(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = None
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


def x_resolve_resource_scopes__mutmut_6(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(None) for key in tool.resource_scope_keys if args.get(key)]
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


def x_resolve_resource_scopes__mutmut_7(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(None)]
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


def x_resolve_resource_scopes__mutmut_8(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
        scopes = None
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


def x_resolve_resource_scopes__mutmut_9(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
        scopes = (
            [f"{tool.resource_scope_kind}:{separator.join(None)}"] if parts else []
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


def x_resolve_resource_scopes__mutmut_10(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
        scopes = (
            [f"{tool.resource_scope_kind}:{separator.join(parts)}"] if parts else []
        )
    else:
        scopes = None
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


def x_resolve_resource_scopes__mutmut_11(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
        scopes = (
            [f"{tool.resource_scope_kind}:{separator.join(parts)}"] if parts else []
        )
    else:
        scopes = []
        for key in tool.resource_scope_keys:
            value = None
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


def x_resolve_resource_scopes__mutmut_12(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
        scopes = (
            [f"{tool.resource_scope_kind}:{separator.join(parts)}"] if parts else []
        )
    else:
        scopes = []
        for key in tool.resource_scope_keys:
            value = args.get(None)
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


def x_resolve_resource_scopes__mutmut_13(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
        scopes = (
            [f"{tool.resource_scope_kind}:{separator.join(parts)}"] if parts else []
        )
    else:
        scopes = []
        for key in tool.resource_scope_keys:
            value = args.get(key)
            if value:
                continue
            if tool.resource_scope_kind in _FILESYSTEM_LIKE_KINDS:
                normalized = str(PurePosixPath(str(value)))
            else:
                normalized = str(value)
            scopes.append(f"{tool.resource_scope_kind}:{normalized}")

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_14(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
        scopes = (
            [f"{tool.resource_scope_kind}:{separator.join(parts)}"] if parts else []
        )
    else:
        scopes = []
        for key in tool.resource_scope_keys:
            value = args.get(key)
            if not value:
                break
            if tool.resource_scope_kind in _FILESYSTEM_LIKE_KINDS:
                normalized = str(PurePosixPath(str(value)))
            else:
                normalized = str(value)
            scopes.append(f"{tool.resource_scope_kind}:{normalized}")

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_15(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
        scopes = (
            [f"{tool.resource_scope_kind}:{separator.join(parts)}"] if parts else []
        )
    else:
        scopes = []
        for key in tool.resource_scope_keys:
            value = args.get(key)
            if not value:
                continue
            if tool.resource_scope_kind not in _FILESYSTEM_LIKE_KINDS:
                normalized = str(PurePosixPath(str(value)))
            else:
                normalized = str(value)
            scopes.append(f"{tool.resource_scope_kind}:{normalized}")

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_16(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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
                normalized = None
            else:
                normalized = str(value)
            scopes.append(f"{tool.resource_scope_kind}:{normalized}")

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_17(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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
                normalized = str(None)
            else:
                normalized = str(value)
            scopes.append(f"{tool.resource_scope_kind}:{normalized}")

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_18(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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
                normalized = str(PurePosixPath(None))
            else:
                normalized = str(value)
            scopes.append(f"{tool.resource_scope_kind}:{normalized}")

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_19(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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
                normalized = str(PurePosixPath(str(None)))
            else:
                normalized = str(value)
            scopes.append(f"{tool.resource_scope_kind}:{normalized}")

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_20(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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
                normalized = None
            scopes.append(f"{tool.resource_scope_kind}:{normalized}")

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_21(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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
                normalized = str(None)
            scopes.append(f"{tool.resource_scope_kind}:{normalized}")

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_22(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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
            scopes.append(None)

    if not scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_23(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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

    if not scopes or tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_24(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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

    if scopes and tool.is_write:
        return (_FALLBACK_WRITE_SCOPE,)
    return tuple(scopes)


def x_resolve_resource_scopes__mutmut_25(
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
    empty tuple and never the bare tool name for a write tool).
    """
    if not tool.resource_scope_kind:
        return ()

    separator = _COMPOSED_KIND_SEPARATORS.get(tool.resource_scope_kind)
    if separator is not None:
        parts = [str(args[key]) for key in tool.resource_scope_keys if args.get(key)]
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
    return tuple(None)

mutants_x_resolve_resource_scopes__mutmut['_mutmut_orig'] = x_resolve_resource_scopes__mutmut_orig # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_1'] = x_resolve_resource_scopes__mutmut_1 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_2'] = x_resolve_resource_scopes__mutmut_2 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_3'] = x_resolve_resource_scopes__mutmut_3 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_4'] = x_resolve_resource_scopes__mutmut_4 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_5'] = x_resolve_resource_scopes__mutmut_5 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_6'] = x_resolve_resource_scopes__mutmut_6 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_7'] = x_resolve_resource_scopes__mutmut_7 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_8'] = x_resolve_resource_scopes__mutmut_8 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_9'] = x_resolve_resource_scopes__mutmut_9 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_10'] = x_resolve_resource_scopes__mutmut_10 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_11'] = x_resolve_resource_scopes__mutmut_11 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_12'] = x_resolve_resource_scopes__mutmut_12 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_13'] = x_resolve_resource_scopes__mutmut_13 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_14'] = x_resolve_resource_scopes__mutmut_14 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_15'] = x_resolve_resource_scopes__mutmut_15 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_16'] = x_resolve_resource_scopes__mutmut_16 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_17'] = x_resolve_resource_scopes__mutmut_17 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_18'] = x_resolve_resource_scopes__mutmut_18 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_19'] = x_resolve_resource_scopes__mutmut_19 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_20'] = x_resolve_resource_scopes__mutmut_20 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_21'] = x_resolve_resource_scopes__mutmut_21 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_22'] = x_resolve_resource_scopes__mutmut_22 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_23'] = x_resolve_resource_scopes__mutmut_23 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_24'] = x_resolve_resource_scopes__mutmut_24 # type: ignore # mutmut generated
mutants_x_resolve_resource_scopes__mutmut['x_resolve_resource_scopes__mutmut_25'] = x_resolve_resource_scopes__mutmut_25 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x__scopes_conflict__mutmut)
def _scopes_conflict(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_orig(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_1(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a != b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_2(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return False

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_3(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = None
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_4(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "XXfilesystem:XX"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_5(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "FILESYSTEM:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_6(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) or b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_7(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(None) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_8(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(None):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_9(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = None
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_10(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(None)
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_11(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = None
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_12(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(None)
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_13(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) and path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_14(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(None) or path_b.is_relative_to(path_a)

    return False


def x__scopes_conflict__mutmut_15(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(None)

    return False


def x__scopes_conflict__mutmut_16(a: str, b: str) -> bool:
    """Return True if scope strings *a* and *b* denote overlapping resources.

    Exact-equal scope strings always conflict. `"filesystem:"`-prefixed scopes also
    conflict when one path is an ancestor/descendant of the other (via
    `PurePosixPath.is_relative_to()`, checked in both directions). Every other case
    (different kind prefixes, or same kind with different non-filesystem values) never
    conflicts.
    """
    if a == b:
        return True

    filesystem_prefix = "filesystem:"
    if a.startswith(filesystem_prefix) and b.startswith(filesystem_prefix):
        path_a = PurePosixPath(a[len(filesystem_prefix) :])
        path_b = PurePosixPath(b[len(filesystem_prefix) :])
        return path_a.is_relative_to(path_b) or path_b.is_relative_to(path_a)

    return True

mutants_x__scopes_conflict__mutmut['_mutmut_orig'] = x__scopes_conflict__mutmut_orig # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_1'] = x__scopes_conflict__mutmut_1 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_2'] = x__scopes_conflict__mutmut_2 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_3'] = x__scopes_conflict__mutmut_3 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_4'] = x__scopes_conflict__mutmut_4 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_5'] = x__scopes_conflict__mutmut_5 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_6'] = x__scopes_conflict__mutmut_6 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_7'] = x__scopes_conflict__mutmut_7 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_8'] = x__scopes_conflict__mutmut_8 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_9'] = x__scopes_conflict__mutmut_9 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_10'] = x__scopes_conflict__mutmut_10 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_11'] = x__scopes_conflict__mutmut_11 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_12'] = x__scopes_conflict__mutmut_12 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_13'] = x__scopes_conflict__mutmut_13 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_14'] = x__scopes_conflict__mutmut_14 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_15'] = x__scopes_conflict__mutmut_15 # type: ignore # mutmut generated
mutants_x__scopes_conflict__mutmut['x__scopes_conflict__mutmut_16'] = x__scopes_conflict__mutmut_16 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut: MutantDict = {}  # type: ignore


@_mutmut_mutated(mutants_x_validate_tool_schema_v2__mutmut)
def validate_tool_schema_v2(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_orig(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_1(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = None

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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_2(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = None
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_3(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get(None)
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_4(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("XXnameXX")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_5(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("NAME")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_6(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) and not name:
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_7(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if isinstance(name, str) or not name:
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_8(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or name:
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_9(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append(None)

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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_10(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("XXname must be a non-empty stringXX")

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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_11(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("NAME MUST BE A NON-EMPTY STRING")

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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_12(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = None
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_13(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get(None)
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_14(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("XXinputSchemaXX")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_15(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputschema")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_16(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("INPUTSCHEMA")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_17(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputSchema")
    properties: dict[str, Any] | None = ""
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_18(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputSchema")
    properties: dict[str, Any] | None = None
    if not isinstance(input_schema, dict) and not input_schema:
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_19(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputSchema")
    properties: dict[str, Any] | None = None
    if isinstance(input_schema, dict) or not input_schema:
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_20(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputSchema")
    properties: dict[str, Any] | None = None
    if not isinstance(input_schema, dict) or input_schema:
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_21(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputSchema")
    properties: dict[str, Any] | None = None
    if not isinstance(input_schema, dict) or not input_schema:
        problems.append(None)
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_22(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputSchema")
    properties: dict[str, Any] | None = None
    if not isinstance(input_schema, dict) or not input_schema:
        problems.append("XXinputSchema must be a non-empty dictXX")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_23(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputSchema")
    properties: dict[str, Any] | None = None
    if not isinstance(input_schema, dict) or not input_schema:
        problems.append("inputschema must be a non-empty dict")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_24(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputSchema")
    properties: dict[str, Any] | None = None
    if not isinstance(input_schema, dict) or not input_schema:
        problems.append("INPUTSCHEMA MUST BE A NON-EMPTY DICT")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_25(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
    """
    problems: list[str] = []

    name = entry.get("name")
    if not isinstance(name, str) or not name:
        problems.append("name must be a non-empty string")

    input_schema = entry.get("inputSchema")
    properties: dict[str, Any] | None = None
    if not isinstance(input_schema, dict) or not input_schema:
        problems.append("inputSchema must be a non-empty dict")
    elif isinstance(input_schema.get("properties"), dict):
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_26(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append(None)
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_27(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("XXinputSchema.properties must be a dictXX")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_28(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("inputschema.properties must be a dict")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_29(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("INPUTSCHEMA.PROPERTIES MUST BE A DICT")
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_30(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        properties = None

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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_31(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        properties = input_schema["XXpropertiesXX"]

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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_32(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        properties = input_schema["PROPERTIES"]

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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_33(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
    if "XXis_writeXX" not in entry:
        problems.append("is_write is required")
    elif not isinstance(entry.get("is_write"), bool):
        problems.append("is_write must be a bool")

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_34(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
    if "IS_WRITE" not in entry:
        problems.append("is_write is required")
    elif not isinstance(entry.get("is_write"), bool):
        problems.append("is_write must be a bool")

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_35(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
    if "is_write" in entry:
        problems.append("is_write is required")
    elif not isinstance(entry.get("is_write"), bool):
        problems.append("is_write must be a bool")

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_36(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append(None)
    elif not isinstance(entry.get("is_write"), bool):
        problems.append("is_write must be a bool")

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_37(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("XXis_write is requiredXX")
    elif not isinstance(entry.get("is_write"), bool):
        problems.append("is_write must be a bool")

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_38(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("IS_WRITE IS REQUIRED")
    elif not isinstance(entry.get("is_write"), bool):
        problems.append("is_write must be a bool")

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_39(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
    elif isinstance(entry.get("is_write"), bool):
        problems.append("is_write must be a bool")

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_40(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append(None)

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_41(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("XXis_write must be a boolXX")

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_42(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("IS_WRITE MUST BE A BOOL")

    if "requires_serial" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_43(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    if "XXrequires_serialXX" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_44(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    if "REQUIRES_SERIAL" not in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_45(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    if "requires_serial" in entry:
        problems.append("requires_serial is required")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_46(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append(None)
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_47(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("XXrequires_serial is requiredXX")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_48(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("REQUIRES_SERIAL IS REQUIRED")
    elif not isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_49(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
    elif isinstance(entry.get("requires_serial"), bool):
        problems.append("requires_serial must be a bool")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_50(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append(None)

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_51(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("XXrequires_serial must be a boolXX")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_52(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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
        problems.append("REQUIRES_SERIAL MUST BE A BOOL")

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_53(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = None
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_54(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get(None, "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_55(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", None)
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_56(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_57(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", )
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_58(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("XXresource_scope_kindXX", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_59(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("RESOURCE_SCOPE_KIND", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_60(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "XXXX")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_61(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_62(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(None)

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_63(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = None
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_64(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get(None, [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_65(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", None)
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_66(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get([])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_67(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", )
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_68(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("XXresource_scope_keysXX", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_69(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("RESOURCE_SCOPE_KEYS", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_70(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) and not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_71(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_72(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_73(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        None
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_74(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append(None)
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_75(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("XXresource_scope_keys must be a list[str]XX")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_76(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("RESOURCE_SCOPE_KEYS MUST BE A LIST[STR]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_77(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_78(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key in properties:
                problems.append(
                    f"resource_scope_key {key!r} not in inputSchema.properties"
                )

    return problems


def x_validate_tool_schema_v2__mutmut_79(entry: dict[str, Any]) -> list[str]:
    """Validate a raw MCP tool-list *entry* against the schema-2.0 contract.

    Returns a list of human-readable problem strings; an empty list means the entry is
    valid. Never coerces or defaults a missing/mistyped field — this is the last line of
    defense before an incomplete or malformed tool declaration reaches the registry, so it
    must reject rather than silently accept.
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

    resource_scope_kind = entry.get("resource_scope_kind", "")
    if resource_scope_kind not in _KNOWN_SCOPE_KINDS:
        problems.append(f"unknown resource_scope_kind: {resource_scope_kind!r}")

    resource_scope_keys = entry.get("resource_scope_keys", [])
    if not isinstance(resource_scope_keys, list) or not all(
        isinstance(key, str) for key in resource_scope_keys
    ):
        problems.append("resource_scope_keys must be a list[str]")
    elif properties is not None:
        for key in resource_scope_keys:
            if key not in properties:
                problems.append(
                    None
                )

    return problems

mutants_x_validate_tool_schema_v2__mutmut['_mutmut_orig'] = x_validate_tool_schema_v2__mutmut_orig # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_1'] = x_validate_tool_schema_v2__mutmut_1 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_2'] = x_validate_tool_schema_v2__mutmut_2 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_3'] = x_validate_tool_schema_v2__mutmut_3 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_4'] = x_validate_tool_schema_v2__mutmut_4 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_5'] = x_validate_tool_schema_v2__mutmut_5 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_6'] = x_validate_tool_schema_v2__mutmut_6 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_7'] = x_validate_tool_schema_v2__mutmut_7 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_8'] = x_validate_tool_schema_v2__mutmut_8 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_9'] = x_validate_tool_schema_v2__mutmut_9 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_10'] = x_validate_tool_schema_v2__mutmut_10 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_11'] = x_validate_tool_schema_v2__mutmut_11 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_12'] = x_validate_tool_schema_v2__mutmut_12 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_13'] = x_validate_tool_schema_v2__mutmut_13 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_14'] = x_validate_tool_schema_v2__mutmut_14 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_15'] = x_validate_tool_schema_v2__mutmut_15 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_16'] = x_validate_tool_schema_v2__mutmut_16 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_17'] = x_validate_tool_schema_v2__mutmut_17 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_18'] = x_validate_tool_schema_v2__mutmut_18 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_19'] = x_validate_tool_schema_v2__mutmut_19 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_20'] = x_validate_tool_schema_v2__mutmut_20 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_21'] = x_validate_tool_schema_v2__mutmut_21 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_22'] = x_validate_tool_schema_v2__mutmut_22 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_23'] = x_validate_tool_schema_v2__mutmut_23 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_24'] = x_validate_tool_schema_v2__mutmut_24 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_25'] = x_validate_tool_schema_v2__mutmut_25 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_26'] = x_validate_tool_schema_v2__mutmut_26 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_27'] = x_validate_tool_schema_v2__mutmut_27 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_28'] = x_validate_tool_schema_v2__mutmut_28 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_29'] = x_validate_tool_schema_v2__mutmut_29 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_30'] = x_validate_tool_schema_v2__mutmut_30 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_31'] = x_validate_tool_schema_v2__mutmut_31 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_32'] = x_validate_tool_schema_v2__mutmut_32 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_33'] = x_validate_tool_schema_v2__mutmut_33 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_34'] = x_validate_tool_schema_v2__mutmut_34 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_35'] = x_validate_tool_schema_v2__mutmut_35 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_36'] = x_validate_tool_schema_v2__mutmut_36 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_37'] = x_validate_tool_schema_v2__mutmut_37 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_38'] = x_validate_tool_schema_v2__mutmut_38 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_39'] = x_validate_tool_schema_v2__mutmut_39 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_40'] = x_validate_tool_schema_v2__mutmut_40 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_41'] = x_validate_tool_schema_v2__mutmut_41 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_42'] = x_validate_tool_schema_v2__mutmut_42 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_43'] = x_validate_tool_schema_v2__mutmut_43 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_44'] = x_validate_tool_schema_v2__mutmut_44 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_45'] = x_validate_tool_schema_v2__mutmut_45 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_46'] = x_validate_tool_schema_v2__mutmut_46 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_47'] = x_validate_tool_schema_v2__mutmut_47 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_48'] = x_validate_tool_schema_v2__mutmut_48 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_49'] = x_validate_tool_schema_v2__mutmut_49 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_50'] = x_validate_tool_schema_v2__mutmut_50 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_51'] = x_validate_tool_schema_v2__mutmut_51 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_52'] = x_validate_tool_schema_v2__mutmut_52 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_53'] = x_validate_tool_schema_v2__mutmut_53 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_54'] = x_validate_tool_schema_v2__mutmut_54 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_55'] = x_validate_tool_schema_v2__mutmut_55 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_56'] = x_validate_tool_schema_v2__mutmut_56 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_57'] = x_validate_tool_schema_v2__mutmut_57 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_58'] = x_validate_tool_schema_v2__mutmut_58 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_59'] = x_validate_tool_schema_v2__mutmut_59 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_60'] = x_validate_tool_schema_v2__mutmut_60 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_61'] = x_validate_tool_schema_v2__mutmut_61 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_62'] = x_validate_tool_schema_v2__mutmut_62 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_63'] = x_validate_tool_schema_v2__mutmut_63 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_64'] = x_validate_tool_schema_v2__mutmut_64 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_65'] = x_validate_tool_schema_v2__mutmut_65 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_66'] = x_validate_tool_schema_v2__mutmut_66 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_67'] = x_validate_tool_schema_v2__mutmut_67 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_68'] = x_validate_tool_schema_v2__mutmut_68 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_69'] = x_validate_tool_schema_v2__mutmut_69 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_70'] = x_validate_tool_schema_v2__mutmut_70 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_71'] = x_validate_tool_schema_v2__mutmut_71 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_72'] = x_validate_tool_schema_v2__mutmut_72 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_73'] = x_validate_tool_schema_v2__mutmut_73 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_74'] = x_validate_tool_schema_v2__mutmut_74 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_75'] = x_validate_tool_schema_v2__mutmut_75 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_76'] = x_validate_tool_schema_v2__mutmut_76 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_77'] = x_validate_tool_schema_v2__mutmut_77 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_78'] = x_validate_tool_schema_v2__mutmut_78 # type: ignore # mutmut generated
mutants_x_validate_tool_schema_v2__mutmut['x_validate_tool_schema_v2__mutmut_79'] = x_validate_tool_schema_v2__mutmut_79 # type: ignore # mutmut generated
