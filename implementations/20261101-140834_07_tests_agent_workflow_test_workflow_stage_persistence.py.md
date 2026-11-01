## Goal

Update the raw task INSERT fixture in `tests/agent/workflow/test_workflow_stage_persistence.py` to the renamed column (Plan REQ-003 rename reaches every test that references the key).

## Scope

- The fixture `INSERT INTO tasks (task_id, workflow_id, workflow_version, status, idempotency_key)` at `:29` becomes `... task_nonce)`.

## Assumptions

- Re-verified 2026-11-01: the INSERT is at `:29` exactly as the Plan cites.

## Design decisions

- Rename-only edit; the inserted value stays an opaque unique string.

## Alternatives considered

- N/A: single fixture line.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_stage_persistence.py`

### Procedure
1. Rename the column at `:29` to `task_nonce` (new).

### Method
One-line edit; if the fixture value is derived from session/turn text (the historical composite-key style), keep the value opaque and unique.

### Details
- No other task-key reference exists in this file (verified by `rg` during Step 3a).

## Compatibility considerations

- Must land with rows 01-04 (the renamed column must exist before this fixture runs).

## Security considerations

- N/A: test-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py -v` (AC-3).

## Completion criteria

- The fixture inserts into `task_nonce` (new) and the file's tests pass against the renamed schema (AC-3).

## Out of Scope

- Stage persistence behavior itself — unchanged by this Plan.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (rename-aware test)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: tests/agent/workflow/test_workflow_stage_persistence.py
