## Goal
Make `tools/sync_plan_workitem_status.py` ignore `N/A` rows when deciding a procedure's outcome, so one `N/A` row no longer leaves the Plan's `Work Items Created` row stuck at `Pending`.

## Scope
**Release unit**: N/A: not part of a release unit
**Companion test file**: `tests/tools/test_sync_plan_workitem_status.py` (covered by this document; it has no procedure document of its own)

## Assumptions
- UNK-01 of the Plan is confirmed: `N/A` is a terminal, not-done status, so an `N/A` row neither blocks reconciliation nor counts as finished by itself.
- The status-module import path already exists in this tool (it imports parse_execution_status_rows from `tools/_workitem_status_table.py` today).

## Design decisions
- In procedure_outcome, drop rows whose trimmed Status is `N/A` before classifying the rest: all remaining rows `Completed` yields `Completed`; remaining rows within `Completed` plus `Superseded` (at least one `Superseded`) yield `Superseded`; any other remaining value, or no remaining rows at all (a procedure whose rows are all `N/A`), returns None and the Plan row stays `Pending`.
- A mixed `Completed` and `N/A` procedure therefore reconciles to `Completed` (AC-2), and an all-`N/A` procedure stays unreconciled: reconciliation reports what the procedure executed, and a procedure that marked every step not-applicable executed nothing.

## Alternatives considered
- Treating an all-`N/A` procedure as `Completed`: rejected by the Plan's AC-2 ("a procedure whose rows are all N/A stays unreconciled") — nothing was done, and the archived-status gate keeps such rows visible through their category.
- Removing `N/A` from accepted values entirely: rejected by Decision 1 (UNK-01), the accepted option in the Plan.

## Implementation
### Target file
`tools/sync_plan_workitem_status.py`

### Procedure
1. In procedure_outcome, after parsing rows, split the trimmed Status values into the `N/A` rows and the rest.
2. Classify the rest exactly as today (the `Completed`-only case and the `Completed`/`Superseded` case with one `Superseded`); return None when the rest is empty.
3. Update the function docstring: `N/A` rows are ignored, not finished.

### Method
A set-difference line before the existing two comparisons; no other function in the tool changes.

### Details
- The tool's `--dry-run` behavior, row selection (only `Pending` rows of the Plan table), and printing are untouched.
- The module docstring currently describes the reconcile rule; extend its sentence to name the ignored `N/A` rows.

### Companion test files
- `tests/tools/test_sync_plan_workitem_status.py`
  - Procedure: add the `N/A` outcome cases — `N/A` mixed with `Completed` reconciles to `Completed`; `N/A` mixed with `Completed` and `Superseded` reconciles to `Superseded`; a procedure whose rows are all `N/A` stays unreconciled (REQ-002 / AC-2); write them first (Plan Phase 1) — they fail until the function change lands.
  - Validation: `uv run pytest tests/tools/test_sync_plan_workitem_status.py -q` — all cases pass and the existing outcome tests still pass unchanged.

## Compatibility considerations
- Behavior change is additive: cases that reconciled before reconcile the same way; a previously-never-reconciled case (`Completed` plus `N/A`) now reconciles to `Completed` — the Plan's recorded risk with the stated mitigation (tests cover mixed and all-`N/A` procedures; archived procedures are not rewritten).

## Security considerations
No new I/O; the tool already rewrites only the Plan file through its existing write path.

## Rollback considerations
Revert the function and its companion test additions together; no other file depends on the change.

## Validation plan
- Companion tests in `tests/tools/test_sync_plan_workitem_status.py`: `N/A` mixed with `Completed` reconciles, `N/A` mixed with `Completed` and `Superseded` reconciles as `Superseded`, all-`N/A` stays unreconciled (REQ-002 / AC-2).
- `uv run pytest tests/tools/test_sync_plan_workitem_status.py -q` plus the Plan's importer regression row; lint, mypy, bandit, size gate.

## Completion criteria
- The three `N/A` outcome cases pass (AC-2).
- Existing tests of the tool still pass unchanged.

## Out of Scope
- Editing any archived procedure or Plan row by hand (the tool does the reconciliation).
- The batch-close terminal set (sibling procedure).

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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261117-132201_wftoolfu001_workitem-status-vocabulary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261117-133851_wftoolfu001_workitem-status-vocabulary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-050931
- **Related target files**: `tools/sync_plan_workitem_status.py`, `tests/tools/test_sync_plan_workitem_status.py`
