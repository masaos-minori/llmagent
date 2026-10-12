## Goal
- Describe the `# mock-patch-ok: <reason>` marker in the `check_mock_patch_targets.py` detail row (`REQ-003`).

## Scope
- Only the detail-table row for `check_mock_patch_targets.py` (the row whose second column is `tests/**/test_*.py`); the inventory row stays as is.

## Assumptions
- The documentation language of this file is Japanese, matching its existing rows.

## Design decisions
- One added sentence in the existing row: syntax, line-local effect, mandatory reason.

## Alternatives considered
N/A: the Plan Design section already fixed the approach for this row.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. Locate the row with `grep -n "check_mock_patch_targets.py" tools/TOOL_DESCRIPTIONS.md` (detail row near line 106).
2. Append a sentence stating that a `patch(...)` line ending with `# mock-patch-ok: <理由>` is excluded from the findings, that an empty reason does not suppress, and that the marker applies to that line only.

### Method
- Edit the row text in place; keep it a single table row.

### Details
- Do not add or remove files in `tools/`, so the file inventory is unchanged.

## Compatibility considerations
N/A: test-only change; no runtime or public interface is affected.

## Security considerations
N/A: no input handling, credentials, or I/O boundary is touched.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` reports `No issues found.`

## Completion criteria
- The row documents the marker and the sync checker passes.

## Out of scope
- Any other row or section of this file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the marker description to the `check_mock_patch_targets.py` detail row | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the touched files | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (inline suppression marker with a mandatory reason)
- **Source issue**: issues/20261012-120426_mock001_fix-ineffective-mock-patch-targets-in-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261012-120856_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261012-121424
- **Related target files**: tools/TOOL_DESCRIPTIONS.md
