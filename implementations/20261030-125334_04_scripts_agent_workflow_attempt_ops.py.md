## Goal

Make `scripts/agent/workflow/attempt_ops.py` the owner of attempt rows with persisted numbering and a terminal-only conditional finish (`REQ-003`, persisted monotonic attempt numbers and one canonical start; `REQ-005`, terminal-only finish), and remove the bypass `start_attempt` (`REQ-012`, no bypass path).

## Scope

- Modify only `scripts/agent/workflow/attempt_ops.py`.
- The public attempt-start entry that the engine calls lives in `idempotency_ops.py` (next row); this module provides the row-level operations it composes.

## Assumptions

- Plan Dependencies (`plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Scope): Plan Phase 3. It requires the schema row (`attempts.attempt_number`, Phase 2, Plan row 10) to have landed first, and that row needs `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3. The schema row is `Blocked` for this document set (see the cycle report), so this document MUST NOT be executed before the schema row exists.
- Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `attempt_ops.py` is also a target of `plans/20261030-114516_wflease001_stale-attempt-lease.md` (owner and lease at attempt start): sequencing dependency, that Plan adds columns to this contract after this one lands.
- `begin_immediate()` holds the write transaction; functions that run inside it must not call `db.commit()`.
- Caller evidence: production does not call `start_attempt` (`rg start_attempt scripts` finds only definitions); tests in `tests/agent/workflow/` do.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `AttemptStatus` and `ATTEMPT_TERMINAL_STATUSES` (row 01 document), `AttemptTransitionError` (row 02 document).

## Design decisions

- Row-level helpers that run inside a caller's transaction (`insert_attempt` (new), `mark_attempt_finished` (new)) do not commit; `finish_attempt` keeps its name and opens its own `begin_immediate()` block around `mark_attempt_finished` (new).
- `attempt_number` is `COALESCE(MAX(attempt_number), 0) + 1` for the task-stage pair, computed in the same transaction as the insert; the unique index is the backstop.
- `finish_attempt` accepts only terminal statuses (`AttemptStatus` completed or failed) and updates `WHERE attempt_id=? AND status='running'`, requiring one row, else `AttemptTransitionError`.

## Alternatives considered

- Keep `start_attempt` as a thin wrapper: rejected, it would stay a second attempt-start path (`REQ-012`).
- Number attempts in the engine: rejected, that is the in-memory counter this Plan removes.

## Implementation

### Target file

`scripts/agent/workflow/attempt_ops.py`

### Procedure

1. Add `max_attempt_number` (new)(db, task_id, stage_id) returning the largest persisted number or 0.
2. Replace `start_attempt` (`:12`) with `insert_attempt` (new)(db, task_id, stage_id): inside the caller's transaction compute the next number, insert the `running` row with `attempt_number`, and return an `AttemptRecord` carrying it.
3. Add `mark_attempt_finished` (new) performing the conditional terminal update with the row-count check, and make `finish_attempt` (`:34`) call it inside its own `begin_immediate()` block; reject a non-terminal status before any SQL; correct the docstring (it says "Mark an attempt as completed").
4. Keep `count_attempts` (`:50`) unchanged.

### Method

- Terminal-status check uses `ATTEMPT_TERMINAL_STATUSES` from `models.py`; an unknown or non-terminal status raises `AttemptTransitionError` naming the status.
- `insert_attempt` (new) still sets `started_at` through the shared `now_iso` helper and generates `attempt_id` as before.

### Details

- `error_msg`, `error_kind`, and `error_detail` pass through unchanged.
- Tests that call `start_attempt` (`tests/agent/workflow/test_workflow_state_store.py`, `test_workflow_stage_persistence.py`) are rewritten against the canonical start in their own rows.

## Compatibility considerations

- Public function removed (`start_attempt`) and `finish_attempt` tightened; callers are the engine (via `StateStore.finish_attempt`) and tests.
- Persisted rows need the new `attempt_number` column; existing databases get it from the schema migration, not from this module.

## Security considerations

- N/A: parameterized SQL, no external input.

## Rollback considerations

- Revert the commit together with the schema row; the migration itself is forward-only (dbmig001), so a rolled-back database is restored from the pre-migration backup.

## Validation plan

- `uv run pytest tests/agent/workflow/ -v` (numbering across restarts, terminal-only finish, zero-row error)
- `rg start_attempt scripts tests` (no remaining caller)
- `uv run ruff format scripts/agent/workflow/attempt_ops.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria

- `start_attempt` is gone; `insert_attempt` (new) allocates a monotonic per task-stage number in the caller's transaction.
- `finish_attempt` rejects non-terminal statuses and a non-`running` row with `AttemptTransitionError`.

## Out of Scope

- The ledger and the public attempt-start entry (`idempotency_ops.py` row), `StateStore` delegates (its row), DDL.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `max_attempt_number` (new), `insert_attempt` (new), `mark_attempt_finished` (new); tighten `finish_attempt`; remove `start_attempt` | Pending | — | — | Plan Phase 3; gated on the schema row |
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
- **Requirement ID**: REQ-003 (persisted attempt numbering), REQ-005 (terminal-only finish), REQ-012 (no bypass start)
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: scripts/agent/workflow/attempt_ops.py
