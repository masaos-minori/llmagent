#!/usr/bin/env python3
"""tools/apply_producer_policy_fields.py

One-shot migration (agentcfg003 rows 09-21): insert the schema-2.1 declared policy
fields into every MCP producer ``TOOL_LIST`` entry and convert the
``resource_scope_keys`` key list to the key-to-``ResourceKeyKind`` mapping.

Declared values are the values each module already encodes, read from the
reference data so the migration cannot drift:

- ``agent_safety_tier``   : mirrored from ``config/agent.toml [tool_safety_tiers]``
- ``side_effect_class``   : from ``shared.tool_constants`` write-set membership
- ``retry_policy``        : ``same_logical_call_only`` for members of
  ``RETRYABLE_TOOLS``, ``safe_read_retry`` for read-only tools, else ``never``
- ``reconciliation_policy`` : derived from ``side_effect_class``
- ``idempotency_required``  : True for side-effecting tools
- ``preview_capability``  : ``dry_run`` for tools whose own interface accepts a
  dry_run parameter (inputSchema property or pydantic model field), else ``none``
- ``policy_version``      : ``shared.tool_metadata.TOOL_FIELD_SET_VERSION``

Modules with a shared metadata head (the 4 github modules) get ``policy_version``
in the shared head TypedDict; the fields that vary per entry are inserted inline.
Idempotent: entries that already declare ``agent_safety_tier`` are left alone.

Usage: uv run python tools/apply_producer_policy_fields.py <producer.py> ...
"""

from __future__ import annotations

import argparse
import re
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "scripts"))

from _atomic_write import (  # noqa: E402
    add_dry_run_argument,
    atomic_write_text,
    print_dry_run,
)
from shared import tool_constants  # noqa: E402
from shared.tool_metadata import RESOURCE_KEY_KIND_VALUES  # noqa: E402

# Wire keys used by the 13 producer modules and their declared escalation kind.
# Keys no escalation rule reads take ``non_escalating`` (procedure rows 10-21).
KEY_KIND: dict[str, str] = {
    "path": "path",
    "paths": "path",
    "repo_path": "path",
    "ref": "branch",
    "repo": "repo",
    "owner": "non_escalating",
    "run_id": "non_escalating",
    "workflow": "non_escalating",
    # move_file source/destination are filesystem paths (verified 2026-11-21 in
    # the move_file inputSchema); they stay jail-checked, so they take path kind.
    "source": "path",
    "destination": "path",
}

assert set(KEY_KIND.values()) <= RESOURCE_KEY_KIND_VALUES

# Tools whose own interface accepts a dry_run parameter (verified 2026-11-21:
# inputSchema dry_run property in the file/git/shell producers; pydantic dry_run
# field in the github_models_* write request models).
DRY_RUN_CAPABLE: frozenset[str] = frozenset(
    {
        "write_file",
        "edit_file",
        "create_directory",
        "move_file",
        "delete_file",
        "delete_directory",
        "git_add",
        "git_commit",
        "git_checkout",
        "git_pull",
        "git_push",
        "shell_run",
        "github_create_branch",
        "github_create_or_update_file",
        "github_push_files",
        "github_delete_file",
        "github_create_issue",
        "github_add_issue_comment",
        "github_create_pull_request",
        "github_update_pull_request",
        "github_merge_pull_request",
    }
)

EXTERNAL_WRITE: frozenset[str] = (
    tool_constants.GITHUB_WRITE_TOOLS
    | tool_constants.GITHUB_DANGEROUS_TOOLS
    | tool_constants.CICD_WRITE_TOOLS
)
LOCAL_WRITE: frozenset[str] = (
    tool_constants.WRITE_TOOLS
    | tool_constants.DELETE_TOOLS
    | tool_constants.GIT_WRITE_TOOLS
    | tool_constants.MDQ_WRITE_TOOLS
    | tool_constants.RAG_WRITE_TOOLS
    | tool_constants.SHELL_TOOLS
)

TIERS: dict[str, str] = tomllib.loads((REPO / "config" / "agent.toml").read_text())[
    "tool_safety_tiers"
]

NAME_RE = re.compile(r'^\s*"name": "([a-z0-9_]+)",')
SCOPE_KEYS_RE = re.compile(r'^(\s*)"resource_scope_keys": \[([^\]]*)\],\s*$')
HEAD_CLASS_RE = re.compile(r"^class _\w+Head\(TypedDict\):", re.M)


