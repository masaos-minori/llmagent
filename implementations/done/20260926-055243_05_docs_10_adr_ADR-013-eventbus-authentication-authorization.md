## Goal

Update reference from `docs/adr-index.md` to `docs/10_adr/adr-index.md` in `docs/10_adr/ADR-013-eventbus-authentication-authorization.md`.

## Scope

- Update reference at line 54 referencing `docs/adr-index.md`

## Assumptions

- No other references to `docs/adr-index.md` exist in this file beyond line 54
- The file structure and English content should remain unchanged

## Design decisions

- Only update the one path reference; leave all other content intact
- Preserve the Assumptions section formatting exactly as-is

## Alternatives considered

- Updating the entire Assumptions section: unnecessary since only the path reference needs changing
- Adding a new section or subsection: out of scope for this fix

## Implementation

### Target file

`docs/10_adr/ADR-013-eventbus-authentication-authorization.md`

### Procedure

Replace the prose reference from `docs/adr-index.md` to `docs/10_adr/adr-index.md`.

### Method

Use Edit tool to replace the occurrence.

### Details

1. **Line 54**: Replace `docs/adr-index.md` with `docs/10_adr/adr-index.md` in the Assumptions bullet about ADR numbering convention.

## Compatibility considerations

No compatibility impact. This change only updates documentation text within an ADR document. The ADR's meaning and intent are preserved.

## Security considerations

N/A: No security-relevant changes.

## Rollback considerations

Revert the Edit operation to restore the original text. No data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/10_adr/ADR-013-eventbus-authentication-authorization.md | Grep verification | `rg -rn "docs/adr-index\.md" docs/10_adr/ADR-013-eventbus-authentication-authorization.md` | Zero matches |

## Completion criteria

- All references to `docs/adr-index.md` in `docs/10_adr/ADR-013-eventbus-authentication-authorization.md` have been replaced with `docs/10_adr/adr-index.md`
- Document structure and content remain intact

## Out of scope

- Updating references in other files (handled by separate procedure documents)
- Modifying any ADR entries beyond the path reference
- Changing the ADR's status or classification
- Additional target file discovery: `tests/tools/test_check_adr_reference.py` and `tests/tools/test_check_adr_invariant_matrix.py` contain references to `docs/adr-index.md` in their docstrings/comments but are not listed in the Plan's frozen Implementation Target Files table. Per the workflow discipline, they must not be modified here — they require a separate row addition to the plan before any modification.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update reference at line 54 | Completed | 20260926-073723 | 20260926-073723 |  |
| 2 | Grep verification | Completed | 20260926-073723 | 20260926-073723 |  |

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
- **Related target files**: docs/10_adr/ADR-013-eventbus-authentication-authorization.md