#!/usr/bin/env python3
"""tools/extend_runtime_tool_test_fixtures.py

Agentcfg003 row 02 ripple fixer: extend `build_runtime_tool()` / `RuntimeTool(...)`
fixture calls in test modules to the schema-2.1 required field set.

Rewrites only fixture calls that already carry the schema-2.0 four fields
(`is_write`, `requires_serial`, `resource_scope_kind`, `resource_scope_keys`) and
omit the six new ones. Missing fields are injected with the values a producer of
that tier/shape declares:

  READ_ONLY        -> read_only / safe_read_retry / not_required / False / none
  WRITE_SAFE       -> local_write / never / local_state / True / none
  WRITE_DANGEROUS  -> external_write / reconcile_then_retry / external_state / True / none
  ADMIN            -> external_write / never / external_state / True / none
With no tier literal, `is_write=False` maps to the READ_ONLY row, True to WRITE_SAFE.
`policy_version` is `shared.tool_metadata.TOOL_FIELD_SET_VERSION`.

A bare `RuntimeTool(...)` call (positional dataclass, missing the new fields) is
rewritten to `build_runtime_tool(...)`, which is keyword-only; a tuple-shaped
`resource_scope_keys=()` becomes the empty mapping. Imports are updated: a file
whose only remaining use of the `RuntimeTool` name is the import line gets
`build_runtime_tool` imported in its place.

Idempotent: an already-compliant call reports zero rewrites.

Usage: uv run python tools/extend_runtime_tool_test_fixtures.py <test.py> ...
"""

from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from shared.tool_metadata import TOOL_FIELD_SET_VERSION  # noqa: E402

SCHEMA20_FIELDS = (
    "is_write",
    "requires_serial",
    "resource_scope_kind",
    "resource_scope_keys",
)
NEW_FIELDS = (
    "agent_safety_tier",
    "side_effect_class",
    "retry_policy",
    "reconciliation_policy",
    "idempotency_required",
    "preview_capability",
    "policy_version",
)
# tier literal -> the four vocabulary values a producer of that tier declares
_TIER_VALUES: dict[str, tuple[str, str, str, bool, str]] = {
    "READ_ONLY": ("read_only", "safe_read_retry", "not_required", False, "none"),
    "WRITE_SAFE": ("local_write", "never", "local_state", True, "none"),
    "WRITE_DANGEROUS": (
        "external_write",
        "reconcile_then_retry",
        "external_state",
        True,
        "none",
    ),
    "ADMIN": ("external_write", "never", "external_state", True, "none"),
}


def _kwarg_value(node: ast.Call, name: str) -> ast.expr | None:
    for kw in node.keywords:
        if kw.arg == name:
            return kw.value
    return None


def _fixture_call(node: ast.Call) -> bool:
    """True when the call is a fixture build of a registered tool entry."""
    func = node.func
    name = getattr(func, "id", None) or getattr(func, "attr", None)
    if name not in {"build_runtime_tool", "RuntimeTool"}:
        return False
    kwargs = {kw.arg for kw in node.keywords if kw.arg}
    return set(SCHEMA20_FIELDS) <= kwargs


