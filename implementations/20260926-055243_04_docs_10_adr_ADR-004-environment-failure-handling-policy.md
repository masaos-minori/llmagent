## Goal

Update references from `docs/adr-index.md` to `docs/10_adr/adr-index.md` in `docs/10_adr/ADR-004-environment-failure-handling-policy.md`.

## Scope

- Update reference at line 489 referencing `docs/adr-index.md`
- Update reference at line 490 referencing `docs/adr-index.md`

## Assumptions

- No other references to `docs/adr-index.md` exist in this file beyond lines 489-490
- The file structure and Japanese content should remain unchanged

## Design decisions

- Only update the two path references; leave all other content including Japanese descriptions intact
- Preserve the Known Deviations section formatting exactly as-is

## Alternatives considered

- Updating the entire Known Deviations section: unnecessary since only the path references need changing
- Adding a new section or subsection: out of scope for this fix

## Implementation

### Target file

`docs/10_adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

Replace all prose references from `docs/adr-index.md` to `docs/10_adr/adr-index.md`.

### Method

Use Edit tool to replace each occurrence individually.

### Details

1. **Line 489**: Replace `docs/adr-index.md` with `docs/10_adr/adr-index.md` in the Summary field of the Known Deviation entry.
2. **Line 490**: Replace `docs/adr-index.md` with `docs/10_adr/adr-index.md` in the Conflicting Source field of the Known Deviation entry.

## Compatibility considerations

No compatibility impact. This change only updates documentation text within an ADR document. The ADR's meaning and intent are preserved.

## Security considerations

N/A: No security-relevant changes.

## Rollback considerations

Revert the two Edit operations to restore the original text. No data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/10_adr/ADR-004-environment-failure-handling-policy.md | Grep verification | `rg -rn "docs/adr-index\.md" docs/10_adr/ADR-004-environment-failure-handling-policy.md` | Zero matches |

## Completion criteria

- All references to `docs/adr-index.md` in `docs/10_adr/ADR-004-environment-failure-handling-policy.md` have been replaced with `docs/10_adr/adr-index.md`
- Document structure and Japanese content remain intact

## Out of scope

- Updating references in other files (handled by separate procedure documents)
- Modifying any Known Deviation entries beyond the path references
- Changing the ADR's status or classification
- Additional target file discovery: `tests/tools/test_check_adr_reference.py` and `tests/tools/test_check_adr_invariant_matrix.py` contain references to `docs/adr-index.md` in their docstrings/comments but are not listed in the Plan's frozen Implementation Target Files table. Per the workflow discipline, they must not be modified here — they require a separate row addition to the plan before any modification.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update reference at line 489 | Pending | — | — | |
| 2 | Update reference at line 490 | Pending | — | — | |
| 3 | Grep verification | Pending | — | — | |

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
- **Requirement ID**: REQ-003 — No remaining references in the codebase point to the discarded path `docs/adr-index.md`
- **Source issue**: issues/20260925-133804_h002_pre-commit-hooks-expect-nonexistent-adr-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-212812_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260926-055243
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md
