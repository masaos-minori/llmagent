## Goal

Update references from `docs/adr-index.md` to `docs/10_adr/adr-index.md` in `tools/TOOL_DESCRIPTIONS.md`.

## Scope

- Update reference at line 66 referencing `docs/adr-index.md`
- Update reference at line 67 referencing `docs/adr-index.md`

## Assumptions

- No other references to `docs/adr-index.md` exist in this file beyond lines 66-67
- The file structure (table format) should remain unchanged

## Design decisions

- Only update the two path references; leave all other content including Japanese descriptions intact
- Preserve the table formatting exactly as-is

## Alternatives considered

- Updating the entire table row: unnecessary since only the path reference needs changing
- Adding a new column or section: out of scope for this fix

## Implementation

### Target file

`tools/TOOL_DESCRIPTIONS.md`

### Procedure

Replace all prose references from `docs/adr-index.md` to `docs/10_adr/adr-index.md`.

### Method

Use Edit tool to replace each occurrence individually.

### Details

1. **Line 66**: Replace `docs/adr-index.md` with `docs/10_adr/adr-index.md` in the `check_adr_invariant_matrix.py` tool description row.
2. **Line 67**: Replace `docs/adr-index.md` with `docs/10_adr/adr-index.md` in the `check_adr_reference.py` tool description row.

## Compatibility considerations

No compatibility impact. This change only updates documentation text within the tool descriptions file. The actual tool behavior is unchanged.

## Security considerations

N/A: No security-relevant changes.

## Rollback considerations

Revert the two Edit operations to restore the original text. No data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/TOOL_DESCRIPTIONS.md | Grep verification | `rg -rn "docs/adr-index\.md" tools/TOOL_DESCRIPTIONS.md` | Zero matches |

## Completion criteria

- All references to `docs/adr-index.md` in `tools/TOOL_DESCRIPTIONS.md` have been replaced with `docs/10_adr/adr-index.md`
- Table formatting remains intact

## Out of scope

- Updating references in other files (handled by separate procedure documents)
- Modifying any tool code or configuration
- Additional target file discovery: `tests/tools/test_check_adr_reference.py` and `tests/tools/test_check_adr_invariant_matrix.py` contain references to `docs/adr-index.md` in their docstrings/comments but are not listed in the Plan's frozen Implementation Target Files table. Per the workflow discipline, they must not be modified here — they require a separate row addition to the plan before any modification.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update reference at line 66 | Completed | 20260926-073347 | 20260926-073347 |  |
| 2 | Update reference at line 67 | Completed | 20260926-073347 | 20260926-073347 |  |
| 3 | Grep verification | Completed | 20260926-073347 | 20260926-073347 |  |

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
- **Related target files**: tools/TOOL_DESCRIPTIONS.md