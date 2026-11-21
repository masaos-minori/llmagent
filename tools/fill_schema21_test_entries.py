#!/usr/bin/env python3
"""tools/fill_schema21_test_entries.py

Agentcfg003 row 39 ripple fixer: bring the fake `/v1/tools` entry dicts in test modules
up to the schema-2.1 contract.

A dict literal is rewritten only when ALL of its schema-2.1 problems are
  - `<field> is required` for one of the seven new policy fields, and/or
  - `resource_scope_keys must be a mapping of key name to ResourceKeyKind` on a key-name
    list (the schema-2.0 shape)
Entries that are deliberately invalid (missing `is_write`, a key outside `inputSchema`,
a bad schema version, ...) are left alone, so the negative tests keep testing what they
test. Each rewritten entry is re-validated before it is written; an entry that still
fails is reported instead of patched.

Injected values mirror what a producer declares for an entry of that shape: a non-write
entry declares the read-only side of each vocabulary, a write entry the write side.
`resource_scope_keys` kinds come from the entry's `resource_scope_kind`.
`policy_version` is `shared.tool_metadata.TOOL_FIELD_SET_VERSION`.

Idempotent: a run over an already-compliant file reports zero rewrites.

Usage: uv run python tools/fill_schema21_test_entries.py <test.py> ...
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from shared.resource_scope import validate_tool_schema_v2  # noqa: E402
from shared.tool_metadata import TOOL_FIELD_SET_VERSION  # noqa: E402

NEW_FIELDS = (
    "agent_safety_tier",
    "side_effect_class",
    "retry_policy",
    "reconciliation_policy",
    "idempotency_required",
    "preview_capability",
    "policy_version",
)
_MAPPING_PROBLEM = (
    "resource_scope_keys must be a mapping of key name to ResourceKeyKind"
)

_READ_ONLY_VALUES = {
    "agent_safety_tier": "READ_ONLY",
    "side_effect_class": "read_only",
    "retry_policy": "safe_read_retry",
    "reconciliation_policy": "not_required",
    "idempotency_required": False,
    "preview_capability": "none",
}
_WRITE_VALUES = {
    "agent_safety_tier": "WRITE_SAFE",
    "side_effect_class": "local_write",
    "retry_policy": "never",
    "reconciliation_policy": "local_state",
    "idempotency_required": True,
    "preview_capability": "none",
}
# resource_scope_kind (schema 2.0 scope axis) -> ResourceKeyKind (schema 2.1 key kind)
_SCOPE_KIND_TO_KEY_KIND = {
    "filesystem": "path",
    "git_repo": "repo",
    "github_repo": "repo",
    "branch": "branch",
}


def _literal_entry(node: ast.Dict) -> dict[str, object] | None:
    """Return the dict's literal key/value mapping, or None when it is not fully literal."""
    entry: dict[str, object] = {}
    for key, value in zip(node.keys, node.values):
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            return None
        try:
            entry[key.value] = ast.literal_eval(value)
        except (ValueError, SyntaxError):
            return None
    return entry


def _upgradable_entry(node: ast.Dict) -> dict[str, object] | None:
    """Return the schema-2.1 form of the entry, or None when the entry is not a candidate."""
    entry = _literal_entry(node)
    if entry is None:
        return None
    problems = validate_tool_schema_v2(dict(entry))
    if not problems:
        return None
    allowed = {
        f"{field} is required" for field in (*NEW_FIELDS, "resource_scope_keys")
    } | {_MAPPING_PROBLEM}
    if not set(problems) <= allowed:
        return None

    updated = dict(entry)
    keys = updated.get("resource_scope_keys")
    if isinstance(keys, list):
        kind = _SCOPE_KIND_TO_KEY_KIND.get(
            str(updated.get("resource_scope_kind")), "non_escalating"
        )
        updated["resource_scope_keys"] = {str(name): kind for name in keys}
    values = dict(_WRITE_VALUES if updated.get("is_write") else _READ_ONLY_VALUES)
    values["policy_version"] = TOOL_FIELD_SET_VERSION
    for field, value in values.items():
        updated.setdefault(field, value)
    if validate_tool_schema_v2(updated):
        return None
    return updated


def _render(entry: dict[str, object], indent: int) -> str:
    """Render one entry dict as a multi-line dict literal at the given indentation."""
    inner = " " * (indent + 2)
    lines = ["{"]
    lines.extend(f"{inner}{key!r}: {value!r}," for key, value in entry.items())
    lines.append(f"{' ' * indent}}}")
    return "\n".join(lines)


def _entry_indent(text: str, node: ast.Dict, parents: dict[ast.AST, ast.AST]) -> int:
    """Indent for a re-rendered dict literal, derived from its parent container.

    The ast node offset is unreliable for multi-line expressions, and a
    previously corrupted file may already sit at column 0. When the dict is a
    value inside a dict literal, the indent is the parent's opening-brace column
    plus two; otherwise the node's own offset is used.
    """
    parent = parents.get(node)
    if isinstance(parent, ast.Dict):
        line = text.splitlines()[parent.lineno - 1]
        brace = parent.col_offset if line[parent.col_offset] == "{" else line.index("{")
        return brace + 2
    return node.col_offset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    parser.add_argument(
        "--reformat",
        action="store_true",
        help="Re-render already-compliant entry dicts too (repairs broken indentation/quotes).",
    )
    args = parser.parse_args()
    for raw in args.paths:
        path = Path(raw)
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        parents: dict[ast.AST, ast.AST] = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        rewrites: list[tuple[ast.Dict, dict[str, object]]] = []
        skipped: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Dict):
                continue
            keys = {
                k.value
                for k in node.keys
                if isinstance(k, ast.Constant) and isinstance(k.value, str)
            }
            if "name" not in keys or "inputSchema" not in keys:
                continue
            entry = _literal_entry(node)
            if entry is None:
                skipped.append(f"non-literal entry at line {node.lineno}")
                continue
            upgraded = _upgradable_entry(node)
            if upgraded is None:
                if validate_tool_schema_v2(dict(entry)):
                    skipped.append(f"line {node.lineno}: {entry.get('name')}")
                elif args.reformat:
                    rewrites.append((node, dict(entry)))
                continue
            rewrites.append((node, upgraded))
        if not rewrites:
            print(f"{path}: 0 rewrites; skipped {len(skipped)} invalid entries")
            for note in skipped:
                print(f"  left as-is: {note}")
            continue
        lines = text.splitlines()
        for node, entry in sorted(rewrites, key=lambda p: p[0].lineno, reverse=True):
            rendered = _render(entry, _entry_indent(text, node, parents))
            lines[node.lineno - 1 : node.end_lineno] = rendered.splitlines()
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"{path}: {len(rewrites)} entries rewritten; skipped {len(skipped)}")
        for note in skipped:
            print(f"  left as-is: {note}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