def _inject(node: ast.Call) -> list[tuple[int, str]]:
    """Insert the missing schema-2.1 kwargs into the call source.

    Returns (lineno, rendered_line) pairs for line replacement; the caller applies
    them bottom-up.
    """
    present = {kw.arg for kw in node.keywords if kw.arg}
    tier_node = _kwarg_value(node, "agent_safety_tier")
    tier = tier_node.value if isinstance(tier_node, ast.Constant) else None
    values = _TIER_VALUES.get(str(tier))
    if values is None:
        write = _kwarg_value(node, "is_write")
        is_write = write.value if isinstance(write, ast.Constant) else None
        values = _TIER_VALUES["WRITE_SAFE" if is_write else "READ_ONLY"]
    side_effect, retry, reconcile, idem, preview = values
    rendered = {
        "side_effect_class": f"{side_effect!r}",
        "retry_policy": f"{retry!r}",
        "reconciliation_policy": f"{reconcile!r}",
        "idempotency_required": repr(idem),
        "preview_capability": f"{preview!r}",
        "policy_version": f"{TOOL_FIELD_SET_VERSION!r}",
    }
    if tier is None:
        rendered["agent_safety_tier"] = (
            "'WRITE_SAFE'" if values is _TIER_VALUES["WRITE_SAFE"] else "'READ_ONLY'"
        )
    # one indent deeper than the call's own first keyword line
    first_kw = min((kw for kw in node.keywords if kw.arg), key=lambda k: k.lineno)
    indent = " " * (
        first_kw.col_offset
        if first_kw.col_offset != node.col_offset
        else node.col_offset + 4
    )
    inserts: list[tuple[int, str]] = []
    anchor = max(
        (
            _kwarg_value(node, name).lineno  # type: ignore[union-attr]
            for name in NEW_FIELDS
            if name in present and _kwarg_value(node, name) is not None
        ),
        default=None,
    )
    if anchor is None:
        anchor = max(
            (
                kw.lineno
                for kw in node.keywords
                if kw.arg in {"agent_safety_tier", "resource_scope_keys"}
            ),
            default=node.lineno,
        )
    for name in NEW_FIELDS:
        if name in present:
            continue
        inserts.append((anchor, f"{indent}{name}={rendered[name]},"))
    return inserts


def _fix_scope_keys(text: str) -> int:
    """Convert tuple-shaped `resource_scope_keys=()` kwargs to the empty mapping."""
    return text.count("resource_scope_keys=(),")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    for raw in args.paths:
        path = Path(raw)
        text = path.read_text(encoding="utf-8")
        tree = ast.parse(text)
        lines = text.splitlines()
        edits: list[tuple[int, int, list[str]]] = []  # (start, end, replacement lines)
        renamed = 0
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not _fixture_call(node):
                continue
            present = {kw.arg for kw in node.keywords if kw.arg}
            missing = [name for name in NEW_FIELDS if name not in present]
            func_name = getattr(node.func, "id", None) or getattr(
                node.func, "attr", None
            )
            if not missing and func_name == "build_runtime_tool":
                continue
            segment = lines[node.lineno - 1 : node.end_lineno]
            if func_name == "RuntimeTool":
                segment[0] = segment[0].replace(
                    "RuntimeTool(", "build_runtime_tool(", 1
                )
                renamed += 1
            inserts = _inject(node)
            for lineno, line in sorted(inserts, key=lambda p: p[0], reverse=True):
                segment.insert(lineno - node.lineno + 1, line)
            edits.append((node.lineno - 1, node.end_lineno or node.lineno, segment))
        for start, end, segment in sorted(edits, key=lambda e: e[0], reverse=True):
            lines[start:end] = segment
        text = "\n".join(lines) + "\n"
        n = _fix_scope_keys(text)
        text = text.replace("resource_scope_keys=(),", "resource_scope_keys={},")
        if "build_runtime_tool(" in text and "build_runtime_tool" not in {
            alias or name
            for node in ast.walk(ast.parse(text))
            if isinstance(node, ast.ImportFrom) and node.module == "shared.runtime_tool"
            for name, alias in ((a.name, a.asname) for a in node.names)
        }:
            if "from shared.runtime_tool import " in text:
                text = text.replace(
                    "from shared.runtime_tool import ",
                    "from shared.runtime_tool import build_runtime_tool, ",
                    1,
                )
            else:
                text = text.replace(
                    "from shared.runtime_tool_registry import ",
                    "from shared.runtime_tool import build_runtime_tool\n"
                    "from shared.runtime_tool_registry import ",
                    1,
                )
        if renamed and "RuntimeTool" not in text.replace(
            "from shared.runtime_tool import RuntimeTool\n", ""
        ).replace("build_runtime_tool", "").replace("RuntimeToolRegistry", ""):
            text = text.replace(
                "from shared.runtime_tool import RuntimeTool\n",
                "from shared.runtime_tool import build_runtime_tool\n",
            )
        path.write_text(text, encoding="utf-8")
        print(
            f"{path}: {len(edits)} calls extended ({renamed} RuntimeTool->build_runtime_tool), {n} tuple scope-keys converted"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
