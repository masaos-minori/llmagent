## Goal

Update docstring references from `docs/adr-index.md` to `docs/10_adr/adr-index.md` in `tools/check_adr_reference.py`.

## Scope

- Update docstring at line 4 referencing `docs/adr-index.md`
- Update error message at line 147 referencing `docs/adr-index.md`
- Update function description at line 186 referencing `docs/adr-index.md`

## Assumptions

- The path variable `ADR_INDEX` at line 44 is already correct (`DOCS_DIR / "10_adr" / "adr-index.md"`)
- The `file="adr-index.md"` strings at lines 129 and 160 are short identifiers used in Issue objects and do not need changing
- The error message at line 163 already contains the correct path `docs/10_adr/adr-index.md`

## Design decisions

- Only update prose/docstring/error-message references; leave the `ADR_INDEX` variable definition unchanged since it already resolves correctly
- Keep `file="adr-index.md"` in Issue objects as-is since these are display identifiers, not filesystem paths

## Alternatives considered

- Updating the `ADR_INDEX` variable name or structure: unnecessary since the current definition already resolves correctly
- Adding a constant for the display identifier: out of scope for this fix

## Implementation

### Target file

`tools/check_adr_reference.py`

### Procedure

Replace all prose/docstring/error-message references from `docs/adr-index.md` to `docs/10_adr/adr-index.md`.

### Method

Use Edit tool to replace each occurrence individually.

### Details

1. **Line 4**: Replace `docs/adr-index.md` with `docs/10_adr/adr-index.md` in the docstring opening paragraph.
2. **Line 147**: Replace `docs/adr-index.md` with `docs/10_adr/adr-index.md` in the error message string.
3. **Line 186**: Replace `docs/adr-index.md` with `docs/10_adr/adr-index.md` in the argparse description.

Do NOT modify:
- Line 44: `ADR_INDEX = DOCS_DIR / "10_adr" / "adr-index.md"` — already correct
- Lines 129, 160: `file="adr-index.md"` — display identifiers, not filesystem paths
- Line 163: `message="docs/10_adr/adr-index.md not found"` — already correct

## Compatibility considerations

No compatibility impact. This change only updates documentation text within the tool itself. The runtime behavior is unchanged since the `ADR_INDEX` variable was already pointing to the correct location.

## Security considerations

N/A: No security-relevant changes.

## Rollback considerations

Revert the three Edit operations to restore the original text. No data loss risk.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tools/check_adr_reference.py | Direct invocation | `uv run python -m tools.check_adr_reference` | Zero errors |
| tools/check_adr_reference.py | Grep verification | `rg -rn "docs/adr-index\.md" tools/check_adr_reference.py` | Zero matches outside of `ADR_INDEX` variable definition |

## Completion criteria

- All prose/docstring/error-message references to `docs/adr-index.md` in `tools/check_adr_reference.py` have been replaced with `docs/10_adr/adr-index.md`
- The `ADR_INDEX` variable definition remains unchanged (already correct)
- Running `uv run python -m tools.check_adr_reference` completes successfully

## Out of scope

- Updating references in other files (handled by separate procedure documents)
- Modifying the `ADR_INDEX` variable definition
- Changing the `file="adr-index.md"` identifiers in Issue objects
- Additional target file discovery: `tests/tools/test_check_adr_invariant_matrix.py` contains a reference to `docs/adr-index.md` in its docstring/comment but is not listed in the Plan's frozen Implementation Target Files table. Per the workflow discipline, it must not be modified here — it requires a separate row addition to the plan before any modification.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update docstring reference at line 4 | Pending | — | — | |
| 2 | Update error message at line 147 | Pending | — | — | |
| 3 | Update function description at line 186 | Pending | — | — | |
| 4 | Validate with direct invocation | Pending | — | — | |
| 5 | Grep verification | Pending | — | — | |

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
- **Requirement ID**: REQ-001 — Update hardcoded path references in governance tools
- **Source issue**: issues/20260925-133804_h002_pre-commit-hooks-expect-nonexistent-adr-path.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-212812_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260926-055243
- **Related target files**: tools/check_adr_reference.py
