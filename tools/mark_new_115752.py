#!/usr/bin/env python3
"""mark_new_115752.py — Idempotent `(new)` marker application for the mcpgate001 batch.

Adds " (new)" after every backticked symbol occurrence listed in EDITS unless the
occurrence already carries the marker. Reproducible record of the marker edits made
during procedure generation for plan 20261030-001153_mcpgate001 (stale_detector
symbol_missing fixes).

Usage: uv run python tools/mark_new_115752.py
Exit codes: 0 applied/no-op, 1 a listed file or symbol was not found.
"""

from __future__ import annotations

import re
import sys

EDITS: dict[str, list[str]] = {
    "implementations/20261030-115752_01_registry_component_mandatoriness.yaml.md": [
        "component_id",
        "non_required",
        "failure_category",
        "safety_role",
        "safely_disableable_functions",
        "startup_consequence",
        "abort_startup",
        "authority_adr",
    ],
    "implementations/20261030-115752_02_scripts_shared_component_mandatoriness.py.md": [
        "ComponentMandatorinessError",
        "component_id",
        "UnknownComponentError",
        "ClassificationConflictError",
        "non_required",
        "safely_disableable_functions",
    ],
    "implementations/20261030-115752_04_scripts_agent_production_config_validator.py.md": [
        "load_component_mandatoriness",
        "get_classification",
        "check_required_agreement",
        "component_mandatoriness",
        "ClassificationConflictError",
        "UnknownComponentError",
        "validate_against_registry",
    ],
    "implementations/20261030-115752_05_scripts_agent_startup_validation.py.md": [
        "validate_against_registry",
        "ComponentMandatorinessError",
        "component_mandatoriness",
        "load_component_mandatoriness",
    ],
    "implementations/20261030-115752_08_tools_check_component_mandatoriness.py.md": [
        "component_id",
    ],
    "implementations/20261030-115752_09_tools_generate_reference_table.py.md": [
        "component_id",
        "load_component_mandatoriness",
        "build_manifest",
        "load_manifest",
        "component_mandatoriness",
    ],
    "implementations/20261030-115752_10_tests_shared_test_component_mandatoriness.py.md": [
        "load_component_mandatoriness",
        "get_classification",
        "check_required_agreement",
        "ComponentClassification",
        "UnknownComponentError",
        "ClassificationConflictError",
        "component_id",
    ],
    "implementations/20261030-115752_23_tests_agent_test_production_config_validator.py.md": [
        "ComponentClassification",
        "load_component_mandatoriness",
    ],
    "implementations/20261030-115752_24_tests_agent_test_startup_validation.py.md": [
        "_check_component_mandatoriness",
    ],
    "implementations/20261030-115752_27_docs_22_mcp_mcp_06_02_mcpserverconfig-fields-agenttoml-mcp_servers.md.md": [
        "component_mandatoriness",
    ],
}

MARKED_RE = re.compile(r"`([A-Za-z_][A-Za-z0-9_./-]*)`")


def mark(text: str, symbols: list[str]) -> str:
    targets = set(symbols)

    def repl(m: re.Match[str]) -> str:
        name = m.group(1)
        end = m.end()
        if name in targets and not text.startswith(" (new)", end):
            return m.group(0) + " (new)"
        return m.group(0)

    return MARKED_RE.sub(repl, text)


def main() -> int:
    rc = 0
    for path, symbols in EDITS.items():
        try:
            src = open(path, encoding="utf-8").read()
        except OSError as exc:
            print(f"missing file: {path}: {exc}")
            rc = 1
            continue
        out = mark(src, symbols)
        for sym in symbols:
            if f"`{sym}`" not in src:
                print(f"symbol not found in {path}: {sym}")
                rc = 1
        if out != src:
            open(path, "w", encoding="utf-8").write(out)
            print(f"updated {path}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
