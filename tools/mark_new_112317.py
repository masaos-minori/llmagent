#!/usr/bin/env python3
"""mark_new_112317.py — apply " (new)" markers to the 20261030-112317 procedure docs.

One-off batch fixer for tools/stale_detector.py symbol_missing findings on the
adrcov001 batch: constructs created by this plan (manifest enum names, envelope
key `generated_at`, new test function names) carry the " (new)" marker directly
after the closing backtick; pytest summary tokens (SKIPPED/XFAIL/XPASS) are
prose vocabulary and are unbackticked instead.

Already applied once; kept for reproducibility. Idempotent: lines that already
carry the marker are skipped.
"""

from __future__ import annotations

from pathlib import Path

BASE = Path(__file__).resolve().parent.parent / "implementations"

EDITS: list[tuple[str, str, str]] = [
    (
        "20261030-112317_02_tools_check_adr_invariant_matrix.py.md",
        "module constant `_CADENCE_RULE_SEVERITY` (default",
        "module constant `_CADENCE_RULE_SEVERITY` (new) (default",
    ),
    (
        "20261030-112317_03_.github_run_cited_adr_tests.py.md",
        "distinguish `skipped` and `xfail` from `passed` by parsing pytest output.",
        "distinguish SKIPPED and XFAIL from passed by parsing pytest output.",
    ),
    (
        "20261030-112317_03_.github_run_cited_adr_tests.py.md",
        "summary lines (`SKIPPED`/`XFAIL`/`XPASS`) attributes outcomes without",
        "summary lines (SKIPPED / XFAIL / XPASS) attributes outcomes without",
    ),
    (
        "20261030-112317_05_tools_generate_reference_table.py.md",
        "`generated_at` recorded but",
        "`generated_at` (new) recorded but",
    ),
    (
        "20261030-112317_06_schemas_contract_manifest.json.md",
        "`manifest`, `version`, `generated_by`,",
        "`manifest` (new), `version` (new), `generated_by` (new),",
    ),
    (
        "20261030-112317_06_schemas_contract_manifest.json.md",
        "`manifest` const branch or `oneOf`).",
        "`manifest` const branch or `oneOf` (new)).",
    ),
    (
        "20261030-112317_06_schemas_contract_manifest.json.md",
        "`mcp_endpoints`, `eventbus_route_roles`,",
        "`mcp_endpoints` (new), `eventbus_route_roles` (new),",
    ),
    (
        "20261030-112317_06_schemas_contract_manifest.json.md",
        "`generated_by`\n   (const",
        "`generated_by` (new)\n   (const",
    ),
    (
        "20261030-112317_06_schemas_contract_manifest.json.md",
        "via `allOf`/`if-then` branches",
        "via `allOf` (new)/`if-then` branches",
    ),
    (
        "20261030-112317_07_registry_manifests_tool_ownership.yaml.md",
        "with `manifest: tool_ownership`.",
        "with `manifest: tool_ownership` (new).",
    ),
    (
        "20261030-112317_08_registry_manifests_mcp_endpoints.yaml.md",
        "Ship the `mcp_endpoints` contract manifest",
        "Ship the `mcp_endpoints` (new) contract manifest",
    ),
    (
        "20261030-112317_09_registry_manifests_eventbus_route_roles.yaml.md",
        "- `manifest: eventbus_route_roles`;",
        "- `manifest: eventbus_route_roles` (new);",
    ),
    (
        "20261030-112317_10_registry_manifests_db_schema_versions.yaml.md",
        "- `manifest: db_schema_versions`;",
        "- `manifest: db_schema_versions` (new);",
    ),
    (
        "20261030-112317_10_registry_manifests_db_schema_versions.yaml.md",
        "drops `generated_at` from comparisons",
        "drops `generated_at` (new) from comparisons",
    ),
    (
        "20261030-112317_11_registry_manifests_config_ownership.yaml.md",
        "- `manifest: config_ownership`;",
        "- `manifest: config_ownership` (new);",
    ),
    (
        "20261030-112317_12_registry_manifests_health_contracts.yaml.md",
        "- `manifest: health_contracts`;",
        "- `manifest: health_contracts` (new);",
    ),
    (
        "20261030-112317_13_registry_manifests_invariant_coverage.yaml.md",
        "- `manifest: invariant_coverage`;",
        "- `manifest: invariant_coverage` (new);",
    ),
    (
        "20261030-112317_16_tests_tools_test_check_adr_invariant_matrix.py.md",
        "→ `_CADENCE_RULE_SEVERITY` severity (doc 02);",
        "→ `_CADENCE_RULE_SEVERITY` (new) severity (doc 02);",
    ),
    (
        "20261030-112317_16_tests_tools_test_check_adr_invariant_matrix.py.md",
        "Add `test_skipped_citation_reports_error`, `test_xfail_citation_reports_error`,",
        "Add `test_skipped_citation_reports_error` (new), `test_xfail_citation_reports_error` (new),",
    ),
    (
        "20261030-112317_16_tests_tools_test_check_adr_invariant_matrix.py.md",
        "Add `test_missing_cadence_warning`, `test_cadence_present_ok` (new)",
        "Add `test_missing_cadence_warning` (new), `test_cadence_present_ok` (new)",
    ),
    (
        "20261030-112317_17_tests_tools_test_run_cited_adr_tests.py.md",
        "the new `_classify_outcome` and\n  `_cited_exceptions` (doc 03)",
        "the new `_classify_outcome` (new) and\n  `_cited_exceptions` (new) (doc 03)",
    ),
    (
        "20261030-112317_18_tests_tools_test_generate_reference_table.py.md",
        "ignoring\n  `generated_at`)",
        "ignoring\n  `generated_at` (new))",
    ),
    (
        "20261030-112317_18_tests_tools_test_generate_reference_table.py.md",
        "strips the `generated_at` key",
        "strips the `generated_at` (new) key",
    ),
    (
        "20261030-112317_18_tests_tools_test_generate_reference_table.py.md",
        "`test_manifest_stale_vs_source`,",
        "`test_manifest_stale_vs_source` (new),",
    ),
]


def main() -> int:
    failures = 0
    for name, old, new in EDITS:
        path = BASE / name
        text = path.read_text(encoding="utf-8")
        if new in text:
            print(f"already applied: {name}")
            continue
        if old not in text:
            print(f"NOT FOUND in {name}: {old!r}")
            failures += 1
            continue
        path.write_text(text.replace(old, new, 1), encoding="utf-8")
        print(f"ok {name}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
