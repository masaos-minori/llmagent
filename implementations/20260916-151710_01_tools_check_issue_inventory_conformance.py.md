## Goal

Implement `tools/check_issue_inventory_conformance.py`: (a) vocabulary checks — `Status`/`Type`/`Severity`/`Area`/`Owner` (Part 1) and `Status` (Part 2) against their defined value sets, case-sensitive; (b) template checks — exactly 16 fields per Part 1 full entry, 15 per Part 2 entry, with removal-placeholder paragraphs exempted; (c) orphaned-bullet detection — a `- **Field**:` bullet appearing after a removal-placeholder paragraph with no intervening `#### ` heading; (d) closing-summary consistency — the Part 1 closing sentence's named/ranged IDs must exactly match the set of IDs that currently have a real `#### ` heading; (e) referential integrity — every ID in a `Related`/`Related NC`/`Target` field resolves to an existing `#### ` heading (OK) or a removal-placeholder paragraph naming that ID (Warning), and Blocking if neither exists.

## Scope

- Create a new Python script at `tools/check_issue_inventory_conformance.py`.
- Implement five check functions: vocabulary, template field-count, orphaned bullets, closing-summary consistency, referential integrity.
- Reuse `tools/_docs_consistency_lib.py`'s shared `DocFile`, `Issue`, `discover_md_files`, `report_and_exit` helpers.
- Follow the pattern established by `tools/check_known_deviation_sync.py` and `tools/check_needs_confirmation_inventory.py`.

## Assumptions

- The vocabulary value sets are defined in `docs/00_governance_03_issue-and-uncertainty-management.md` Part 1:
  - Status: `open`, `investigating`, `deferred`
  - Type: `document-code-mismatch`, `operational-gap`, `implementation-bug`, `design-decision`
  - Severity: `high`, `medium`, `low`
  - Area: `agent`, `mcp-server`, `workflow-engine`, `shared`, `governance`, `rag`
  - Owner: role-based values like `@data-eng`, `@platform`, etc.
- Part 2 vocabulary: Status only — `open`, `investigating`, `deferred`
- Removal placeholders are prose paragraphs (no `- **Field**:` bullets) ending in the "do not create a `#### {ID}` heading" sentence.
- The Part 1 closing summary is a prose sentence listing all expected IDs after the last `#### ` heading.

## Design decisions

- Use argparse for CLI interface — consistent with other `tools/check_*.py` scripts.
- Return exit code 0 when no violations found, non-zero when violations exist.
- Classify referential-integrity findings as Blocking (neither heading nor placeholder exists) or Warning (placeholder exists but no heading).
- Do not hardcode the entry list — parse the document dynamically.

## Alternatives considered

- Adding a separate Rule ID in the Governance Verification Matrix — rejected because the Plan's intent is to update GV-008 in place to avoid duplicate-tracking-slot problems.

## Implementation
### Target file

`tools/check_issue_inventory_conformance.py`

### Procedure

1. Create the new script file under `tools/`.
2. Import from `tools/_docs_consistency_lib.py` — reuse `DocFile`, `Issue`, `discover_md_files`, `report_and_exit`.
3. Define vocabulary value sets as constants.
4. Implement five check functions:
   - `check_vocabulary()` — validate Status/Type/Severity/Area/Owner (Part 1) and Status (Part 2) against defined value sets.
   - `check_template_field_count()` — count `- **Field**:` bullets per entry; require 16 for Part 1 full entries, 15 for Part 2 entries; exempt removal placeholders.
   - `check_orphaned_bullets()` — detect `- **Field**:` bullets appearing after a removal-placeholder paragraph with no intervening `#### ` heading.
   - `check_closing_summary()` — verify the Part 1 closing sentence's ID list matches the set of IDs with real `#### ` headings.
   - `check_referential_integrity()` — resolve every ID in `Related`/`Related NC`/`Target` fields against headings and placeholder-prose IDs.
5. Add module docstring documenting the script's purpose and its relationship to `check_docs_quality.py::check_resolved_in_active`.

### Method

Current state: No existing script implements this checker. Two modeled analogues exist:
- `tools/check_known_deviation_sync.py` — same ID-resolves-to-a-heading problem, one document-hop removed
- `tools/check_needs_confirmation_inventory.py` — Part 2 parsing pattern

