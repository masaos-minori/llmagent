#!/usr/bin/env python3
"""_agent_config_migration.py — Agent-config migration table (agentcfg006 REQ-002).

Private module for tools/generate_reference_table.py: reads the single-source
`_REMOVED_KEY_REPLACEMENTS` mapping in `scripts/agent/production_config_validator.py`
and renders the `agent_config_migration` domain's manifest entries and guarded table.

The mapping is read as source text with `ast`, not imported, so this module does not
depend on `scripts/` being importable at run time, and the generated table reads the
same literal the fatal unknown-key error reads, so the two cannot diverge. The module
holds only the mapping read and the table render; the domain registration stays in the
tool, whose size is at its recorded baseline.

Usage (through the tool):
    python tools/generate_reference_table.py --type agent_config_migration
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

from tools._contract_manifests import ManifestError, escape_table_cell

MAPPING_NAME = "_REMOVED_KEY_REPLACEMENTS"


def read_mapping(source: Path) -> dict[str, str]:
    """Return the module-level `MAPPING_NAME` dict literal as {removed key: replacement}.

    Fail closed: an unreadable or unparseable source, a missing assignment, a
    non-dict literal, a non-string key or value, or a duplicate key raises
    ManifestError, so no partial or guessed row is emitted.
    """
    try:
        tree = ast.parse(source.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        raise ManifestError(f"cannot parse {source.name}: {exc}") from exc
    mapping: dict[str, str] = {}
    for node in tree.body:
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            if node.value is None:
                continue
            targets = [node.target]
            value = node.value
        else:
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == MAPPING_NAME
            for target in targets
        ):
            continue
        if not isinstance(value, ast.Dict):
            raise ManifestError(f"{source.name}: {MAPPING_NAME} is not a dict literal")
        for key, val in zip(value.keys, value.values):
            if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
                raise ManifestError(f"{source.name}: non-string key in {MAPPING_NAME}")
            if not isinstance(val, ast.Constant) or not isinstance(val.value, str):
                raise ManifestError(
                    f"{source.name}: non-string replacement for key {key.value}"
                )
            if key.value in mapping:
                raise ManifestError(f"duplicate key in {MAPPING_NAME}: {key.value}")
            mapping[key.value] = val.value
    if not mapping:
        raise ManifestError(
            f"{MAPPING_NAME} assignment not found in {source.name} — "
            "regenerate against the new structure"
        )
    return mapping


def mapping_entries(source: Path) -> list[dict[str, Any]]:
    """Return the `{key, replacement}` manifest entries, sorted by natural key."""
    mapping = read_mapping(source)
    return [{"key": key, "replacement": mapping[key]} for key in sorted(mapping)]


def render_migration_table(entries: list[dict[str, Any]]) -> str:
    """Render the `| Removed key | Replacement |` table from manifest entries.

    Entry order follows the sorted manifest, which is the byte-stable committed
    artifact, so the block matches the manifest-vs-source drift check. Pipe
    characters in cell text are escaped.
    """
    lines = [
        "| Removed key (`config/agent.toml`) | Replacement (single source) |",
        "|---|---|",
    ]
    for entry in entries:
        key = escape_table_cell(str(entry["key"]))
        replacement = escape_table_cell(str(entry["replacement"]))
        lines.append(f"| `{key}` | {replacement} |")
    return "\n".join(lines)
