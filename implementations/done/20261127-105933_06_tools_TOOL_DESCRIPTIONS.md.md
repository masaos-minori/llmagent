## Goal
- Document the two new options in `tools/TOOL_DESCRIPTIONS.md` (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- Verified in Step 3a: an Index row and a Work Items row exist for `check_plan_target_overlaps.py` and for `run_validation_gates.py`, and an Index row exists for `_validation_gate_report.py`; `tools/check_tool_descriptions_sync.py` checks only that tool names are documented. Run after seq 01 to 05.

## Design decisions
- Append sentences to the existing cells; do not restructure rows.

## Alternatives considered
- N/A: documentation rows only.

## Implementation
### Target file
`tools/TOOL_DESCRIPTIONS.md`

### Procedure
1. `check_plan_target_overlaps.py` Work Items row: append "`--plan PATH` (repeatable) keeps only findings whose Plan list contains that Plan (exact path match, repository-relative or absolute); an argument that is not a file exits 2; default output and exit 0 are unchanged."
2. `run_validation_gates.py` Work Items row: append "`--failures-only` prints the changed-file count (no file list), every non-`Pass` row (rows hidden by default for a runtime argument stay behind the count line unless `--verbose`), and a final `Result: Pass` or `Result: Fail (N failing gate(s))` line; the exit code equals the full output's (1 only when a gate is `Fail`); it omits the changed-file list, so use the default output to compare it with the staged set."
3. `_validation_gate_report.py` Index row: append "also the failures-only branch".

### Method
- Keep each row on one line and match neighboring wording.

### Details
- Keep the option names exact: `--plan`, `--failures-only`.

## Compatibility considerations
- N/A: documentation only.

## Security considerations
- N/A: no behavior change.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/check_tool_descriptions_sync.py` exits 0.

## Completion criteria
- Both options are described in the rows named above and the sync check passes.

## Out of Scope
- Other tools' rows and any skill text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the three rows | Completed | 20261127-111303 | 20261127-111313 | Changed: tools/TOOL_DESCRIPTIONS.md (three rows) |
| 2 | Run `uv run python tools/check_tool_descriptions_sync.py` | Completed | 20261127-111313 | 20261127-111313 | check_tool_descriptions_sync.py: No issues found |

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
- **Requirement ID**: `REQ-005` (documentation of both options)
- **Source issue**: issues/20261126-151443_wfeff008_gate-output-filters.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261127-104530_wfeff008_gate-output-filters.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261127-105933
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`