Required structure:
```python
#!/usr/bin/env python3
"""tools/check_issue_inventory_conformance.py

Conformance checker for docs/00_governance_03_issue-and-uncertainty-management.md.

Validates:
  (a) Vocabulary conformance — Status/Type/Severity/Area/Owner against defined value sets
  (b) Template field-count — 16 fields per Part 1 entry, 15 per Part 2 entry
  (c) Orphaned bullets — - **Field:** bullets after removal placeholders
  (d) Closing-summary consistency — Part 1 closing ID list vs. actual headings
  (e) Referential integrity — Related/Related NC/Target ID resolution

Removal placeholders (prose paragraphs ending in 'do not create a #### {ID} heading')
are exempt from field-count checks and classified as Warning (not Blocking) for
referential-integrity lookups.

Modeled on tools/check_known_deviation_sync.py and tools/check_needs_confirmation_inventory.py.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Reused from _docs_consistency_lib.py
from _docs_consistency_lib import DocFile, Issue, discover_md_files, report_and_exit

# ── Vocabulary value sets ────────────────────────────────────────────────────────

PART1_STATUS_VALUES = {"open", "investigating", "deferred"}
PART1_TYPE_VALUES = {"document-code-mismatch", "operational-gap", "implementation-bug", "design-decision"}
PART1_SEVERITY_VALUES = {"high", "medium", "low"}
PART1_AREA_VALUES = {"agent", "mcp-server", "workflow-engine", "shared", "governance", "rag"}
PART1_OWNER_PATTERN = re.compile(r"^@[a-z][a-z0-9_-]*$")

PART2_STATUS_VALUES = {"open", "investigating", "deferred"}

# ── Check functions ──────────────────────────────────────────────────────────────

def check_vocabulary(doc: DocFile) -> list[Issue]:
    """Validate Status/Type/Severity/Area/Owner against defined value sets."""
    ...

def check_template_field_count(doc: DocFile) -> list[Issue]:
    """Count - **Field:** bullets per entry; require 16 (Part 1) / 15 (Part 2); exempt placeholders."""
    ...

def check_orphaned_bullets(doc: DocFile) -> list[Issue]:
    """Detect - **Field:** bullets after a removal-placeholder with no intervening #### heading."""
    ...

def check_closing_summary(doc: DocFile) -> list[Issue]:
    """Verify Part 1 closing ID list matches actual #### headings."""
    ...

def check_referential_integrity(doc: DocFile) -> list[Issue]:
    """Resolve Related/Related NC/Target IDs against headings and placeholder-prose IDs."""
    ...

# ── Main ─────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("doc_path", nargs="?", default=None, help="Path to the governance document")
    args = parser.parse_args()

    doc_path = Path(args.doc_path) if args.doc_path else Path(__file__).parent.parent / "docs" / "00_governance_03_issue-and-uncertainty-management.md"
    
    # Parse the document
    doc = DocFile(doc_path)
    
    issues: list[Issue] = []
    issues.extend(check_vocabulary(doc))
    issues.extend(check_template_field_count(doc))
    issues.extend(check_orphaned_bullets(doc))
    issues.extend(check_closing_summary(doc))
    issues.extend(check_referential_integrity(doc))
    
    if issues:
        print(f"\nFound {len(issues)} conformance violation(s):\n", file=sys.stderr)
        for issue in issues:
            print(f"  [{issue.severity}] {issue.id}: {issue.message}", file=sys.stderr)
        report_and_exit(issues)
    else:
        print("All conformance checks passed.", file=sys.stdout)
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### Details

The script must be executable (`chmod +x`) and include the shebang line. All five check functions should return a list of `Issue` objects with severity classification (Blocking or Warning). The script should handle missing files gracefully and provide clear error messages.

## Compatibility considerations

- This is a new tool — no backward compatibility concerns.
- The script reuses existing library functions from `_docs_consistency_lib.py`, ensuring consistency with other conformance checkers.

## Security considerations

- No security impact — the script reads local Markdown files and reports findings; it does not modify any files.

## Rollback considerations

- If the script is found to produce false positives, the check logic can be adjusted without removing the entire tool.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tools/check_issue_inventory_conformance.py` | Unit (fixture-backed) | `uv run pytest tests/tools/test_check_issue_inventory_conformance.py -v` | All fixtures pass, each violation class correctly flagged, placeholders not falsely flagged |
| `tools/check_issue_inventory_conformance.py` | Manual smoke test | `uv run python tools/check_issue_inventory_conformance.py` (against the live, unfixed document) | Non-zero exit, reporting all currently-known violation instances |
| `tools/check_issue_inventory_conformance.py` | Lint/type/security | `uv run ruff format tools/check_issue_inventory_conformance.py && uv run ruff check tools/check_issue_inventory_conformance.py && uv run mypy tools/check_issue_inventory_conformance.py && uv run bandit tools/check_issue_inventory_conformance.py` | All pass |

## Completion criteria

- The script detects all five violation classes when run against the current, unfixed `docs/00_governance_03_issue-and-uncertainty-management.md`.
- The script detects the one confirmed dangling reference (`RAG-006` → `NC-026`, Blocking).
- Removal placeholders (e.g. `RAG-003`, `CI-001`) are not falsely flagged as malformed entries.
- `uv run ruff format tools/check_issue_inventory_conformance.py && uv run ruff check tools/check_issue_inventory_conformance.py && uv run mypy tools/check_issue_inventory_conformance.py && uv run bandit tools/check_issue_inventory_conformance.py` passes clean.
- Manual smoke test confirms non-zero exit against the live, unfixed document.

## Out of scope

- Fixing the vocabulary violations themselves — tracked by the single-status-vocabulary Plan (`plans/20260916-150416_plan.md`) and the RAG-entries-correction Plan (`plans/20260916-150753_plan.md`).
- Extending the check to other governance documents.
- Validating references to files outside the governance document.
- Fixing `tools/check_docs_quality.py`'s `check_resolved_in_active` — out of this issue's named target files.
- Entry ordering, NC-033 indentation, or identifier capitalization — structural/typographic cleanup, a separate issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260915-200449_gov03_add-conformance-and-referential-integrity-checks-for-the-issue-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-151710_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-151710
- **Related target files**: tools/check_issue_inventory_conformance.py