def _policy(name: str) -> list[tuple[str, str]]:
    """Return (field, emitted-value-literal) pairs for one tool entry."""
    if name not in TIERS:
        raise SystemExit(f"2 usage error: no tier declared for tool {name!r}")
    if name in EXTERNAL_WRITE:
        side_effect = "external_write"
    elif name in LOCAL_WRITE:
        side_effect = "local_write"
    else:
        side_effect = "read_only"
    if name in tool_constants.RETRYABLE_TOOLS:
        retry = "same_logical_call_only"
    elif side_effect == "read_only":
        retry = "safe_read_retry"
    else:
        retry = "never"
    reconciliation = {
        "read_only": "not_required",
        "local_write": "local_state",
        "external_write": "external_state",
    }[side_effect]
    return [
        ("agent_safety_tier", f'"{TIERS[name]}"'),
        ("side_effect_class", f'"{side_effect}"'),
        ("retry_policy", f'"{retry}"'),
        ("reconciliation_policy", f'"{reconciliation}"'),
        ("idempotency_required", "True" if side_effect != "read_only" else "False"),
        ("preview_capability", f'"{"dry_run" if name in DRY_RUN_CAPABLE else "none"}"'),
    ]


def _entry_has_policy(lines: list[str], start: int) -> bool:
    for line in lines[start + 1 :]:
        if NAME_RE.match(line):
            return False
        if "agent_safety_tier" in line:
            return True
    return False


def _transform(path: Path) -> str:
    original = path.read_text()
    has_head = bool(HEAD_CLASS_RE.search(original))
    lines = original.splitlines(keepends=True)
    current: str | None = None
    out: list[str] = []
    for i, line in enumerate(lines):
        m = NAME_RE.match(line)
        if m:
            current = m.group(1)
        sk = SCOPE_KEYS_RE.match(line)
        if sk:
            indent, items = sk.group(1), sk.group(2)
            keys = [k.strip().strip('"') for k in items.split(",") if k.strip()]
            missing = [k for k in keys if k not in KEY_KIND]
            if missing:
                raise SystemExit(
                    f"2 usage error: unmapped scope keys {missing} in {path}"
                )
            inner = ", ".join(f'"{k}": "{KEY_KIND[k]}"' for k in keys)
            out.append(f'{indent}"resource_scope_keys": {{{inner}}},\n')
            continue
        out.append(line)
        if '"is_write":' in line:
            if current is None or _entry_has_policy(lines, i):
                continue
            for field, value in _policy(current):
                out.append(f'        "{field}": {value},\n')
            if not has_head:
                out.append('        "policy_version": TOOL_FIELD_SET_VERSION,\n')
    text = "".join(out)

    if has_head:
        # policy_version moves into the shared head TypedDict and its literal;
        # the scope-tail key lists become the key-to-kind mapping type.
        text = re.sub(
            r'(class _\w+Head\(TypedDict\):\n    """[^"]*"""\n\n)',
            r"\1    policy_version: str\n",
            text,
            count=1,
        )
        text = re.sub(
            r'(_\w+HEAD: _\w+Head = \{\n(?:\s*"[a-z_]+": [^\n]*\n)*?)(\}\n)',
            r'\1    "policy_version": TOOL_FIELD_SET_VERSION,\n\2',
            text,
            count=1,
        )
        text = text.replace(
            "    resource_scope_keys: list[str]",
            "    resource_scope_keys: Mapping[str, ResourceKeyKind]",
        )

    if "import TOOL_FIELD_SET_VERSION" not in text:
        text_lines = text.splitlines(keepends=True)
        last_import = max(
            i for i, ln in enumerate(text_lines) if ln.startswith(("from ", "import "))
        )
        imports = ["from shared.tool_metadata import TOOL_FIELD_SET_VERSION\n"]
        if has_head:
            imports = [
                "from shared.tool_metadata import ResourceKeyKind, TOOL_FIELD_SET_VERSION\n",
            ]
            text = text.replace(
                "from typing import TypedDict",
                "from collections.abc import Mapping\nfrom typing import TypedDict",
                1,
            )
            text_lines = text.splitlines(keepends=True)
            last_import = max(
                i
                for i, ln in enumerate(text_lines)
                if ln.startswith(("from ", "import "))
            )
        text_lines.insert(last_import + 1, "\n" + imports[0])
        text = "".join(text_lines)

    return text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="apply_producer_policy_fields.py",
        description="Insert schema-2.1 policy fields into MCP producer TOOL_LIST entries",
    )
    parser.add_argument(
        "files", nargs="+", help="producer modules under scripts/mcp_servers/"
    )
    add_dry_run_argument(parser)
    ns = parser.parse_args(sys.argv[1:] if argv is None else argv)
    for arg in ns.files:
        path = Path(arg)
        old = path.read_text()
        new = _transform(path)
        if ns.dry_run:
            print_dry_run(path, old, new)
        else:
            atomic_write_text(path, new)
            print(f"updated {arg}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
