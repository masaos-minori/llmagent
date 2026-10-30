## Goal

Make task status changes validated, conditional, and race-safe in `scripts/agent/workflow/task_ops.py` (`REQ-002`, conditional updates with typed errors), and provide the claim and resume contract the engine and adapter use (`REQ-007`, claim and resume rules).

## Scope

- Modify only `scripts/agent/workflow/task_ops.py`.
- No schema change: the transition API works on the existing `tasks.status` column; the database `CHECK` is the schema row.

## Assumptions

- Plan Dependencies (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Scope): this row is Plan Phase 1 and needs rows 01 (enums and matrix) and 02 (errors) first; it should follow `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` Phase 2, which makes `task_ops` the single task-SQL owner. If that Plan has not landed, this row still adds the transitions to `task_ops` and adds no new task SQL elsewhere.
- Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `task_ops.py` is also a target of `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` (count functions, lookup deletion, key rename): sequencing dependency, different functions, rebase in landing order.
- Owner decision (2026-10-30): resume contract is `pending` and `failed` claimable; `running`, `completed`, and `halted` rejected.
- `SQLiteHelper.begin_immediate()` serializes writers (`BEGIN IMMEDIATE`, default busy timeout 30000 ms) and `execute` returns the cursor whose `rowcount` is checked (`scripts/db/helper.py`).
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `TaskStatus` and the transition mapping (row 01 document), `TaskNotFoundError` and `TaskTransitionError` (row 02 document).

## Design decisions

- `update_task_status` keeps its name and signature (callers: `StateStore`, tests) but becomes a validated transition: read the current status, check the matrix, then update `WHERE task_id=? AND status=<current>` inside one `begin_immediate()` block and require exactly one row.
- A separate claim entry (`claim_task` (new)) encodes the resume contract once; the adapter's resume guard calls a pure check (`assert_resumable` (new)) built on the same constant, so the contract lives in this module only.
- The error for an invalid or unknown status is `TaskTransitionError` (typed), never a silent write.

## Alternatives considered

- A bare `UPDATE ... WHERE status IN (...)` without a read: rejected, the typed error would not name the current status that the halted-resume test matches on.
- Enforcing the matrix only in SQL: rejected, the message and error type would be lost; SQL `CHECK` covers the vocabulary only.

## Implementation

### Target file

`scripts/agent/workflow/task_ops.py`

### Procedure

1. Add `transition_task_in_txn` (new)(db, task_id, new_status, expected=None) that assumes the caller holds the write transaction, and `transition_task` (new)(db, task_id, new_status, expected=None) that wraps it in `begin_immediate()`. The in-transaction function reads the current status (`TaskNotFoundError` when absent), reject an unknown `new_status`, apply the matrix from `models.py`, honor `expected` when given, run the conditional `UPDATE`, require `rowcount == 1`, raise `TaskTransitionError` otherwise.
2. Re-implement `update_task_status` (`:66`) as `transition_task` (new) with no `expected`.
3. Add `claim_task` (new)(db, task_id) that moves `pending` or `failed` to `running` through `transition_task` (new) with the claimable set, and rejects `running`, `completed`, and `halted`.
4. Add `assert_resumable` (new)(task) for an already fetched `TaskRecord`, raising `TaskTransitionError` whose message names the status (for example `halted`).

### Method

- The claimable set is one module constant derived from `TaskStatus`; both `claim_task` (new) and `assert_resumable` (new) use it.
- The in-transaction variant exists so stale recovery (`state_store.py` row) can fail an attempt and its owning task in one transaction; nested `begin_immediate()` blocks are not allowed.
- Use parameterized SQL only; commit by leaving the `begin_immediate()` block (do not call `db.commit()` inside it).
- The `UPDATE` still sets `updated_at` with the shared `now_iso` helper already imported as `_now`.

### Details

- Callers write `pending -> halted` (adapter preparation failure) and `completed -> failed` (adapter overwrite) today; both are in the matrix, so no caller breaks.
- Two connections racing on `claim_task` (new) for one task: the second sees `running` and raises `TaskTransitionError`; this is what the concurrency test asserts.
- Cited symbols and lines in this file may shift after the wftaskapi001 Plan's row 01; locate by symbol name.

## Compatibility considerations

- Signature of `update_task_status` is unchanged; behavior is stricter (invalid transitions now raise). The existing adapter writes are in the matrix.
- `TaskTransitionError` subclasses `RuntimeError`, so the adapter's `RuntimeError` expectations hold.

## Security considerations

- N/A: no external input; SQL is parameterized.

## Rollback considerations

- N/A: revert the commit (no persisted-data change).

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_state_store.py tests/agent/workflow/test_workflow_concurrency.py tests/agent/test_orchestrator.py -v`
- `uv run ruff format scripts/agent/workflow/task_ops.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`

## Completion criteria

- An invalid status string, an invalid transition, and a zero-row update each raise a typed error.
- `claim_task` (new) accepts only `pending` and `failed`; two concurrent claims yield one winner.
- `assert_resumable` (new) rejects `halted` with a message containing `halted`.

## Out of Scope

- Attempt and ledger logic, engine and adapter wiring, DDL, tests, docs (other rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `transition_task` (new), `claim_task` (new), `assert_resumable` (new); re-implement `update_task_status` | Pending | — | — | Plan Phase 1; after rows 01 and 02 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Test rows' documents |
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
- **Requirement ID**: REQ-002 (conditional task transitions with typed errors), REQ-007 (claim and resume contract)
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/agent/workflow/task_ops.py
