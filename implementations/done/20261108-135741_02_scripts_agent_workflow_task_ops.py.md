## Goal
Make `update_task_status` usable inside another module's open transaction: add a no-commit, vocabulary-guarded variant so `recover_stale_attempts` can write `tasks.status` without breaking its begin-immediate transaction (REQ-001/REQ-003).

## Scope
**Release unit**: wfaudit007-full

- Covers Plan `plans/20261108-084004_wfaudit007_task-status-never-reconciled.md` row 2 only: `scripts/agent/workflow/task_ops.py`.

## Assumptions
- Callers outside recovery keep the current commit-per-call behavior; only the recovery path opts into the new mode.

## Design decisions
- Add a keyword-only parameter `commit` (new) (default `True`) to `update_task_status` (L68-82) instead of a second function: one vocabulary guard, one SQL statement, no divergent validation paths (wfaudit005 "every write validated by the ops helpers" invariant preserved).

## Alternatives considered
- A separate no-commit variant function: rejected — duplicates the `TASK_STATUSES` guard and invites two near-identical helpers to drift.
- Raw SQL in `state_store.py`: rejected — bypasses the ops-helper validation pattern the vocabulary enforcement established.

## Implementation
### Target file
`scripts/agent/workflow/task_ops.py`

### Procedure
Extend `update_task_status` with the keyword-only `commit` (new) parameter and skip the trailing `db.commit()` when it is `False`.

### Method
Signature becomes `update_task_status(db: SQLiteHelper, task_id: str, status: str, *, commit: bool = True) -> None`; validation and the UPDATE statement are unchanged; the `db.commit()` at L82 runs only when `commit` is true. Update the docstring to state that `commit=False` leaves the write to the caller's open transaction.

### Details
- The `ValueError` raised for out-of-vocabulary values is unchanged — the recovery caller relies on it for REQ-003.

## Compatibility considerations
- Keyword-only with default `True`: all existing callers (`state_store.py:81-83` wrapper, engine paths) behave identically.

## Security considerations
- N/A: no new inputs; vocabulary guard unchanged.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- Unit tests in `tests/agent/workflow/` (task_ops/status-vocabulary test modules): `commit=False` leaves the row uncommitted until the caller commits; out-of-vocabulary status still raises `ValueError`; default behavior unchanged.
- `uv run pytest tests/agent/workflow/ -q`; lint/type gates per `rules/toolchain.md`.

## Completion criteria
- Recovery can write `tasks.status` through the validated helper without committing; existing behavior is byte-for-byte unchanged for all current callers.

## Out of Scope
- The recovery-side caller (row 1 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the keyword-only `commit` parameter per Procedure/Method | Completed | 20261109-064151 | 20261109-064151 | keyword-only commit=True param added; docstring states commit=False semantics |
| 2 | Add or update tests per Validation plan | Completed | 20261109-064151 | 20261109-064151 | TestUpdateTaskStatusCommitFlag (3 tests) in test_workflow_status_vocabulary.py |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-064151 | 20261109-064151 | targeted suites green; gates exit 0 |

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
- **Requirement ID**: `REQ-001` (in-transaction write path), `REQ-003` (vocabulary-validated write)
- **Source issue**: `issues/20261107-203220_wfaudit007_task-status-never-reconciled.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261108-084004_wfaudit007_task-status-never-reconciled.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-135741
- **Related target files**: `scripts/agent/workflow/task_ops.py`