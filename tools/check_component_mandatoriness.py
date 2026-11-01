#!/usr/bin/env python3
"""check_component_mandatoriness.py — Verify the three-way MCP mandatoriness consistency.

Statically verifies that the three sources of each MCP server's approved
required/non-required classification agree (ADR-004 Decision Group 3 item 13):

  1. registry <-> generated table: every registry entry's ``component_id``,
     ``classification``, and ``rationale`` equal the rendered AUTO-GENERATED
     guard-block rows in
     ``docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md``.
  2. registry <-> config: every configured ``[mcp_servers.*]`` key has a registry
     entry whose ``required`` agrees with the config value; every registry entry
     exists as a configured server (no orphan).
  3. table freshness: the classification table sits inside the AUTO-GENERATED
     guard block produced by ``tools/generate_reference_table.py``; a hand-edited
     table outside the markers is drift.

Rule: ADR-004 Decision Group 3 item 13.

Usage:
    uv run python tools/check_component_mandatoriness.py
    uv run python tools/check_component_mandatoriness.py --format json

Exit codes:
    0  No violations found
    1  Violations detected
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
import tomllib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
CONFIG_DIR = REPO_ROOT / "config"
AGENT_TOML = CONFIG_DIR / "agent.toml"
DOC_PATH = (
    REPO_ROOT / "docs" / "23_agent" / "agent_08_04_configuration-mcp-approval-obs.md"
)

# Guard markers emitted by tools/generate_reference_table.py --type mandatoriness.
GUARD_START = (
    "<!-- AUTO-GENERATED: generate_reference_table.py "
    "component-mandatoriness-reference -->"
)
GUARD_END = "<!-- END AUTO-GENERATED -->"

if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Imported so tests can monkeypatch the loader with a synthetic registry.
from shared.component_mandatoriness import (  # noqa: E402
    ComponentMandatorinessError,
    load_component_mandatoriness,
)


@dataclasses.dataclass(frozen=True)
class Violation:
    """One drift finding: which check, which component, and the detail."""

    check: str
    component_id: str
    detail: str

    def message(self) -> str:
        """Greppable ``<check>: <component_id>: <detail>`` form."""
        return f"{self.check}: {self.component_id}: {self.detail}"


def _load_registry() -> Any:
    """Load the registry; on failure return a sentinel ``None``.

    Callers turn a load failure into an "undeterminable mandatoriness" violation
    (fail-closed: the checker exits non-zero rather than skip).
    """
    try:
        return load_component_mandatoriness()
    except ComponentMandatorinessError as cause:
        sys.stderr.write(f"Undeterminable component mandatoriness: {cause}\n")
        return None


def _parse_table_rows(doc_text: str) -> list[tuple[str, str, str]]:
    """Return ``(server, classification, rationale)`` rows inside the guard block.

    Only markdown table rows between the two guard markers are read; the welcome
    line and separator row are ignored. Cells are de-backticked and stripped.
    """
    start = doc_text.find(GUARD_START)
    end = doc_text.find(GUARD_END)
    if start == -1 or end == -1 or end < start:
        return []
    block = doc_text[start:end]
    rows: list[tuple[str, str, str]] = []
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        # Skip the markdown separator row (``|---|---|---|``); data rows never
        # contain ``---`` so it must not be used as a skip predicate.
        if stripped.startswith("|---"):
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 3:
            continue
        server = cells[0].strip("`")
        classification = cells[1].strip("`")
        # Skip the header row (``Server | Classification | Rationale``).
        if classification == "Classification":
            continue
        rationale = "|".join(cells[2:]).strip()
        rows.append((server, classification, rationale))
    return rows


def _load_config_requireds() -> dict[str, bool]:
    """Return each ``[mcp_servers.*]`` key mapped to its ``required`` value.

    Defaults to ``True`` mirroring ``scripts/shared/mcp_config.py`` normalization.
    """
    with AGENT_TOML.open("rb") as handle:
        config = tomllib.load(handle)
    servers = config.get("mcp_servers", {})
    return {
        name: bool(value.get("required", True))
        for name, value in servers.items()
        if isinstance(value, dict)
    }


def check_registry_vs_table(registry: Any, doc_text: str) -> list[Violation]:
    """Check 1: registry entries equal the rendered guard-block table rows."""
    violations: list[Violation] = []
    rows = _parse_table_rows(doc_text)
    seen: set[str] = set()
    for server, classification, rationale in rows:
        seen.add(server)
        entry = registry.get(server)
        if entry is None:
            violations.append(
                Violation(
                    "registry-vs-table",
                    server,
                    "table row has no registry entry",
                )
            )
            continue
        if entry.classification != classification:
            violations.append(
                Violation(
                    "registry-vs-table",
                    server,
                    f"table classification {classification!r} != "
                    f"registry {entry.classification!r}",
                )
            )
        if entry.rationale != rationale:
            violations.append(
                Violation(
                    "registry-vs-table",
                    server,
                    "rationale mismatch with registry",
                )
            )
    for component_id in registry:
        if component_id not in seen:
            violations.append(
                Violation(
                    "registry-vs-table",
                    component_id,
                    "registry entry missing from table",
                )
            )
    return violations


def check_registry_vs_config(
    registry: Any, config_requireds: dict[str, bool]
) -> list[Violation]:
    """Check 2: config ``required`` values agree with the registry."""
    violations: list[Violation] = []
    configured = set(config_requireds)
    for component_id, required in config_requireds.items():
        entry = registry.get(component_id)
        if entry is None:
            violations.append(
                Violation(
                    "registry-vs-config",
                    component_id,
                    "configured server absent from registry (unknown)",
                )
            )
            continue
        if entry.classification == "required" and not required:
            violations.append(
                Violation(
                    "registry-vs-config",
                    component_id,
                    "required=false conflicts with registry classification 'required'",
                )
            )
    for component_id in registry:
        if component_id not in configured:
            violations.append(
                Violation(
                    "registry-vs-config",
                    component_id,
                    "registry entry has no configured server (orphan)",
                )
            )
    return violations


def check_table_freshness(doc_text: str) -> list[Violation]:
    """Check 3: the table sits inside the AUTO-GENERATED guard block."""
    if GUARD_START not in doc_text:
        return [
            Violation(
                "table-freshness",
                "(block)",
                "missing AUTO-GENERATED start marker",
            )
        ]
    if doc_text.count(GUARD_START) > 1:
        return [
            Violation(
                "table-freshness",
                "(block)",
                "duplicate AUTO-GENERATED start marker",
            )
        ]
    if GUARD_END not in doc_text:
        return [
            Violation(
                "table-freshness",
                "(block)",
                "missing END AUTO-GENERATED marker",
            )
        ]
    if _parse_table_rows(doc_text):
        return []
    return [
        Violation(
            "table-freshness",
            "(block)",
            "no classification table inside the guard block "
            "(hand-edited table outside the markers is drift)",
        )
    ]


def run_checks(
    registry: Any, doc_text: str, config_requireds: dict[str, bool]
) -> list[Violation]:
    """Run every check and return the combined violation list."""
    return (
        check_registry_vs_table(registry, doc_text)
        + check_registry_vs_config(registry, config_requireds)
        + check_table_freshness(doc_text)
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args(argv)

    registry = _load_registry()
    if registry is None:
        undetermined = Violation(
            "registry-load",
            "(registry)",
            "undeterminable component mandatoriness (fail-closed)",
        )
        _emit([undetermined], args.format)
        return 1

    doc_text = DOC_PATH.read_text(encoding="utf-8")
    config_requireds = _load_config_requireds()
    violations = run_checks(registry, doc_text, config_requireds)
    _emit(violations, args.format)
    return 1 if violations else 0


def _emit(violations: list[Violation], fmt: str) -> None:
    """Print violations in the requested format."""
    if fmt == "json":
        sys.stdout.write(
            json.dumps({"violations": [v.__dict__ for v in violations]}) + "\n"
        )
        return
    if violations:
        for v in violations:
            sys.stdout.write(v.message() + "\n")
        sys.stdout.write(f"{len(violations)} violation(s) found\n")
    else:
        sys.stdout.write("No violations found\n")


if __name__ == "__main__":
    sys.exit(main())
