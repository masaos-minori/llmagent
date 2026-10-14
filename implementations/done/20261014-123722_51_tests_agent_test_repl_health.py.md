## Goal

REPL health tests: Drop `require_approval` from the inline workflow definitions, remove the `approvals` DDL and the table-missing test (REQ-005: tests).

## Scope

- Drop `require_approval` from the inline workflow definitions, remove the `approvals` DDL and the table-missing test

## Assumptions

- Plan `plans/20261014-114443_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Apply only after the repository owner's decision (Plan Step 1) is recorded, together with every other procedure of this plan (Steps 2-11) as one commit unit.
- Line numbers come from the Plan and may shift; locate edits by symbol, test name, or section.

## Design decisions

- Edit by test name; compare `pytest --collect-only -q` counts before and after and confirm only the intended tests changed.
- New test text must not contain registered removed names (the allowlisted test files excepted); use unregistered terms such as require_approval, approvals, or pending_approval where needed.

## Alternatives considered

N/A: test-only change

## Implementation

### Target file

`tests/agent/test_repl_health.py`

### Procedure

Drop `require_approval` from the inline workflow definitions, remove the `approvals` DDL and the table-missing test.

### Method

Evidence recorded in the Plan: `test_repl_health.py` lines 908, 936, 951, 983, 984, 1041 (plus 1 more). Locate the places with a case-sensitive search for the removed names in this file, edit by symbol or section, then format the file.

### Details

- Drop the require_approval key from the inline workflow definitions (about lines 908, 936, 951), remove the approvals DDL in the workflow database helper (about lines 983-985) and the test that expects the missing approvals table to fail, or retarget it to another required table.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit; the whole plan lands as one commit unit.

## Validation plan

- `uv run pytest` on this file passes after the code procedures are applied.
- `uv run ruff format` and `uv run ruff check` on the file are clean.

## Completion criteria

- The file contains no removed gate name outside what the Procedure keeps.
- Remaining tests still pass and the collected-count change matches the Procedure.

## Out of scope

- Tool-level approval (the keep list), the MDQ and eventbus areas, and any file outside this Plan's target table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the edit | Completed | 20261014-142001 | 20261014-142001 |  |
| 2 | Run the affected tests | Completed | 20261014-142001 | 20261014-142001 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-142001 | 20261014-142001 |  |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261014-112913_appr001_remove-the-post-execution-approval-gate.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-114443_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-123722
- **Related target files**: tests/agent/test_repl_health.py